"""
Servicio para extraer contenido traducible de paquetes SCORM.

Extrae textos de archivos XML (imsmanifest.xml) y HTML manteniendo
contexto y estructura para posterior traducción y reconstrucción.

Filepath: backend/app/services/content_extractor.py
Feature alignment: STORY-006 - Extracción de Contenido Traducible
"""

from pathlib import Path
from typing import List, Optional, Set
from bs4 import BeautifulSoup, Tag, NavigableString
from lxml import etree
import logging

from app.models.scorm import (
    TranslatableContent,
    TranslatableSegment,
    ContentType,
    ExtractionResult,
    ScormManifest,
)

logger = logging.getLogger(__name__)


class ContentExtractorError(Exception):
    """Error durante la extracción de contenido."""

    pass


class ContentExtractor:
    """
    Extractor de contenido traducible de paquetes SCORM.

    Capabilities:
    - Extraer textos de imsmanifest.xml (títulos, descripciones)
    - Extraer textos de archivos HTML (p, h1-6, span, li, etc)
    - Extraer atributos traducibles (alt, title, placeholder)
    - Filtrar elementos no traducibles (script, style, code)
    - Mantener contexto y estructura para aplicar traducciones
    """

    # Tags HTML cuyos textos deben traducirse
    TRANSLATABLE_TAGS = {
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "span",
        "div",
        "li",
        "td",
        "th",
        "a",
        "label",
        "button",
        "strong",
        "em",
        "b",
        "i",
        "u",
        "blockquote",
        "figcaption",
        "caption",
        "legend",
        "summary",
        "details",
        "option",
    }

    # Tags que deben ignorarse completamente (incluido su contenido)
    NON_TRANSLATABLE_TAGS = {
        "script",  # JavaScript
        "style",  # CSS
        "code",  # Código inline
        "pre",  # Código pre-formateado
        "noscript",  # Fallback de script
    }

    # Atributos HTML que deben traducirse
    TRANSLATABLE_ATTRIBUTES = {
        "alt",  # Texto alternativo de imágenes
        "title",  # Tooltip text
        "placeholder",  # Placeholder de inputs
        "aria-label",  # Accesibilidad
        "aria-description",  # Accesibilidad
    }

    # Longitud mínima de texto para considerar traducción (evitar espacios, números solos)
    MIN_TEXT_LENGTH = 3

    def __init__(self):
        """Inicializar el extractor."""
        pass

    def extract_from_scorm_package(
        self, package_path: Path, manifest: ScormManifest, html_files: List[str]
    ) -> ExtractionResult:
        """
        Extraer todo el contenido traducible de un paquete SCORM.

        Args:
            package_path: Path al directorio extraído del SCORM
            manifest: Manifest parseado del SCORM
            html_files: Lista de archivos HTML encontrados

        Returns:
            ExtractionResult con todos los segmentos traducibles
        """
        result = ExtractionResult(scorm_package=package_path.name)

        # 1. Extraer contenido del manifest
        manifest_content = self.extract_from_manifest(manifest)
        if manifest_content.segments:
            result.add_file_content(manifest_content)

        # 2. Extraer contenido de cada archivo HTML
        for html_file in html_files:
            html_path = package_path / html_file
            if not html_path.exists():
                logger.warning(f"HTML file not found: {html_file}")
                continue

            try:
                html_content = self.extract_from_html_file(html_path, html_file)
                if html_content.segments:
                    result.add_file_content(html_content)
            except Exception as e:
                logger.error(f"Error extracting from {html_file}: {e}")
                continue

        logger.info(
            f"Extraction complete: {result.total_segments} segments, "
            f"{result.total_characters} characters from {len(result.files_processed)} files"
        )

        return result

    def extract_from_manifest(self, manifest: ScormManifest) -> TranslatableContent:
        """
        Extraer contenido traducible de imsmanifest.xml.

        Extrae:
        - Títulos de organizaciones
        - Títulos de items
        - Descripciones en metadata

        Args:
            manifest: ScormManifest parseado

        Returns:
            TranslatableContent con segmentos del manifest
        """
        content = TranslatableContent(
            file_path="imsmanifest.xml", content_type=ContentType.XML
        )

        # Extraer metadata del curso
        if manifest.metadata.title:
            content.add_segment(
                TranslatableSegment(
                    segment_id="manifest_metadata_title",
                    content_type=ContentType.XML,
                    original_text=manifest.metadata.title,
                    context="Course title (metadata)",
                    xpath="//metadata/lom/general/title/langstring",
                )
            )

        if manifest.metadata.description:
            content.add_segment(
                TranslatableSegment(
                    segment_id="manifest_metadata_description",
                    content_type=ContentType.XML,
                    original_text=manifest.metadata.description,
                    context="Course description (metadata)",
                    xpath="//metadata/lom/general/description/langstring",
                )
            )

        # Extraer títulos de organizaciones e items
        for org_idx, org in enumerate(manifest.organizations):
            if org.title:
                content.add_segment(
                    TranslatableSegment(
                        segment_id=f"org_{org.identifier}_title",
                        content_type=ContentType.XML,
                        original_text=org.title,
                        context=f"Organization '{org.identifier}' title",
                        xpath=f"//organization[@identifier='{org.identifier}']/title",
                    )
                )

            # Extraer títulos de items recursivamente
            self._extract_from_items(org.items, content, org.identifier)

        return content

    def _extract_from_items(
        self,
        items: List,
        content: TranslatableContent,
        parent_context: str,
        level: int = 0,
    ) -> None:
        """
        Extraer títulos de items recursivamente.

        Args:
            items: Lista de ScormItem
            content: TranslatableContent donde añadir segmentos
            parent_context: Contexto del padre
            level: Nivel de profundidad
        """
        for item in items:
            if item.title:
                content.add_segment(
                    TranslatableSegment(
                        segment_id=f"item_{item.identifier}_title",
                        content_type=ContentType.XML,
                        original_text=item.title,
                        context=f"Item '{item.identifier}' title (level {level})",
                        xpath=f"//item[@identifier='{item.identifier}']/title",
                    )
                )

            # Recursión para items hijos
            if item.children:
                self._extract_from_items(
                    item.children, content, item.identifier, level + 1
                )

    def extract_from_html_file(
        self, html_path: Path, relative_path: str
    ) -> TranslatableContent:
        """
        Extraer contenido traducible de un archivo HTML.

        Args:
            html_path: Path absoluto al archivo HTML
            relative_path: Path relativo dentro del SCORM

        Returns:
            TranslatableContent con segmentos del HTML
        """
        content = TranslatableContent(
            file_path=relative_path, content_type=ContentType.HTML
        )

        # Leer y parsear HTML
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            html_text = f.read()

        soup = BeautifulSoup(html_text, "html.parser")

        # Eliminar tags no traducibles
        for tag in self.NON_TRANSLATABLE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()

        # Extraer textos de tags traducibles
        segment_counter = 0
        for tag_name in self.TRANSLATABLE_TAGS:
            for element in soup.find_all(tag_name):
                # Extraer texto directo (no de hijos)
                text = self._get_direct_text(element)
                if text and len(text.strip()) >= self.MIN_TEXT_LENGTH:
                    segment_counter += 1
                    content.add_segment(
                        TranslatableSegment(
                            segment_id=f"html_{tag_name}_{segment_counter}",
                            content_type=ContentType.HTML,
                            original_text=text.strip(),
                            context=f"{tag_name} element in {relative_path}",
                            element_tag=tag_name,
                            metadata={"element_id": element.get("id"), "class": element.get("class")},
                        )
                    )

        # Extraer atributos traducibles de TODOS los elementos (no solo los con texto)
        # Esto captura atributos de <img>, <input>, etc.
        for attr in self.TRANSLATABLE_ATTRIBUTES:
            for element in soup.find_all(attrs={attr: True}):
                attr_value = element.get(attr)
                if attr_value and len(attr_value.strip()) >= self.MIN_TEXT_LENGTH:
                    segment_counter += 1
                    content.add_segment(
                        TranslatableSegment(
                            segment_id=f"html_attr_{attr}_{segment_counter}",
                            content_type=ContentType.ATTRIBUTE,
                            original_text=attr_value.strip(),
                            context=f"{attr} attribute of {element.name} in {relative_path}",
                            element_tag=element.name,
                            attribute_name=attr,
                            metadata={"element_id": element.get("id")},
                        )
                    )

        return content

    def _get_direct_text(self, element: Tag) -> str:
        """
        Obtener solo el texto directo de un elemento (no de hijos).

        Args:
            element: Elemento BeautifulSoup

        Returns:
            Texto directo del elemento
        """
        # Obtener solo NavigableString directos (no de elementos hijos)
        direct_texts = [
            str(child).strip()
            for child in element.children
            if isinstance(child, NavigableString) and str(child).strip()
        ]
        return " ".join(direct_texts)
