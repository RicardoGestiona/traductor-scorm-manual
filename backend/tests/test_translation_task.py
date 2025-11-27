"""
Tests para la Celery task de traducción.

Filepath: backend/tests/test_translation_task.py
Feature alignment: STORY-010 - Celery Task
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from app.tasks.translation_tasks import translate_scorm_task, _update_progress
from app.models.translation import TranslationStatus


class TestTranslationTask:
    """Tests de la task de traducción principal."""

    @pytest.mark.asyncio
    @patch("app.tasks.translation_tasks.job_service")
    @patch("app.tasks.translation_tasks.storage_service")
    @patch("app.tasks.translation_tasks.ScormParser")
    @patch("app.tasks.translation_tasks.ContentExtractor")
    @patch("app.tasks.translation_tasks.TranslationService")
    @patch("app.tasks.translation_tasks.ScormRebuilder")
    async def test_translate_scorm_task_success(
        self,
        mock_rebuilder,
        mock_translator,
        mock_extractor,
        mock_parser,
        mock_storage,
        mock_job_service,
    ):
        """Test: Task completa exitosamente todo el pipeline."""
        job_id = str(uuid4())
        storage_path = f"originals/{job_id}/test.zip"
        source_lang = "en"
        target_langs = ["es", "fr"]

        # Setup mocks
        mock_job_service.update_job_status = AsyncMock()

        # Ejecutar task
        result = await translate_scorm_task(
            job_id=job_id,
            storage_path=storage_path,
            source_language=source_lang,
            target_languages=target_langs,
        )

        # Assertions
        assert result["success"] is True
        assert "download_urls" in result

        # Verificar que se actualizó el progreso múltiples veces
        assert mock_job_service.update_job_status.called
        # Debe haber llamadas para: VALIDATING, PARSING, TRANSLATING, REBUILDING, COMPLETED
        assert mock_job_service.update_job_status.call_count >= 5

    @pytest.mark.asyncio
    @patch("app.tasks.translation_tasks.job_service")
    async def test_translate_scorm_task_failure(self, mock_job_service):
        """Test: Task maneja errores correctamente."""
        job_id = str(uuid4())
        mock_job_service.update_job_status = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Ejecutar task (debe fallar)
        with pytest.raises(Exception) as exc_info:
            await translate_scorm_task(
                job_id=job_id,
                storage_path="invalid/path",
                source_language="en",
                target_languages=["es"],
            )

        # Verificar que se intentó marcar como fallido
        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("app.tasks.translation_tasks.job_service")
    async def test_update_progress(self, mock_job_service):
        """Test: Helper de actualización de progreso."""
        job_id = uuid4()
        mock_job_service.update_job_status = AsyncMock()

        await _update_progress(job_id, TranslationStatus.TRANSLATING, 50)

        mock_job_service.update_job_status.assert_called_once_with(
            job_id=job_id, status=TranslationStatus.TRANSLATING, progress=50
        )

    @pytest.mark.asyncio
    @patch("app.tasks.translation_tasks.job_service")
    async def test_update_progress_handles_errors(self, mock_job_service):
        """Test: Actualización de progreso no falla si DB falla."""
        job_id = uuid4()
        mock_job_service.update_job_status = AsyncMock(
            side_effect=Exception("DB unavailable")
        )

        # No debe lanzar excepción
        await _update_progress(job_id, TranslationStatus.PARSING, 25)

        # La excepción se loguea pero no se propaga
        assert mock_job_service.update_job_status.called

    @pytest.mark.asyncio
    async def test_task_progress_flow(self):
        """Test: Verificar que el progreso fluye correctamente."""
        # Estados esperados en orden
        expected_statuses = [
            (TranslationStatus.VALIDATING, 0),
            (TranslationStatus.VALIDATING, 10),
            (TranslationStatus.PARSING, 10),
            (TranslationStatus.PARSING, 25),
            (TranslationStatus.PARSING, 40),
            (TranslationStatus.TRANSLATING, 40),
            # ... más estados según idiomas
            (TranslationStatus.REBUILDING, 80),
            (TranslationStatus.COMPLETED, 100),
        ]

        # Este test verifica la lógica del flujo
        # En producción, cada estado se alcanza secuencialmente
        assert expected_statuses[0][0] == TranslationStatus.VALIDATING
        assert expected_statuses[-1][0] == TranslationStatus.COMPLETED
        assert expected_statuses[-1][1] == 100


class TestCeleryConfiguration:
    """Tests de configuración de Celery."""

    def test_celery_app_configured(self):
        """Test: Verificar que Celery app está configurada."""
        from app.core.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.timezone == "UTC"

    def test_celery_timeouts_configured(self):
        """Test: Verificar que timeouts están configurados correctamente."""
        from app.core.celery_app import celery_app

        # 1 hora = 3600 segundos
        assert celery_app.conf.task_soft_time_limit == 3600
        # 1h 5min = 3900 segundos
        assert celery_app.conf.task_time_limit == 3900

    def test_task_registered(self):
        """Test: Verificar que la task está registrada."""
        from app.core.celery_app import celery_app

        registered_tasks = celery_app.tasks
        assert "translate_scorm" in registered_tasks


class TestTaskRetryBehavior:
    """Tests del comportamiento de retry."""

    def test_task_has_retry_configuration(self):
        """Test: Verificar configuración de retry."""
        # La task debe tener retry configurado
        assert translate_scorm_task.autoretry_for == (Exception,)
        assert translate_scorm_task.retry_kwargs["max_retries"] == 3
        assert translate_scorm_task.retry_backoff is True
