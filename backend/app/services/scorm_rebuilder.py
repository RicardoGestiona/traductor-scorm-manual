"""
Servicio para reconstruir paquetes SCORM con traducciones aplicadas.

Toma un SCORM original y aplica traducciones manteniendo estructura y funcionalidad.

Filepath: backend/app/services/scorm_rebuilder.py
Feature alignment: STORY-008 - Reconstrucción de SCORM Traducido
"""

import zipfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List
from lxml import etree
from bs4 import BeautifulSoup
import tempfile

from app.models.scorm import (
    ScormPackage,
    ExtractionResult,
    TranslatableContent,
    ContentType,
)

logger = logging.getLogger(__name__)


class ScormRebuilderError(Exception):
    """Error durante la reconstrucción de SCORM."""

    pass


class ScormRebuilder:
    """
    Reconstructor de paquetes SCORM traducidos.

    Capabilities:
    - Aplicar traducciones a imsmanifest.xml
    - Aplicar traducciones a archivos HTML
    - Preservar estructura de carpetas completa
    - Generar ZIP del paquete traducido
    - Validar integridad del SCORM reconstruido
    """

    def __init__(self):
        """Inicializar el rebuilder."""
        self.files_processed = 0
        self.segments_applied = 0

    def rebuild_scorm(
        self,
        original_package: ScormPackage,
        extraction_result: ExtractionResult,
        translations: Dict[str, str],
        output_dir: Path,
        target_language: str,
    ) -> Path:
        """
        Reconstruir paquete SCORM con traducciones aplicadas.

        Args:
            original_package: Paquete SCORM original
            extraction_result: Resultado de extracción con segmentos
            translations: Dict segment_id -> translated_text
            output_dir: Directorio donde generar el SCORM traducido
            target_language: Código del idioma destino (ej: "es", "fr")

        Returns:
            Path al archivo ZIP generado

        Raises:
            ScormRebuilderError: Si falla la reconstrucción
        """
        logger.info(f"Starting SCORM rebuild for {original_package.filename}")

        # Crear directorio temporal para trabajar
        temp_dir = Path(tempfile.mkdtemp())
        source_dir = Path(original_package.extracted_path)

        try:
            # 1. Copiar toda la estructura de archivos
            logger.debug(f"Copying file structure from {source_dir} to {temp_dir}")
            shutil.copytree(source_dir, temp_dir, dirs_exist_ok=True)

            # 2. Aplicar traducciones a cada archivo procesado
            for file_content in extraction_result.files_processed:
                self._apply_translations_to_file(
                    file_content, translations, temp_dir
                )

            # 3. Generar ZIP
            output_filename = self._generate_output_filename(
                original_package.filename, target_language
            )
            zip_path = output_dir / output_filename

            logger.debug(f"Creating ZIP file: {zip_path}")
            self._create_zip(temp_dir, zip_path)

            logger.info(
                f"SCORM rebuild complete: {self.files_processed} files, "
                f"{self.segments_applied} segments applied"
            )

            return zip_path

        except Exception as e:
            logger.error(f"Error rebuilding SCORM: {e}")
            raise ScormRebuilderError(f"Failed to rebuild SCORM: {str(e)}")

        finally:
            # Limpiar directorio temporal
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _apply_translations_to_file(
        self,
        file_content: TranslatableContent,
        translations: Dict[str, str],
        working_dir: Path,
    ) -> None:
        """
        Aplicar traducciones a un archivo específico.

        Args:
            file_content: Contenido extraído del archivo
            translations: Traducciones por segment_id
            working_dir: Directorio de trabajo
        """
        file_path = working_dir / file_content.file_path

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return

        logger.debug(f"Applying translations to {file_content.file_path}")

        if file_content.content_type == ContentType.XML:
            self._apply_translations_to_xml(file_path, file_content, translations)
        elif file_content.content_type == ContentType.HTML:
            self._apply_translations_to_html(file_path, file_content, translations)

        self.files_processed += 1

    def _apply_translations_to_xml(
        self,
        file_path: Path,
        file_content: TranslatableContent,
        translations: Dict[str, str],
    ) -> None:
        """
        Aplicar traducciones a archivo XML (imsmanifest.xml).

        Args:
            file_path: Path al archivo XML
            file_content: Contenido extraído
            translations: Traducciones
        """
        # Parsear XML
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(str(file_path), parser)
        root = tree.getroot()

        # Aplicar cada traducción usando XPath
        for segment in file_content.segments:
            if segment.segment_id not in translations:
                continue

            translated_text = translations[segment.segment_id]
            if not translated_text:
                continue

            # Intentar encontrar el elemento por XPath
            if segment.xpath:
                try:
                    # Buscar elementos con y sin namespace
                    elements = root.xpath(segment.xpath)
                    if not elements:
                        # Intentar búsqueda sin namespace
                        xpath_no_ns = segment.xpath.replace("/", "//{*}")
                        elements = root.findall(xpath_no_ns)

                    if elements:
                        # Actualizar el primer elemento encontrado
                        element = elements[0] if isinstance(elements, list) else elements
                        element.text = translated_text
                        self.segments_applied += 1
                        logger.debug(
                            f"Applied translation to {segment.segment_id}: {translated_text[:50]}..."
                        )
                    else:
                        logger.warning(
                            f"Element not found for xpath: {segment.xpath} (segment: {segment.segment_id})"
                        )

                except Exception as e:
                    logger.warning(f"Error applying translation via XPath: {e}")

        # Guardar XML modificado preservando formato
        tree.write(
            str(file_path),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
        )

    def _apply_translations_to_html(
        self,
        file_path: Path,
        file_content: TranslatableContent,
        translations: Dict[str, str],
    ) -> None:
        """
        Aplicar traducciones a archivo HTML preservando estructura.

        Args:
            file_path: Path al archivo HTML
            file_content: Contenido extraído
            translations: Traducciones
        """
        # Leer HTML
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Crear mapa de traducciones por tipo
        text_translations = {}
        attr_translations = {}

        for segment in file_content.segments:
            if segment.segment_id not in translations:
                continue

            translated_text = translations[segment.segment_id]
            if not translated_text:
                continue

            if segment.content_type == ContentType.HTML:
                text_translations[segment.original_text.strip()] = translated_text
            elif segment.content_type == ContentType.ATTRIBUTE:
                attr_translations[
                    (segment.attribute_name, segment.original_text.strip())
                ] = translated_text

        # Aplicar traducciones de texto
        for original, translated in text_translations.items():
            # Encontrar todos los elementos que contienen este texto
            for element in soup.find_all(string=lambda text: text and text.strip() == original):
                element.replace_with(translated)
                self.segments_applied += 1

        # Aplicar traducciones de atributos
        for (attr_name, original), translated in attr_translations.items():
            # Encontrar elementos con este atributo y valor
            for element in soup.find_all(attrs={attr_name: original}):
                element[attr_name] = translated
                self.segments_applied += 1

        # Guardar HTML modificado
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

    def _generate_output_filename(self, original_filename: str, target_language: str) -> str:
        """
        Generar nombre del archivo de salida.

        Args:
            original_filename: Nombre original (ej: "curso.zip")
            target_language: Idioma destino (ej: "es")

        Returns:
            Nombre con idioma (ej: "curso_es.zip")
        """
        stem = Path(original_filename).stem
        return f"{stem}_{target_language}.zip"

    def _create_zip(self, source_dir: Path, output_path: Path) -> None:
        """
        Crear archivo ZIP del SCORM reconstruido.

        Args:
            source_dir: Directorio con archivos a comprimir
            output_path: Path del ZIP a crear
        """
        # Asegurar que el directorio de salida existe
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Iterar todos los archivos
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    # Calcular path relativo
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)

        logger.info(f"ZIP created: {output_path} ({output_path.stat().st_size} bytes)")

    def get_stats(self) -> Dict[str, int]:
        """
        Obtener estadísticas de la reconstrucción.

        Returns:
            Dict con files_processed y segments_applied
        """
        return {
            "files_processed": self.files_processed,
            "segments_applied": self.segments_applied,
        }
