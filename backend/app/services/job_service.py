"""
Servicio para gestión de Translation Jobs en Supabase.

Filepath: backend/app/services/job_service.py
Feature alignment: STORY-004 - Upload, STORY-009 - Status de Job
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
from supabase import create_client, Client
from app.core.config import settings
from app.models.translation import (
    TranslationStatus,
    TranslationJobCreate,
    TranslationJobResponse,
)

logger = logging.getLogger(__name__)


class JobService:
    """Gestión de Translation Jobs en la base de datos."""

    def __init__(self):
        """Inicializar cliente de Supabase."""
        self.client: Client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )
        self.table = "translation_jobs"

    async def create_job(
        self, job_data: TranslationJobCreate, storage_path: str
    ) -> TranslationJobResponse:
        """
        Crear un nuevo job de traducción en la base de datos.

        Args:
            job_data: Datos del job a crear
            storage_path: Path del archivo en Supabase Storage

        Returns:
            Job creado con ID asignado

        Raises:
            Exception: Si falla la creación en DB
        """
        try:
            job_id = uuid4()

            job_dict = {
                "id": str(job_id),
                "user_id": str(job_data.user_id) if job_data.user_id else None,
                "original_filename": job_data.original_filename,
                "source_language": job_data.source_language,
                "target_languages": job_data.target_languages,
                "status": TranslationStatus.UPLOADED.value,
                "progress_percentage": 0,
                "storage_path": storage_path,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Insertar en Supabase
            response = self.client.table(self.table).insert(job_dict).execute()

            logger.info(f"Job created successfully: {job_id}")

            # Convertir respuesta a modelo Pydantic
            job_response = TranslationJobResponse(
                id=job_id,
                original_filename=job_data.original_filename,
                source_language=job_data.source_language,
                target_languages=job_data.target_languages,
                status=TranslationStatus.UPLOADED,
                progress_percentage=0,
                created_at=datetime.utcnow(),
            )

            return job_response

        except Exception as e:
            logger.error(f"Failed to create job in database: {e}")
            raise Exception(f"Database error: {str(e)}")

    async def get_job(self, job_id: UUID) -> Optional[TranslationJobResponse]:
        """
        Obtener un job por ID.

        Args:
            job_id: ID del job

        Returns:
            Job encontrado o None
        """
        try:
            response = (
                self.client.table(self.table)
                .select("*")
                .eq("id", str(job_id))
                .single()
                .execute()
            )

            if response.data:
                data = response.data
                return TranslationJobResponse(
                    id=UUID(data["id"]),
                    original_filename=data["original_filename"],
                    scorm_version=data.get("scorm_version"),
                    source_language=data["source_language"],
                    target_languages=data["target_languages"],
                    status=TranslationStatus(data["status"]),
                    progress_percentage=data.get("progress_percentage", 0),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    completed_at=(
                        datetime.fromisoformat(data["completed_at"])
                        if data.get("completed_at")
                        else None
                    ),
                    download_urls=data.get("download_urls", {}),
                    error_message=data.get("error_message"),
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None

    async def update_job_status(
        self,
        job_id: UUID,
        status: TranslationStatus,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Actualizar estado de un job.

        Args:
            job_id: ID del job
            status: Nuevo estado
            progress: Progreso en porcentaje (0-100)
            error_message: Mensaje de error si status es FAILED

        Returns:
            True si se actualizó correctamente
        """
        try:
            update_data: Dict[str, Any] = {"status": status if isinstance(status, str) else status.value}

            if progress is not None:
                update_data["progress_percentage"] = progress

            if error_message:
                update_data["error_message"] = error_message

            if status == TranslationStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow().isoformat()

            self.client.table(self.table).update(update_data).eq(
                "id", str(job_id)
            ).execute()

            logger.info(f"Job {job_id} updated to status {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            return False

    async def update_download_urls(
        self, job_id: UUID, download_urls: Dict[str, str]
    ) -> bool:
        """
        Actualizar URLs de descarga del job.

        Args:
            job_id: ID del job
            download_urls: Dict con URLs por idioma {"es": "url", "fr": "url"}

        Returns:
            True si se actualizó correctamente
        """
        try:
            self.client.table(self.table).update(
                {"download_urls": download_urls}
            ).eq("id", str(job_id)).execute()

            logger.info(f"Download URLs updated for job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update download URLs for job {job_id}: {e}")
            return False


    async def list_jobs_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[str] = None,
    ) -> List[TranslationJobResponse]:
        """
        Listar jobs de un usuario con paginación.

        Args:
            user_id: ID del usuario
            limit: Máximo de resultados (default 20)
            offset: Offset para paginación
            status_filter: Filtrar por estado (opcional)

        Returns:
            Lista de jobs del usuario
        """
        try:
            query = (
                self.client.table(self.table)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
            )

            if status_filter:
                query = query.eq("status", status_filter)

            response = query.execute()

            jobs = []
            for data in response.data or []:
                jobs.append(
                    TranslationJobResponse(
                        id=UUID(data["id"]),
                        user_id=UUID(data["user_id"]) if data.get("user_id") else None,
                        original_filename=data["original_filename"],
                        scorm_version=data.get("scorm_version"),
                        source_language=data["source_language"],
                        target_languages=data["target_languages"],
                        status=TranslationStatus(data["status"]),
                        progress_percentage=data.get("progress_percentage", 0),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        completed_at=(
                            datetime.fromisoformat(data["completed_at"])
                            if data.get("completed_at")
                            else None
                        ),
                        download_urls=data.get("download_urls", {}),
                        error_message=data.get("error_message"),
                    )
                )

            logger.info(f"Found {len(jobs)} jobs for user {user_id}")
            return jobs

        except Exception as e:
            logger.error(f"Failed to list jobs for user {user_id}: {e}")
            return []

    async def count_jobs_by_user(self, user_id: str) -> int:
        """Contar total de jobs de un usuario."""
        try:
            response = (
                self.client.table(self.table)
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            return response.count or 0
        except Exception as e:
            logger.error(f"Failed to count jobs for user {user_id}: {e}")
            return 0


# Instancia global del servicio
job_service = JobService()
