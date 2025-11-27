"""
Modelos Pydantic para representar estructuras SCORM.

Filepath: backend/app/models/scorm.py
Feature alignment: STORY-005 - Parser de SCORM 1.2, STORY-006 - Extracción de Contenido
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


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


# Modelos para SCORM 2004 - Sequencing


class ScormObjective(BaseModel):
    """Objetivo de aprendizaje (SCORM 2004)."""

    identifier: str
    satisfied_by_measure: bool = False
    min_normalized_measure: Optional[float] = None


class ScormSequencingRules(BaseModel):
    """Reglas de secuenciación (SCORM 2004)."""

    # Simplified model - SCORM 2004 sequencing es muy complejo
    # Guardamos info básica para preservar estructura
    control_mode_choice: bool = True
    control_mode_flow: bool = False
    control_mode_forward_only: bool = False
    prevent_activation: bool = False
    constrained_choice: bool = False


class ScormItem(BaseModel):
    """Item dentro de una organización SCORM."""

    identifier: str
    title: str
    identifierref: Optional[str] = None  # Referencia al recurso
    parameters: Optional[str] = None
    is_visible: bool = True
    children: List["ScormItem"] = Field(default_factory=list)  # Items hijos

    # SCORM 2004 specific
    objectives: List[ScormObjective] = Field(default_factory=list)
    sequencing: Optional[ScormSequencingRules] = None
    completion_threshold: Optional[float] = None


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


# ==========================================
# Modelos para Contenido Traducible
# STORY-006: Extracción de Contenido Traducible
# ==========================================


class ContentType(str, Enum):
    """Tipo de contenido a traducir."""

    XML = "xml"  # Contenido de imsmanifest.xml
    HTML = "html"  # Contenido de archivos HTML
    TEXT = "text"  # Texto plano
    ATTRIBUTE = "attribute"  # Atributo HTML (alt, title, etc)


class TranslatableSegment(BaseModel):
    """
    Segmento individual de texto traducible.

    Representa un texto extraído de un archivo SCORM que debe traducirse,
    manteniendo información de contexto para mejor calidad de traducción.
    """

    segment_id: str  # ID único (ej: "manifest_title", "item_001_title", "html_p_5")
    content_type: ContentType
    original_text: str
    context: str  # Contexto: dónde aparece (ej: "Organization Title", "Paragraph in lesson1.html")
    xpath: Optional[str] = None  # XPath/selector para XML/HTML (para aplicar traducción después)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Metadata adicional

    # Para atributos HTML
    element_tag: Optional[str] = None  # ej: "img", "input"
    attribute_name: Optional[str] = None  # ej: "alt", "title", "placeholder"


class TranslatableContent(BaseModel):
    """
    Contenedor de todos los segmentos traducibles de un archivo.

    Agrupa todos los textos extraídos de un archivo (manifest.xml, lesson.html, etc)
    con información para poder aplicar las traducciones después.
    """

    file_path: str  # Path relativo dentro del SCORM (ej: "imsmanifest.xml", "content/lesson1.html")
    content_type: ContentType
    segments: List[TranslatableSegment] = Field(default_factory=list)
    total_characters: int = 0  # Total de caracteres a traducir (para estimación de costo)
    language_detected: Optional[str] = None  # Idioma detectado del contenido

    def add_segment(self, segment: TranslatableSegment) -> None:
        """Añadir un segmento y actualizar contador de caracteres."""
        self.segments.append(segment)
        self.total_characters += len(segment.original_text)

    def get_all_texts(self) -> List[str]:
        """Obtener lista de todos los textos a traducir."""
        return [seg.original_text for seg in self.segments]


class ExtractionResult(BaseModel):
    """
    Resultado de la extracción de contenido traducible de un paquete SCORM.

    Contiene todos los archivos procesados con sus segmentos traducibles.
    """

    scorm_package: str  # Filename del paquete
    files_processed: List[TranslatableContent] = Field(default_factory=list)
    total_segments: int = 0
    total_characters: int = 0
    extraction_date: datetime = Field(default_factory=datetime.utcnow)

    def add_file_content(self, content: TranslatableContent) -> None:
        """Añadir contenido de un archivo y actualizar contadores."""
        self.files_processed.append(content)
        self.total_segments += len(content.segments)
        self.total_characters += content.total_characters


# Necesario para referencias circulares (Item.children)
ScormItem.model_rebuild()
