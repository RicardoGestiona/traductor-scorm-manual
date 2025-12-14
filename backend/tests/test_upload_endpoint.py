"""
Tests para el endpoint de upload de SCORM.

Filepath: backend/tests/test_upload_endpoint.py
Feature alignment: STORY-004 - Endpoint de Upload
"""

import pytest
from io import BytesIO
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.models.translation import TranslationStatus, TranslationJobResponse


@pytest.fixture
def mock_valid_zip_file():
    """Archivo ZIP válido de prueba."""
    content = b"PK\x03\x04" + b"\x00" * 100  # Simulación de ZIP header
    return ("test_scorm.zip", BytesIO(content), "application/zip")


@pytest.fixture
def mock_job_response(mock_user):
    """Respuesta mock de job creado."""
    return TranslationJobResponse(
        id=uuid4(),
        user_id=mock_user.id,
        original_filename="test_scorm.zip",
        source_language="auto",
        target_languages=["es", "fr"],
        status=TranslationStatus.UPLOADED,
        progress_percentage=0,
        created_at=datetime.utcnow(),
    )


class TestUploadEndpoint:
    """Tests del endpoint POST /api/v1/upload."""

    @patch("app.api.v1.upload.storage_service")
    @patch("app.api.v1.upload.job_service")
    def test_upload_success(
        self, mock_job_svc, mock_storage_svc, client, mock_valid_zip_file, mock_user
    ):
        """Test: Upload exitoso de archivo válido."""
        # Setup mocks
        mock_job = TranslationJobResponse(
            id=uuid4(),
            user_id=mock_user.id,
            original_filename="test_scorm.zip",
            source_language="auto",
            target_languages=["es", "fr"],
            status=TranslationStatus.UPLOADED,
            progress_percentage=0,
            created_at=datetime.utcnow(),
        )
        mock_job_svc.create_job = AsyncMock(return_value=mock_job)
        mock_job_svc.update_download_urls = AsyncMock()
        mock_job_svc.update_job_status = AsyncMock()
        mock_storage_svc.upload_file = AsyncMock(return_value=f"originals/{mock_job.id}/test_scorm.zip")
        mock_storage_svc.copy_file = AsyncMock()
        mock_storage_svc.get_download_url = AsyncMock(return_value="https://storage.example.com/url")

        # Request
        filename, file_content, content_type = mock_valid_zip_file
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, file_content, content_type)},
            data={"source_language": "auto", "target_languages": "es,fr"},
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "uploaded"
        assert data["original_filename"] == "test_scorm.zip"
        assert "created_at" in data

    def test_upload_invalid_extension(self, client):
        """Test: Rechazo de archivo con extensión inválida."""
        # Archivo .txt en lugar de .zip
        file_content = BytesIO(b"not a zip file")
        response = client.post(
            "/api/v1/upload",
            files={"file": ("document.txt", file_content, "text/plain")},
            data={"source_language": "es", "target_languages": "en"},
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "validation_errors" in data["detail"]
        errors = data["detail"]["validation_errors"]
        assert any(
            error["code"] == "invalid_extension" for error in errors
        ), "Expected invalid_extension error"

    def test_upload_file_too_large(self, client):
        """Test: Rechazo de archivo demasiado grande."""
        # Crear un archivo > 500MB (simulado con seek)
        large_file = BytesIO()
        large_file.write(b"PK\x03\x04")  # ZIP header
        # Simular tamaño grande sin escribir realmente los bytes
        large_file.seek(600 * 1024 * 1024)  # 600MB
        large_file.write(b"\x00")
        large_file.seek(0)

        response = client.post(
            "/api/v1/upload",
            files={"file": ("huge_scorm.zip", large_file, "application/zip")},
            data={"source_language": "es", "target_languages": "en"},
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "validation_errors" in data["detail"]
        errors = data["detail"]["validation_errors"]
        assert any(error["code"] == "file_too_large" for error in errors)

    def test_upload_invalid_target_language(self, client, mock_valid_zip_file):
        """Test: Rechazo de idioma destino no soportado."""
        filename, file_content, content_type = mock_valid_zip_file
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, file_content, content_type)},
            data={"source_language": "es", "target_languages": "xx,yy"},  # Inválidos
        )

        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "validation_errors" in data["detail"]
        errors = data["detail"]["validation_errors"]
        assert any(error["field"] == "target_languages" for error in errors)

    @patch("app.api.v1.upload.storage_service")
    @patch("app.api.v1.upload.job_service")
    def test_upload_multiple_target_languages(
        self, mock_job_svc, mock_storage_svc, client, mock_valid_zip_file, mock_user
    ):
        """Test: Upload con múltiples idiomas destino."""
        mock_job = TranslationJobResponse(
            id=uuid4(),
            user_id=mock_user.id,
            original_filename="test_scorm.zip",
            source_language="es",
            target_languages=["en", "fr", "de"],
            status=TranslationStatus.UPLOADED,
            progress_percentage=0,
            created_at=datetime.utcnow(),
        )
        mock_job_svc.create_job = AsyncMock(return_value=mock_job)
        mock_job_svc.update_download_urls = AsyncMock()
        mock_job_svc.update_job_status = AsyncMock()
        mock_storage_svc.upload_file = AsyncMock(return_value=f"originals/{mock_job.id}/test_scorm.zip")
        mock_storage_svc.copy_file = AsyncMock()
        mock_storage_svc.get_download_url = AsyncMock(return_value="https://storage.example.com/url")

        filename, file_content, content_type = mock_valid_zip_file
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, file_content, content_type)},
            data={
                "source_language": "es",
                "target_languages": "en,fr,de",  # 3 idiomas
            },
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "uploaded"

    def test_upload_missing_file(self, client):
        """Test: Petición sin archivo."""
        response = client.post(
            "/api/v1/upload",
            data={"source_language": "es", "target_languages": "en"},
        )

        # Assertions
        assert response.status_code == 422  # Unprocessable Entity

    def test_upload_missing_target_languages(self, client, mock_valid_zip_file):
        """Test: Petición sin idiomas destino."""
        filename, file_content, content_type = mock_valid_zip_file
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, file_content, content_type)},
            data={"source_language": "es"},  # Falta target_languages
        )

        # Assertions
        assert response.status_code == 422

    @patch("app.api.v1.upload.storage_service")
    @patch("app.api.v1.upload.job_service")
    def test_upload_storage_failure(
        self, mock_job_svc, mock_storage_svc, client, mock_valid_zip_file, mock_user
    ):
        """Test: Manejo de error al subir a storage."""
        # Setup: job se crea pero storage falla
        mock_job = TranslationJobResponse(
            id=uuid4(),
            user_id=mock_user.id,
            original_filename="test_scorm.zip",
            source_language="auto",
            target_languages=["es"],
            status=TranslationStatus.UPLOADED,
            progress_percentage=0,
            created_at=datetime.utcnow(),
        )
        mock_job_svc.create_job = AsyncMock(return_value=mock_job)
        mock_job_svc.update_job_status = AsyncMock()
        mock_storage_svc.upload_file = AsyncMock(side_effect=Exception("Storage service unavailable"))

        filename, file_content, content_type = mock_valid_zip_file
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, file_content, content_type)},
            data={"source_language": "auto", "target_languages": "es"},
        )

        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]

    @patch("app.api.v1.upload.storage_service")
    @patch("app.api.v1.upload.job_service")
    def test_upload_auto_language_detection(
        self, mock_job_svc, mock_storage_svc, client, mock_valid_zip_file, mock_user
    ):
        """Test: Detección automática de idioma (source_language='auto')."""
        mock_job = TranslationJobResponse(
            id=uuid4(),
            user_id=mock_user.id,
            original_filename="test_scorm.zip",
            source_language="auto",
            target_languages=["en"],
            status=TranslationStatus.UPLOADED,
            progress_percentage=0,
            created_at=datetime.utcnow(),
        )
        mock_job_svc.create_job = AsyncMock(return_value=mock_job)
        mock_job_svc.update_download_urls = AsyncMock()
        mock_job_svc.update_job_status = AsyncMock()
        mock_storage_svc.upload_file = AsyncMock(return_value=f"originals/{mock_job.id}/test_scorm.zip")
        mock_storage_svc.copy_file = AsyncMock()
        mock_storage_svc.get_download_url = AsyncMock(return_value="https://storage.example.com/url")

        filename, file_content, content_type = mock_valid_zip_file
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, file_content, content_type)},
            data={
                "source_language": "auto",  # Detectar automáticamente
                "target_languages": "en",
            },
        )

        # Assertions
        assert response.status_code == 201
        # Verificar que el job se creó con source_language='auto'
        create_call_args = mock_job_svc.create_job.call_args
        assert create_call_args[1]["job_data"].source_language == "auto"

    def test_upload_without_auth(self, test_client_no_auth, mock_valid_zip_file):
        """Test: Upload sin autenticación retorna 403."""
        filename, file_content, content_type = mock_valid_zip_file
        response = test_client_no_auth.post(
            "/api/v1/upload",
            files={"file": (filename, file_content, content_type)},
            data={"source_language": "es", "target_languages": "en"},
        )

        # Sin token de autenticación debería fallar
        assert response.status_code == 403
