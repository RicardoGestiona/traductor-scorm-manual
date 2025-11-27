"""
Tests para el endpoint de jobs (status tracking).

Filepath: backend/tests/test_jobs_endpoint.py
Feature alignment: STORY-009 - Endpoint de Status de Job
"""

import pytest
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.translation import TranslationStatus, TranslationJobResponse


@pytest.fixture
def client():
    """Cliente de test de FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_job_uploaded():
    """Job en estado UPLOADED."""
    return TranslationJobResponse(
        id=uuid4(),
        original_filename="curso_basico.zip",
        scorm_version=None,  # Aún no detectado
        source_language="auto",
        target_languages=["es", "fr"],
        status=TranslationStatus.UPLOADED,
        progress_percentage=0,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_job_translating():
    """Job en proceso de traducción."""
    return TranslationJobResponse(
        id=uuid4(),
        original_filename="curso_avanzado.zip",
        scorm_version="1.2",
        source_language="en",
        target_languages=["es", "fr", "de"],
        status=TranslationStatus.TRANSLATING,
        progress_percentage=45,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_job_completed():
    """Job completado con download URLs."""
    job_id = uuid4()
    return TranslationJobResponse(
        id=job_id,
        original_filename="curso_completo.zip",
        scorm_version="2004",
        source_language="en",
        target_languages=["es", "fr"],
        status=TranslationStatus.COMPLETED,
        progress_percentage=100,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        download_urls={
            "es": f"https://storage.supabase.co/translated/{job_id}/curso_es.zip",
            "fr": f"https://storage.supabase.co/translated/{job_id}/curso_fr.zip",
        },
    )


@pytest.fixture
def mock_job_failed():
    """Job que falló."""
    return TranslationJobResponse(
        id=uuid4(),
        original_filename="curso_corrupto.zip",
        scorm_version="1.2",
        source_language="es",
        target_languages=["en"],
        status=TranslationStatus.FAILED,
        progress_percentage=25,
        created_at=datetime.utcnow(),
        error_message="Invalid SCORM manifest: missing imsmanifest.xml",
    )


class TestJobsEndpoint:
    """Tests del endpoint GET /api/v1/jobs/{job_id}."""

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_status_uploaded(self, mock_get_job, client, mock_job_uploaded):
        """Test: Obtener status de job recién subido."""
        mock_get_job.return_value = mock_job_uploaded

        response = client.get(f"/api/v1/jobs/{mock_job_uploaded.id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(mock_job_uploaded.id)
        assert data["status"] == "uploaded"
        assert data["progress_percentage"] == 0
        assert "current_step" in data
        assert "uploaded successfully" in data["current_step"].lower()
        assert data["download_urls"] == {}

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_status_translating(
        self, mock_get_job, client, mock_job_translating
    ):
        """Test: Obtener status de job en proceso."""
        mock_get_job.return_value = mock_job_translating

        response = client.get(f"/api/v1/jobs/{mock_job_translating.id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "translating"
        assert data["progress_percentage"] == 45
        assert "translating" in data["current_step"].lower()
        assert "45%" in data["current_step"]

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_status_completed(self, mock_get_job, client, mock_job_completed):
        """Test: Obtener status de job completado con download URLs."""
        mock_get_job.return_value = mock_job_completed

        response = client.get(f"/api/v1/jobs/{mock_job_completed.id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100
        assert "completed" in data["current_step"].lower()
        assert len(data["download_urls"]) == 2
        assert "es" in data["download_urls"]
        assert "fr" in data["download_urls"]
        assert "storage.supabase.co" in data["download_urls"]["es"]

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_status_failed(self, mock_get_job, client, mock_job_failed):
        """Test: Obtener status de job que falló."""
        mock_get_job.return_value = mock_job_failed

        response = client.get(f"/api/v1/jobs/{mock_job_failed.id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["progress_percentage"] == 25
        assert data["error_message"] is not None
        assert "imsmanifest.xml" in data["error_message"]
        assert "failed" in data["current_step"].lower()

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_status_not_found(self, mock_get_job, client):
        """Test: Job no encontrado retorna 404."""
        mock_get_job.return_value = None
        job_id = uuid4()

        response = client.get(f"/api/v1/jobs/{job_id}")

        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]["error"].lower()

    def test_get_job_status_invalid_uuid(self, client):
        """Test: UUID inválido retorna 422."""
        response = client.get("/api/v1/jobs/not-a-valid-uuid")

        # Assertions
        assert response.status_code == 422  # Unprocessable Entity

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_status_service_error(self, mock_get_job, client):
        """Test: Error del servicio retorna 500."""
        mock_get_job.side_effect = Exception("Database connection failed")
        job_id = uuid4()

        response = client.get(f"/api/v1/jobs/{job_id}")

        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]


class TestJobDetailsEndpoint:
    """Tests del endpoint GET /api/v1/jobs/{job_id}/details."""

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_details_success(self, mock_get_job, client, mock_job_completed):
        """Test: Obtener detalles completos de un job."""
        mock_get_job.return_value = mock_job_completed

        response = client.get(f"/api/v1/jobs/{mock_job_completed.id}/details")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        # Verificar que se incluyen todos los campos
        assert "id" in data
        assert "original_filename" in data
        assert "scorm_version" in data
        assert "source_language" in data
        assert "target_languages" in data
        assert "status" in data
        assert "progress_percentage" in data
        assert "created_at" in data
        assert "completed_at" in data
        assert "download_urls" in data

        # Verificar valores específicos
        assert data["original_filename"] == "curso_completo.zip"
        assert data["scorm_version"] == "2004"
        assert len(data["target_languages"]) == 2

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_details_not_found(self, mock_get_job, client):
        """Test: Detalles de job no encontrado retorna 404."""
        mock_get_job.return_value = None
        job_id = uuid4()

        response = client.get(f"/api/v1/jobs/{job_id}/details")

        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["error"].lower()

    @patch("app.services.job_service.job_service.get_job")
    def test_get_job_details_vs_status_response_difference(
        self, mock_get_job, client, mock_job_completed
    ):
        """Test: Verificar que /details retorna más info que /status."""
        mock_get_job.return_value = mock_job_completed

        # GET status (lighter)
        status_response = client.get(f"/api/v1/jobs/{mock_job_completed.id}")
        status_data = status_response.json()

        # GET details (full)
        details_response = client.get(f"/api/v1/jobs/{mock_job_completed.id}/details")
        details_data = details_response.json()

        # Assertions
        # Status tiene campos básicos + current_step
        assert "current_step" in status_data
        assert "job_id" in status_data

        # Details tiene TODOS los campos del modelo completo
        assert "original_filename" in details_data
        assert "scorm_version" in details_data
        assert "created_at" in details_data

        # Status NO tiene filename (más ligero para polling)
        assert "original_filename" not in status_data


class TestCurrentStepDescriptions:
    """Tests de las descripciones de pasos actuales."""

    @patch("app.services.job_service.job_service.get_job")
    def test_current_step_descriptions_all_statuses(
        self, mock_get_job, client, mock_job_uploaded
    ):
        """Test: Verificar que todos los estados tienen descripción."""
        statuses_to_test = [
            (TranslationStatus.UPLOADED, "uploaded"),
            (TranslationStatus.VALIDATING, "validating"),
            (TranslationStatus.PARSING, "extracting"),
            (TranslationStatus.TRANSLATING, "translating"),
            (TranslationStatus.REBUILDING, "rebuilding"),
            (TranslationStatus.COMPLETED, "completed"),
            (TranslationStatus.FAILED, "failed"),
        ]

        for status, expected_keyword in statuses_to_test:
            job = mock_job_uploaded
            job.status = status
            job.progress_percentage = 50 if status != TranslationStatus.COMPLETED else 100
            mock_get_job.return_value = job

            response = client.get(f"/api/v1/jobs/{job.id}")
            data = response.json()

            # Verificar que hay descripción y contiene keyword esperado
            assert "current_step" in data
            assert expected_keyword.lower() in data["current_step"].lower()
