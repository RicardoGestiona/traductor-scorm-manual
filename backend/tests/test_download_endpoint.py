"""
Tests para el endpoint de descarga de paquetes SCORM traducidos.

Filepath: backend/tests/test_download_endpoint.py
Feature alignment: FR-005 - Descarga de SCORM Traducido
"""

import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import status
from app.models.translation import TranslationStatus, TranslationJobResponse

# Use valid UUIDs for user_id
OTHER_USER_UUID = "550e8400-e29b-41d4-a716-446655440001"


def now():
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestDownloadEndpoint:
    """Tests del endpoint de descarga individual."""

    @patch("app.api.v1.download.job_service")
    @patch("app.api.v1.download.storage_service")
    def test_download_redirect_to_signed_url(
        self, mock_storage, mock_job_service, test_client, mock_user
    ):
        """Test: Descarga redirige a signed URL correctamente."""
        job_id = uuid4()
        language = "es"

        # Mock job completado con URL de descarga
        mock_job = TranslationJobResponse(
            id=job_id,
            user_id=mock_user.id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es", "fr"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={
                "es": "translated/job123/curso_es.zip",
                "fr": "translated/job123/curso_fr.zip",
            },
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        # Mock signed URL
        mock_storage.get_signed_url = AsyncMock(
            return_value="https://storage.example.com/signed-url"
        )

        # Hacer request
        response = test_client.get(f"/api/v1/download/{job_id}/{language}", follow_redirects=False)

        # Assertions
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "https://storage.example.com/signed-url" in response.headers["location"]

        # Verificar que se llamó al storage service con 7 días de expiración
        mock_storage.get_signed_url.assert_called_once_with(
            file_path="translated/job123/curso_es.zip",
            expires_in=7 * 24 * 3600,
        )

    @patch("app.api.v1.download.job_service")
    def test_download_job_not_found(self, mock_job_service, test_client):
        """Test: 404 si el job no existe."""
        job_id = uuid4()
        mock_job_service.get_job = AsyncMock(return_value=None)

        response = test_client.get(f"/api/v1/download/{job_id}/es")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["error"] == "Job not found"

    @patch("app.api.v1.download.job_service")
    def test_download_job_not_completed(self, mock_job_service, test_client, mock_user):
        """Test: 409 si el job aún no está completado."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            user_id=mock_user.id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es"],
            status=TranslationStatus.TRANSLATING,
            progress_percentage=45,
            created_at=now(),
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        response = test_client.get(f"/api/v1/download/{job_id}/es")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"]["error"] == "Translation not completed"
        assert response.json()["detail"]["current_status"] == "translating"

    @patch("app.api.v1.download.job_service")
    def test_download_language_not_in_job(self, mock_job_service, test_client, mock_user):
        """Test: 404 si el idioma no estaba en target_languages."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            user_id=mock_user.id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es", "fr"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={"es": "url1", "fr": "url2"},
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        # Pedir idioma que no está en el job
        response = test_client.get(f"/api/v1/download/{job_id}/de")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["error"] == "Language not found"
        assert response.json()["detail"]["requested_language"] == "de"
        assert "es" in response.json()["detail"]["available_languages"]

    @patch("app.api.v1.download.job_service")
    def test_download_url_missing_for_language(
        self, mock_job_service, test_client, mock_user
    ):
        """Test: 500 si falta la URL de descarga para un idioma."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            user_id=mock_user.id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es", "fr"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={"fr": "url2"},  # Falta "es"
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        response = test_client.get(f"/api/v1/download/{job_id}/es")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"]["error"] == "Download URL not available"

    @patch("app.api.v1.download.job_service")
    def test_download_with_http_url_direct_redirect(
        self, mock_job_service, test_client, mock_user
    ):
        """Test: Si la URL ya es HTTP, redirigir directamente sin llamar a storage."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            user_id=mock_user.id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={"es": "https://storage.example.com/direct-url"},
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        response = test_client.get(f"/api/v1/download/{job_id}/es", follow_redirects=False)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "https://storage.example.com/direct-url" in response.headers["location"]

    @patch("app.api.v1.download.job_service")
    @patch("app.api.v1.download.storage_service")
    def test_download_storage_service_fails(
        self, mock_storage, mock_job_service, test_client, mock_user
    ):
        """Test: 500 si storage service falla al generar signed URL."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            user_id=mock_user.id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={"es": "translated/job123/curso_es.zip"},
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)
        mock_storage.get_signed_url = AsyncMock(return_value=None)  # Falla

        response = test_client.get(f"/api/v1/download/{job_id}/es")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"]["error"] == "Failed to generate download URL"

    @patch("app.api.v1.download.job_service")
    def test_download_forbidden_wrong_user(
        self, mock_job_service, test_client, mock_user
    ):
        """Test: 403 si el job pertenece a otro usuario."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            user_id=OTHER_USER_UUID,  # Different user
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={"es": "url"},
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        response = test_client.get(f"/api/v1/download/{job_id}/es")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"]["error"] == "Forbidden"


