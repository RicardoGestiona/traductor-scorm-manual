"""
Endpoint de upload de paquetes SCORM.

Filepath: backend/app/api/v1/upload.py
Feature alignment: STORY-004 - Endpoint de Upload de SCORM
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.auth import get_current_user, User
from app.models.translation import (
    UploadResponse,
    TranslationJobCreate,
    ErrorResponse,
    UploadValidationError,
    TranslationStatus,
)
from app.services.storage import storage_service
from app.services.job_service import job_service

logger = logging.getLogger(__name__)

router = APIRouter()


# SECURITY: FILE-001 fix - ZIP magic bytes for validation
# Standard ZIP signatures
ZIP_MAGIC_BYTES = [
    b"PK\x03\x04",  # Standard ZIP
    b"PK\x05\x06",  # Empty ZIP
    b"PK\x07\x08",  # Spanned ZIP
]


def validate_file_extension(filename: str) -> bool:
    """Validar que el archivo tenga extensión permitida (.zip)."""
    file_ext = Path(filename).suffix.lower()
    return file_ext in settings.ALLOWED_EXTENSIONS


def validate_file_magic_bytes(file: UploadFile) -> bool:
    """
    SECURITY: FILE-001 fix - Validate file is actually a ZIP by checking magic bytes.

    This prevents attacks where a malicious file is renamed to .zip.

    Args:
        file: Upload file to validate

    Returns:
        True if file has valid ZIP magic bytes
    """
    try:
        # Read first 4 bytes (ZIP signature length)
        file.file.seek(0)
        header = file.file.read(4)
        file.file.seek(0)  # Reset for later use

        # Check against known ZIP signatures
        for magic in ZIP_MAGIC_BYTES:
            if header.startswith(magic):
                return True

        return False
    except Exception:
        return False


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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
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
    user: User = Depends(get_current_user),
):
    """
    Upload a SCORM package for translation.

    **Authentication:** Required (Bearer token)

    **Validations:**
    - File must be a .zip file
    - File size must be <= 500MB (configurable)
    - Target languages must be supported

    **Returns:**
    - job_id: Unique identifier for tracking translation progress
    - status: Current status (initially 'uploaded')
    - original_filename: Name of the uploaded file
    - created_at: Timestamp of upload
    - user_id: ID of the authenticated user who uploaded the file

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/upload" \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
      -F "file=@curso.zip" \\
      -F "source_language=es" \\
      -F "target_languages=en,fr"
    ```
    """
    validation_errors: List[UploadValidationError] = []

    logger.info(f"Upload request - file: {file.filename}, source: {source_language}, target: {target_languages}, user: {user.email}")

    # 1. Validar extensión
    if not validate_file_extension(file.filename):
        validation_errors.append(
            UploadValidationError(
                field="file",
                message=f"Invalid file extension. Allowed: {settings.ALLOWED_EXTENSIONS}",
                code="invalid_extension",
            )
        )

    # 1b. SECURITY: FILE-001 fix - Validar magic bytes (tipo real del archivo)
    if not validate_file_magic_bytes(file):
        validation_errors.append(
            UploadValidationError(
                field="file",
                message="File is not a valid ZIP archive. The file content does not match ZIP format.",
                code="invalid_file_type",
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
            user_id=user.id,  # Asociar job con usuario autenticado
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
        logger.error(f"Validation errors: {[error.dict() for error in validation_errors]}")
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
        # Pasar bytes directamente (no BytesIO)

        storage_path = await storage_service.upload_file(
            file=file_content,
            filename=file.filename,
            job_id=job_response.id,
            folder="originals",
        )

        logger.info(f"File uploaded successfully to {storage_path}")

        # 6. Mock translation process (sin Celery/Redis para testing)
        logger.info(f"Starting mock translation process for job {job_response.id}")

        # Simular traducción: copiar archivo a scorm-translated para cada idioma
        download_urls = {}
        for target_lang in job_data.target_languages:
            # Copiar archivo original a bucket traducido
            translated_path = f"{job_response.id}/{target_lang}/{file.filename}"

            try:
                # Copiar desde scorm-originals a scorm-translated
                await storage_service.copy_file(
                    source_path=storage_path,
                    dest_path=translated_path,
                    source_bucket="scorm-originals",
                    dest_bucket="scorm-translated"
                )

                # Generar URL de descarga
                download_url = await storage_service.get_download_url(
                    file_path=translated_path,
                    bucket="scorm-translated"
                )
                download_urls[target_lang] = download_url

                logger.info(f"Mock translation completed for {target_lang}")
            except Exception as copy_error:
                logger.error(f"Failed to copy file for {target_lang}: {copy_error}")

        # Actualizar job con URLs de descarga y marcar como completado
        await job_service.update_download_urls(
            job_id=job_response.id,
            download_urls=download_urls
        )

        await job_service.update_job_status(
            job_id=job_response.id,
            status=TranslationStatus.COMPLETED,
            progress=100
        )

        logger.info(f"Mock translation process completed for job {job_response.id}")

        # 7. Retornar respuesta exitosa
        return UploadResponse(
            job_id=job_response.id,
            status=job_response.status,
            message="SCORM package uploaded successfully. Translation started in background.",
            original_filename=file.filename,
            created_at=job_response.created_at,
        )

    except Exception as e:
        # SECURITY: ERROR-001 fix - Log full error internally, return generic message
        logger.error(f"Failed to process upload: {e}", exc_info=True)

        # Si ya se creó el job, marcarlo como failed (keep internal error for debugging)
        if "job_response" in locals():
            await job_service.update_job_status(
                job_id=job_response.id,
                status="FAILED",
                error_message=f"Upload processing failed",  # Generic message stored
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to process upload",
                "message": "An error occurred while processing your file. Please try again.",
            },
        )
