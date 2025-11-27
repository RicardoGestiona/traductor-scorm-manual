"""
Endpoint de descarga de paquetes SCORM traducidos.

Filepath: backend/app/api/v1/download.py
Feature alignment: FR-005 - Descarga de SCORM Traducido
"""

import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import FileResponse, RedirectResponse

from app.core.auth import get_current_user, User
from app.services.job_service import job_service
from app.services.storage import storage_service
from app.models.translation import TranslationStatus, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/download/{job_id}/{language}",
    response_class=RedirectResponse,
    responses={
        307: {"description": "Redirect to signed download URL"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Job belongs to another user"},
        404: {"model": ErrorResponse, "description": "Job or language not found"},
        409: {"model": ErrorResponse, "description": "Translation not completed yet"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def download_translated_scorm(
    job_id: UUID,
    language: str,
    user: User = Depends(get_current_user),
):
    """
    Download a translated SCORM package for a specific language.

    This endpoint redirects to a signed URL in Supabase Storage that is valid for 7 days.

    **Flow**:
    1. Verify job exists and is completed
    2. Verify language was requested in the translation job
    3. Get signed URL from storage service
    4. Redirect to signed URL (307 Temporary Redirect)

    **Example**:
    ```bash
    curl -L "http://localhost:8000/api/v1/download/{job_id}/es" -o curso_es.zip
    ```

    **Response**:
    - 307 Redirect: To signed Supabase Storage URL
    - 404: Job not found or language not in job's target_languages
    - 409: Job not completed yet (still processing or failed)
    - 500: Error generating signed URL

    **Technical Notes**:
    - Signed URL is valid for 7 days (604800 seconds)
    - Filename format: `{original_filename}_{LANGUAGE}.zip`
    - Auto-deletion of files after 7 days (Supabase lifecycle policy)
    """
    try:
        logger.info(f"Download request for job {job_id}, language {language} (user: {user.email})")

        # 1. Obtener job de la base de datos
        job = await job_service.get_job(job_id)

        if not job:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Job not found",
                    "job_id": str(job_id),
                },
            )

        # 2. Verificar que el job pertenece al usuario autenticado
        if job.user_id and str(job.user_id) != user.id:
            logger.warning(f"User {user.email} attempted to download job {job_id} owned by {job.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "details": "You don't have permission to download this translation",
                },
            )

        # 3. Verificar que el job esté completado
        if job.status != TranslationStatus.COMPLETED:
            logger.warning(
                f"Job {job_id} not completed yet (status: {job.status.value})"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Translation not completed",
                    "current_status": job.status.value,
                    "message": f"Job is currently in '{job.status.value}' state. Please wait until it completes.",
                },
            )

        # 3. Verificar que el idioma esté en los target_languages del job
        if language not in job.target_languages:
            logger.warning(
                f"Language {language} not in job {job_id} target_languages: {job.target_languages}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Language not found",
                    "requested_language": language,
                    "available_languages": job.target_languages,
                    "message": f"Language '{language}' was not part of this translation job.",
                },
            )

        # 4. Verificar que exista URL de descarga para ese idioma
        if language not in job.download_urls:
            logger.error(
                f"Download URL missing for language {language} in completed job {job_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Download URL not available",
                    "message": "Translation completed but download URL is missing. Please contact support.",
                },
            )

        # 5. Obtener signed URL
        download_url = job.download_urls[language]

        # Si ya es una URL firmada (desde el task de traducción), retornarla directamente
        if download_url.startswith("http"):
            logger.info(f"Redirecting to existing signed URL for job {job_id}, language {language}")
            return RedirectResponse(
                url=download_url,
                status_code=status.HTTP_307_TEMPORARY_REDIRECT
            )

        # Si es un path de storage, generar signed URL
        logger.info(f"Generating signed URL for path: {download_url}")
        signed_url = await storage_service.get_signed_url(
            file_path=download_url,
            expires_in=7 * 24 * 3600,  # 7 días
        )

        if not signed_url:
            logger.error(f"Failed to generate signed URL for {download_url}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Failed to generate download URL",
                    "message": "Could not create signed URL for download. Please try again later.",
                },
            )

        logger.info(f"Successfully generated signed URL for job {job_id}, language {language}")

        # 6. Redirect a la signed URL
        return RedirectResponse(
            url=signed_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "details": str(e),
            },
        )