class TestDownloadAllEndpoint:
    """Tests del endpoint de descarga de todos los idiomas."""

    @patch("app.api.v1.download.job_service")
    @patch("app.api.v1.download.storage_service")
    def test_download_all_creates_bundle_zip(
        self, mock_storage, mock_job_service, test_client
    ):
        """Test: Descarga de todos crea un bundle ZIP."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es", "fr"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={
                "es": "translated/job123/curso_es.zip",
                "fr": "translated/job123/curso_fr.zip",
            },
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        # Mock download de archivos individuales
        mock_storage.download_file = AsyncMock(
            return_value=b"fake-zip-content-12345"  # Contenido fake
        )

        response = test_client.get(f"/api/v1/download/{job_id}/all")

        # Verificar que se intenta descargar ambos idiomas
        assert mock_storage.download_file.call_count == 2

        # Verificar respuesta
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/zip"
        assert "curso_translations.zip" in response.headers["content-disposition"]

    @patch("app.api.v1.download.job_service")
    def test_download_all_job_not_found(self, mock_job_service, test_client):
        """Test: 404 si el job no existe."""
        job_id = uuid4()
        mock_job_service.get_job = AsyncMock(return_value=None)

        response = test_client.get(f"/api/v1/download/{job_id}/all")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["error"] == "Job not found"

    @patch("app.api.v1.download.job_service")
    def test_download_all_job_not_completed(
        self, mock_job_service, test_client
    ):
        """Test: 409 si el job aún está en progreso."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es"],
            status=TranslationStatus.PARSING,
            progress_percentage=25,
            created_at=now(),
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        response = test_client.get(f"/api/v1/download/{job_id}/all")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"]["current_status"] == "parsing"

    @patch("app.api.v1.download.job_service")
    def test_download_all_no_download_urls(self, mock_job_service, test_client):
        """Test: 500 si no hay URLs de descarga."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={},  # Vacío
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        response = test_client.get(f"/api/v1/download/{job_id}/all")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"]["error"] == "Download URLs not available"

    @patch("app.api.v1.download.job_service")
    @patch("app.api.v1.download.storage_service")
    def test_download_all_storage_download_fails(
        self, mock_storage, mock_job_service, test_client
    ):
        """Test: 500 si storage service no puede descargar ningún archivo."""
        job_id = uuid4()

        mock_job = TranslationJobResponse(
            id=job_id,
            original_filename="curso.zip",
            source_language="en",
            target_languages=["es", "fr"],
            status=TranslationStatus.COMPLETED,
            progress_percentage=100,
            created_at=now(),
            download_urls={
                "es": "translated/job123/curso_es.zip",
                "fr": "translated/job123/curso_fr.zip",
            },
        )
        mock_job_service.get_job = AsyncMock(return_value=mock_job)

        # Storage falla en todas las descargas
        mock_storage.download_file = AsyncMock(return_value=None)

        response = test_client.get(f"/api/v1/download/{job_id}/all")

        # Debería fallar porque el ZIP quedó vacío
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"]["error"] == "Failed to create bundle"
