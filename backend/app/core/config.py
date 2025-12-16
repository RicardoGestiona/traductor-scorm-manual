"""
Configuración de la aplicación FastAPI.

Filepath: backend/app/core/config.py
Feature alignment: EPIC-001 - Backend Core API
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación usando variables de entorno."""

    # API
    ENVIRONMENT: str = "development"
    # SECURITY: DEBUG-001 fix - Secure default, enable via .env if needed
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "scorm-originals"

    # AI Translation
    TRANSLATION_PROVIDER: str = "google"  # Options: google, argos, claude
    ANTHROPIC_API_KEY: str = ""  # Required only for claude provider
    OPENAI_API_KEY: str = ""  # Optional fallback
    ARGOS_AUTO_DOWNLOAD: bool = True  # Auto-download missing language models

    # Database
    DATABASE_URL: str = (
        "postgresql://postgres:postgres@localhost:5432/traductor_scorm"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 500
    TEMP_STORAGE_TTL_DAYS: int = 7
    ALLOWED_EXTENSIONS: List[str] = [".zip"]

    # Translation
    DEFAULT_SOURCE_LANGUAGE: str = "es"
    SUPPORTED_LANGUAGES: List[str] = [
        "es",
        "en",
        "fr",
        "de",
        "it",
        "pt",
        "nl",
        "pl",
        "zh",
        "ja",
        "ru",
        "ar",
        "ca",  # Catalán
        "gl",  # Gallego
        "eu",  # Euskera
    ]
    TRANSLATION_BATCH_SIZE: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        """Convertir MB a bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Instancia global de configuración
settings = Settings()
