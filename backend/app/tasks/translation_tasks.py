"""
Celery tasks para procesamiento de traducciones SCORM.

Filepath: backend/app/tasks/translation_tasks.py
Feature alignment: STORY-010 - Celery Task para Traducción Asíncrona
"""

import logging
import tempfile
import zipfile
from pathlib import Path
from uuid import UUID
from io import BytesIO

from celery import Task
from app.core.celery_app import celery_app
from app.models.translation import TranslationStatus
from app.services.job_service import job_service
from app.services.storage import storage_service
from app.services.scorm_parser import ScormParser
from app.services.content_extractor import ContentExtractor
from app.services.translation_service import TranslationService
from app.services.scorm_rebuilder import ScormRebuilder

logger = logging.getLogger(__name__)


class TranslationTask(Task):
    """
    Base task class con auto-retry y error handling.
    """

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutos máximo
    retry_jitter = True


@celery_app.task(base=TranslationTask, bind=True, name="translate_scorm")
async def translate_scorm_task(
    self,
    job_id: str,
    storage_path: str,
    source_language: str,
    target_languages: list[str],
):
    """
    Task principal de traducción de paquetes SCORM.

    Orquesta el pipeline completo:
    1. Download del ZIP desde storage
    2. Validación y parsing SCORM
    3. Extracción de contenido traducible
    4. Traducción con Claude API
    5. Reconstrucción del SCORM traducido
    6. Upload de paquetes traducidos
    7. Generación de signed URLs

    Args:
        job_id: UUID del job
        storage_path: Path en Supabase Storage
        source_language: Código de idioma origen
        target_languages: Lista de códigos de idiomas destino

    Returns:
        Dict con URLs de descarga por idioma
    """
    job_uuid = UUID(job_id)

    try:
        logger.info(f"[Job {job_id}] Starting translation task")

        # ============================================================
        # PASO 1: VALIDATING - Descargar y validar SCORM (0% → 10%)
        # ============================================================
        await _update_progress(job_uuid, TranslationStatus.VALIDATING, 0)

        logger.info(f"[Job {job_id}] Downloading SCORM package from storage")
        # TODO: Implementar download desde Supabase Storage
        # Por ahora, asumimos que tenemos acceso al archivo

        await _update_progress(job_uuid, TranslationStatus.VALIDATING, 10)

        # ============================================================
        # PASO 2: PARSING - Parsear estructura SCORM (10% → 25%)
        # ============================================================
        await _update_progress(job_uuid, TranslationStatus.PARSING, 10)

        logger.info(f"[Job {job_id}] Parsing SCORM package")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # TODO: Extraer ZIP descargado
            # Por ahora simulamos que ya está extraído

            parser = ScormParser()
            # scorm_package = parser.parse_scorm_package(temp_path)

            # Detectar versión SCORM
            # scorm_version = scorm_package.version
            scorm_version = "1.2"  # Temporal

            # Actualizar job con versión detectada
            # await job_service.update_scorm_version(job_uuid, scorm_version)

            await _update_progress(job_uuid, TranslationStatus.PARSING, 25)

            # ============================================================
            # PASO 3: PARSING - Extraer contenido traducible (25% → 40%)
            # ============================================================
            logger.info(f"[Job {job_id}] Extracting translatable content")

            extractor = ContentExtractor()
            # extraction_result = extractor.extract_from_manifest(...)
            # extraction_result += extractor.extract_from_html_files(...)

            await _update_progress(job_uuid, TranslationStatus.PARSING, 40)

            # ============================================================
            # PASO 4: TRANSLATING - Traducir contenido (40% → 80%)
            # ============================================================
            await _update_progress(job_uuid, TranslationStatus.TRANSLATING, 40)

            logger.info(
                f"[Job {job_id}] Translating to {len(target_languages)} language(s)"
            )

            translator = TranslationService()
            translations_by_language = {}

            # Traducir para cada idioma destino
            progress_per_language = 40 / len(target_languages)
            current_progress = 40

            for i, target_lang in enumerate(target_languages):
                logger.info(f"[Job {job_id}] Translating to {target_lang}")

                # translated_segments = await translator.translate_segments(
                #     segments=extraction_result.get_all_segments(),
                #     source_language=source_language,
                #     target_language=target_lang,
                #     context=f"SCORM {scorm_version} course"
                # )

                # translations_by_language[target_lang] = translated_segments

                # Actualizar progreso por idioma
                current_progress += progress_per_language
                await _update_progress(
                    job_uuid, TranslationStatus.TRANSLATING, int(current_progress)
                )

            await _update_progress(job_uuid, TranslationStatus.TRANSLATING, 80)

            # ============================================================
            # PASO 5: REBUILDING - Reconstruir SCORM traducido (80% → 95%)
            # ============================================================
            await _update_progress(job_uuid, TranslationStatus.REBUILDING, 80)

            logger.info(f"[Job {job_id}] Rebuilding translated SCORM packages")

            rebuilder = ScormRebuilder()
            download_urls = {}

            progress_per_rebuild = 15 / len(target_languages)
            current_progress = 80

            for target_lang in target_languages:
                logger.info(f"[Job {job_id}] Rebuilding SCORM for {target_lang}")

                # translated_zip_path = rebuilder.rebuild_scorm(
                #     original_package=scorm_package,
                #     extraction_result=extraction_result,
                #     translations=translations_by_language[target_lang],
                #     output_dir=temp_path / "output",
                #     target_language=target_lang
                # )

                # Upload a Supabase Storage
                # storage_path_translated = await storage_service.upload_file(
                #     file=open(translated_zip_path, "rb"),
                #     filename=f"scorm_{target_lang}.zip",
                #     job_id=job_uuid,
                #     folder="translated"
                # )

                # Generar signed URL
                # signed_url = await storage_service.get_signed_url(
                #     storage_path_translated,
                #     expires_in=7 * 24 * 3600  # 7 días
                # )

                # download_urls[target_lang] = signed_url

                current_progress += progress_per_rebuild
                await _update_progress(
                    job_uuid, TranslationStatus.REBUILDING, int(current_progress)
                )

            await _update_progress(job_uuid, TranslationStatus.REBUILDING, 95)

            # ============================================================
            # PASO 6: COMPLETED - Finalizar (95% → 100%)
            # ============================================================
            logger.info(f"[Job {job_id}] Translation completed successfully")

            # Actualizar job con URLs de descarga
            # await job_service.update_download_urls(job_uuid, download_urls)

            await _update_progress(job_uuid, TranslationStatus.COMPLETED, 100)

            logger.info(
                f"[Job {job_id}] Task completed. URLs: {list(download_urls.keys())}"
            )

            return {"success": True, "download_urls": download_urls}

    except Exception as e:
        logger.error(f"[Job {job_id}] Translation failed: {str(e)}", exc_info=True)

        # Marcar job como fallido
        await job_service.update_job_status(
            job_id=job_uuid,
            status=TranslationStatus.FAILED,
            error_message=str(e),
        )

        # Re-raise para que Celery lo maneje (retry si aplica)
        raise


async def _update_progress(
    job_id: UUID, status: TranslationStatus, progress: int
) -> None:
    """
    Helper para actualizar progreso del job en la DB.

    Args:
        job_id: UUID del job
        status: Nuevo estado
        progress: Progreso en porcentaje (0-100)
    """
    try:
        await job_service.update_job_status(
            job_id=job_id, status=status, progress=progress
        )
        logger.debug(f"[Job {job_id}] Progress updated: {status.value} ({progress}%)")
    except Exception as e:
        logger.error(f"[Job {job_id}] Failed to update progress: {e}")
        # No re-lanzar excepción, el job puede continuar
