"""
Modelos Pydantic para gestión de traducciones y jobs.

Filepath: backend/app/models/translation.py
Feature alignment: STORY-004 - Endpoint de Upload, STORY-009 - Status de Job
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TranslationStatus(str, Enum):
    """Estados posibles de un job de traducción."""

    UPLOADED = "uploaded"  # Archivo subido, en cola
    VALIDATING = "validating"  # Validando estructura SCORM
    PARSING = "parsing"  # Extrayendo textos traducibles
    TRANSLATING = "translating"  # Enviando a API de traducción
    REBUILDING = "rebuilding"  # Reconstruyendo paquete SCORM
    COMPLETED = "completed"  # Listo para descargar
    FAILED = "failed"  # Error en algún paso


class UploadResponse(BaseModel):
    """Respuesta del endpoint de upload."""

    job_id: UUID = Field(default_factory=uuid4)
    status: TranslationStatus = TranslationStatus.UPLOADED
    message: str = "SCORM package uploaded successfully"
    original_filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TranslationJobCreate(BaseModel):
    """Datos para crear un nuevo job de traducción."""

    original_filename: str
    source_language: str = "auto"  # Detectar automáticamente o especificar
    target_languages: List[str] = Field(min_length=1, max_length=10)
    user_id: Optional[UUID] = None  # Para auth en v2

    @field_validator("target_languages")
    @classmethod
    def validate_languages(cls, v):
        """Validar códigos de idioma."""
        supported = {
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
        }
        for lang in v:
            if lang not in supported:
                raise ValueError(
                    f"Unsupported language: {lang}. Supported: {supported}"
                )
        return v


class TranslationJobResponse(BaseModel):
    """Respuesta completa de un job de traducción."""

    id: UUID
    original_filename: str
    scorm_version: Optional[str] = None
    source_language: str
    target_languages: List[str]
    status: TranslationStatus
    progress_percentage: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_urls: Dict[str, str] = Field(default_factory=dict)
    error_message: Optional[str] = None

    class Config:
        from_attributes = True  # Para compatibilidad con SQLAlchemy models


class JobStatusResponse(BaseModel):
    """Respuesta del endpoint de status (GET /jobs/{id})."""

    job_id: UUID
    status: TranslationStatus
    progress_percentage: int
    current_step: Optional[str] = None
    download_urls: Dict[str, str] = Field(default_factory=dict)
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class UploadValidationError(BaseModel):
    """Error de validación en el upload."""

    field: str
    message: str
    code: str


class ErrorResponse(BaseModel):
    """Respuesta genérica de error."""

    error: str
    details: Optional[str] = None
    validation_errors: Optional[List[UploadValidationError]] = None
