"""
Servicio para gestión de almacenamiento en Supabase Storage.

Filepath: backend/app/services/storage.py
Feature alignment: STORY-004 - Upload de SCORM, STORY-010 - Storage
"""

import logging
from typing import Optional, BinaryIO
from uuid import UUID
from pathlib import Path
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Gestión de archivos en Supabase Storage."""

    def __init__(self):
        """Inicializar cliente de Supabase."""
        self.client: Client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        job_id: UUID,
        folder: str = "originals",
    ) -> str:
        """
        Subir archivo a Supabase Storage.

        Args:
            file: Archivo binario a subir
            filename: Nombre original del archivo
            job_id: ID del job de traducción
            folder: Carpeta dentro del bucket (originals/translated)

        Returns:
            Path del archivo en storage

        Raises:
            Exception: Si falla el upload
        """
        try:
            # Construir path: {folder}/{job_id}/{filename}
            file_path = f"{folder}/{job_id}/{filename}"

            logger.info(f"Uploading file to Supabase Storage: {file_path}")

            # Upload a Supabase Storage
            response = self.client.storage.from_(self.bucket).upload(
                path=file_path,
                file=file,
                file_options={"content-type": "application/zip"},
            )

            logger.info(f"File uploaded successfully: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise Exception(f"Storage upload failed: {str(e)}")

    async def get_signed_url(
        self, file_path: str, expires_in: int = 3600
    ) -> Optional[str]:
        """
        Generar URL firmada para descarga.

        Args:
            file_path: Path del archivo en storage
            expires_in: Segundos de validez de la URL (default 1 hora)

        Returns:
            URL firmada para descarga o None si falla
        """
        try:
            response = self.client.storage.from_(self.bucket).create_signed_url(
                path=file_path, expires_in=expires_in
            )

            if response and "signedURL" in response:
                return response["signedURL"]
            return None

        except Exception as e:
            logger.error(f"Failed to generate signed URL for {file_path}: {e}")
            return None

    async def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Descargar archivo desde storage.

        Args:
            file_path: Path del archivo en storage

        Returns:
            Contenido del archivo en bytes o None si falla
        """
        try:
            logger.info(f"Downloading file from storage: {file_path}")

            response = self.client.storage.from_(self.bucket).download(file_path)

            if response:
                logger.info(f"File downloaded successfully: {file_path}")
                return response

            logger.warning(f"No content returned for {file_path}")
            return None

        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            return None

    async def delete_file(self, file_path: str) -> bool:
        """
        Eliminar archivo de storage.

        Args:
            file_path: Path del archivo en storage

        Returns:
            True si se eliminó correctamente, False si falló
        """
        try:
            self.client.storage.from_(self.bucket).remove([file_path])
            logger.info(f"File deleted from storage: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    async def list_files_for_job(self, job_id: UUID) -> list:
        """
        Listar archivos asociados a un job.

        Args:
            job_id: ID del job de traducción

        Returns:
            Lista de archivos en storage para ese job
        """
        try:
            # Buscar en ambas carpetas: originals y translated
            files = []

            for folder in ["originals", "translated"]:
                prefix = f"{folder}/{job_id}/"
                response = self.client.storage.from_(self.bucket).list(path=prefix)
                if response:
                    files.extend(response)

            return files

        except Exception as e:
            logger.error(f"Failed to list files for job {job_id}: {e}")
            return []

    def get_file_size_mb(self, file: BinaryIO) -> float:
        """
        Obtener tamaño del archivo en MB.

        Args:
            file: Archivo binario

        Returns:
            Tamaño en MB
        """
        file.seek(0, 2)  # Ir al final del archivo
        size_bytes = file.tell()
        file.seek(0)  # Volver al inicio
        return size_bytes / (1024 * 1024)

    async def copy_file(
        self,
        source_path: str,
        dest_path: str,
        source_bucket: str = "scorm-originals",
        dest_bucket: str = "scorm-translated"
    ) -> bool:
        """
        Copiar archivo entre buckets de Supabase Storage.

        Args:
            source_path: Path del archivo origen
            dest_path: Path del archivo destino
            source_bucket: Bucket origen
            dest_bucket: Bucket destino

        Returns:
            True si se copió correctamente

        Raises:
            Exception: Si falla la copia
        """
        try:
            logger.info(f"Copying file from {source_bucket}/{source_path} to {dest_bucket}/{dest_path}")

            # Descargar archivo del bucket origen
            file_content = self.client.storage.from_(source_bucket).download(source_path)

            if not file_content:
                raise Exception(f"Could not download source file: {source_path}")

            # Subir al bucket destino
            response = self.client.storage.from_(dest_bucket).upload(
                path=dest_path,
                file=file_content,
                file_options={"content-type": "application/zip"},
            )

            logger.info(f"File copied successfully to {dest_bucket}/{dest_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            raise Exception(f"File copy failed: {str(e)}")

    async def get_download_url(
        self,
        file_path: str,
        bucket: str = "scorm-translated",
        expires_in: int = 3600
    ) -> str:
        """
        Generar URL firmada para descarga desde un bucket específico.

        Args:
            file_path: Path del archivo en storage
            bucket: Bucket del que descargar
            expires_in: Segundos de validez (default 1 hora)

        Returns:
            URL firmada para descarga

        Raises:
            Exception: Si falla la generación de URL
        """
        try:
            response = self.client.storage.from_(bucket).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )

            if response and "signedURL" in response:
                logger.info(f"Generated download URL for {bucket}/{file_path}")
                return response["signedURL"]

            raise Exception(f"No signedURL in response for {file_path}")

        except Exception as e:
            logger.error(f"Failed to generate download URL for {file_path}: {e}")
            raise Exception(f"Download URL generation failed: {str(e)}")


# Instancia global del servicio
storage_service = StorageService()
