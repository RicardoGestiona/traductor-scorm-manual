"""
Endpoint de upload de paquetes SCORM.

Filepath: backend/app/api/v1/upload.py
Feature alignment: STORY-004 - Endpoint de Upload de SCORM
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.translation import (
    UploadResponse,
    TranslationJobCreate,
    ErrorResponse,
    UploadValidationError,
)
from app.services.storage import storage_service
from app.services.job_service import job_service

logger = logging.getLogger(__name__)

router = APIRouter()


def validate_file_extension(filename: str) -> bool:
    """Validar que el archivo tenga extensión permitida (.zip)."""
    file_ext = Path(filename).suffix.lower()
    return file_ext in settings.ALLOWED_EXTENSIONS


def validate_file_size(file: UploadFile) -> tuple[bool, float]:
    """
    Validar tamaño del archivo.

    Returns:
        (is_valid, size_in_mb)
    """
    # Leer tamaño del archivo
    file.file.seek(0, 2)  # Ir al final
    size_bytes = file.file.tell()
    file.file.seek(0)  # Volver al inicio

    size_mb = size_bytes / (1024 * 1024)
    is_valid = size_mb <= settings.MAX_UPLOAD_SIZE_MB

    return is_valid, size_mb


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def upload_scorm(
    file: UploadFile = File(..., description="SCORM package (.zip file)"),
    source_language: str = Form(
        "auto", description="Source language code (auto-detect if 'auto')"
    ),
    target_languages: str = Form(
        ..., description="Comma-separated target language codes (e.g., 'es,fr,de')"
    ),
):
    """
    Upload a SCORM package for translation.

    **Validations:**
    - File must be a .zip file
    - File size must be <= 500MB (configurable)
    - Target languages must be supported

    **Returns:**
    - job_id: Unique identifier for tracking translation progress
    - status: Current status (initially 'uploaded')
    - original_filename: Name of the uploaded file
    - created_at: Timestamp of upload

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/upload" \\
      -F "file=@curso.zip" \\
      -F "source_language=es" \\
      -F "target_languages=en,fr"
    ```
    """
    validation_errors: List[UploadValidationError] = []

    # 1. Validar extensión
    if not validate_file_extension(file.filename):
        validation_errors.append(
            UploadValidationError(
                field="file",
                message=f"Invalid file extension. Allowed: {settings.ALLOWED_EXTENSIONS}",
                code="invalid_extension",
            )
        )

    # 2. Validar tamaño
    is_valid_size, size_mb = validate_file_size(file)
    if not is_valid_size:
        validation_errors.append(
            UploadValidationError(
                field="file",
                message=f"File too large ({size_mb:.2f}MB). Max allowed: {settings.MAX_UPLOAD_SIZE_MB}MB",
                code="file_too_large",
            )
        )

    # 3. Parsear y validar idiomas destino
    target_langs_list = [lang.strip() for lang in target_languages.split(",")]

    try:
        job_data = TranslationJobCreate(
            original_filename=file.filename,
            source_language=source_language,
            target_languages=target_langs_list,
        )
    except ValueError as e:
        validation_errors.append(
            UploadValidationError(
                field="target_languages",
                message=str(e),
                code="invalid_language",
            )
        )

    # Si hay errores de validación, retornar 400
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "validation_errors": [error.dict() for error in validation_errors],
            },
        )

    try:
        # 4. Crear job en database primero (para obtener job_id)
        logger.info(
            f"Creating translation job for file: {file.filename} ({size_mb:.2f}MB)"
        )

        # Crear job temporal con storage_path vacío (lo actualizamos después del upload)
        job_response = await job_service.create_job(
            job_data=job_data, storage_path=""
        )

        # 5. Subir archivo a Supabase Storage
        logger.info(f"Uploading file to Supabase Storage for job {job_response.id}")

        # Leer contenido del archivo
        file_content = await file.read()
        file_bytes = BytesIO(file_content)

        storage_path = await storage_service.upload_file(
            file=file_bytes,
            filename=file.filename,
            job_id=job_response.id,
            folder="originals",
        )

        logger.info(f"File uploaded successfully to {storage_path}")

        # 6. Disparar Celery task para procesamiento asíncrono
        from app.tasks.translation_tasks import translate_scorm_task

        logger.info(f"Dispatching translation task for job {job_response.id}")

        translate_scorm_task.delay(
            job_id=str(job_response.id),
            storage_path=storage_path,
            source_language=job_data.source_language,
            target_languages=job_data.target_languages,
        )

        logger.info(f"Translation task dispatched successfully for job {job_response.id}")

        # 7. Retornar respuesta exitosa
        return UploadResponse(
            job_id=job_response.id,
            status=job_response.status,
            message="SCORM package uploaded successfully. Translation started in background.",
            original_filename=file.filename,
            created_at=job_response.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to process upload: {e}")

        # Si ya se creó el job, marcarlo como failed
        if "job_response" in locals():
            await job_service.update_job_status(
                job_id=job_response.id,
                status="FAILED",
                error_message=f"Upload failed: {str(e)}",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to process upload",
                "details": str(e),
            },
        )
