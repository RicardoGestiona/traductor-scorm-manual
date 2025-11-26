"""
Modelos Pydantic para representar estructuras SCORM.

Filepath: backend/app/models/scorm.py
Feature alignment: STORY-005 - Parser de SCORM 1.2
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ScormMetadata(BaseModel):
    """Metadata del paquete SCORM."""

    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    version: Optional[str] = None


class ScormResource(BaseModel):
    """Recurso SCORM (archivo HTML, imagen, etc)."""

    identifier: str
    type: str  # "webcontent", "sco", etc
    href: Optional[str] = None  # Archivo principal (ej: index.html)
    files: List[str] = Field(default_factory=list)  # Todos los archivos del recurso
    metadata: Optional[Dict[str, Any]] = None


class ScormItem(BaseModel):
    """Item dentro de una organización SCORM."""

    identifier: str
    title: str
    identifierref: Optional[str] = None  # Referencia al recurso
    parameters: Optional[str] = None
    is_visible: bool = True
    children: List["ScormItem"] = Field(default_factory=list)  # Items hijos


class ScormOrganization(BaseModel):
    """Organización SCORM (estructura jerárquica del curso)."""

    identifier: str
    title: str
    structure: Optional[str] = None
    items: List[ScormItem] = Field(default_factory=list)


class ScormManifest(BaseModel):
    """
    Representación completa del manifest SCORM (imsmanifest.xml).

    Soporta SCORM 1.2 y 2004.
    """

    identifier: str
    version: Literal["1.2", "2004", "xapi"] = "1.2"
    metadata: ScormMetadata
    organizations: List[ScormOrganization] = Field(default_factory=list)
    resources: List[ScormResource] = Field(default_factory=list)
    default_organization: Optional[str] = None

    # Información adicional del paquete
    schema_version: Optional[str] = None
    xml_namespace: Optional[str] = None


class ScormPackage(BaseModel):
    """
    Representación completa de un paquete SCORM procesado.

    Incluye el manifest parseado y metadatos adicionales.
    """

    filename: str
    size_bytes: int
    extracted_path: str  # Path temporal donde se extrajo el ZIP
    manifest: ScormManifest
    detected_language: Optional[str] = None
    html_files: List[str] = Field(default_factory=list)  # Lista de archivos HTML traducibles
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScormValidationResult(BaseModel):
    """Resultado de la validación de un paquete SCORM."""

    is_valid: bool
    version: Optional[Literal["1.2", "2004", "xapi"]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    manifest_found: bool = False
    resources_found: int = 0


# Necesario para referencias circulares (Item.children)
ScormItem.model_rebuild()