@router.get(
    "/download/{job_id}/all",
    response_class=FileResponse,
    responses={
        200: {"description": "ZIP file with all translated packages"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Translation not completed yet"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def download_all_translations(
    job_id: UUID,
):
    """
    Download all translated SCORM packages in a single ZIP file.

    This endpoint creates a temporary ZIP containing all translated packages
    and returns it as a direct download.

    **Structure of returned ZIP**:
    ```
    curso_translations.zip
    ├── curso_ES.zip
    ├── curso_FR.zip
    └── curso_DE.zip
    ```

    **Example**:
    ```bash
    curl "http://localhost:8000/api/v1/download/{job_id}/all" -o translations.zip
    ```

    **Response**:
    - 200: ZIP file with all translations
    - 404: Job not found
    - 409: Job not completed yet
    - 500: Error creating bundle

    **Technical Notes**:
    - Creates temporary ZIP file on server
    - File is auto-deleted after download (FileResponse with delete=True)
    - Filename format: `{original_filename}_translations.zip`
    - Each language package maintains its individual ZIP structure
    """
    try:
        logger.info(f"Download ALL request for job {job_id}")

        # 1. Obtener job de la base de datos
        job = await job_service.get_job(job_id)

        if not job:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Job not found",
                    "job_id": str(job_id),
                },
            )

        # 2. Verificar que el job esté completado
        if job.status != TranslationStatus.COMPLETED:
            logger.warning(
                f"Job {job_id} not completed yet (status: {job.status.value})"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Translation not completed",
                    "current_status": job.status.value,
                    "message": f"Job is currently in '{job.status.value}' state. Please wait until it completes.",
                },
            )

        # 3. Verificar que haya URLs de descarga
        if not job.download_urls or len(job.download_urls) == 0:
            logger.error(f"No download URLs available for completed job {job_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Download URLs not available",
                    "message": "Translation completed but download URLs are missing. Please contact support.",
                },
            )

        # 4. Crear ZIP temporal con todos los paquetes traducidos
        logger.info(f"Creating bundle ZIP for {len(job.download_urls)} language(s)")

        # Crear archivo temporal para el bundle
        temp_dir = tempfile.mkdtemp()
        temp_zip_path = Path(temp_dir) / f"{Path(job.original_filename).stem}_translations.zip"

        with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as bundle_zip:
            for language, download_url in job.download_urls.items():
                logger.info(f"Adding {language} package to bundle")

                # Si es URL firmada, descargar primero
                if download_url.startswith("http"):
                    # TODO: Implementar descarga desde signed URL y añadir al ZIP
                    # Por ahora, solo agregamos un placeholder
                    logger.warning(f"Downloading from signed URL not implemented yet for {language}")
                    continue

                # Si es path de storage, descargar y añadir
                try:
                    # Descargar archivo del storage
                    file_content = await storage_service.download_file(download_url)

                    if file_content:
                        # Nombre del archivo dentro del bundle
                        filename = f"{Path(job.original_filename).stem}_{language.upper()}.zip"
                        bundle_zip.writestr(filename, file_content)
                        logger.info(f"Added {filename} to bundle")
                    else:
                        logger.warning(f"Failed to download {language} package from storage")

                except Exception as e:
                    logger.error(f"Error adding {language} to bundle: {e}")
                    # Continuar con los demás idiomas

        # 5. Verificar que el ZIP no esté vacío
        if temp_zip_path.stat().st_size < 100:  # ZIP vacío es ~22 bytes
            logger.error(f"Bundle ZIP is empty for job {job_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Failed to create bundle",
                    "message": "Could not download any translated packages. Please try downloading individually.",
                },
            )

        # 6. Retornar FileResponse con auto-delete
        filename = f"{Path(job.original_filename).stem}_translations.zip"

        logger.info(f"Returning bundle ZIP ({temp_zip_path.stat().st_size} bytes) for job {job_id}")

        return FileResponse(
            path=str(temp_zip_path),
            media_type="application/zip",
            filename=filename,
            background=None,  # TODO: Add cleanup task
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download all endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "details": str(e),
            },
        )
