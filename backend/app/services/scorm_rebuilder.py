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
from app.services.filename_normalizer import (
    normalize_files_in_directory,
    update_references_in_html,
    update_references_in_xml,
    update_references_in_css,
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

            # 2. Normalizar nombres de archivo (quitar tildes y caracteres especiales)
            logger.debug("Normalizing filenames...")
            rename_map = normalize_files_in_directory(temp_dir)
            if rename_map:
                logger.info(f"Normalized {len(rename_map)} filenames")
                # Actualizar referencias en todos los archivos
                self._update_file_references(temp_dir, rename_map)

            # 3. Aplicar traducciones a cada archivo procesado
            for file_content in extraction_result.files_processed:
                self._apply_translations_to_file(
                    file_content, translations, temp_dir
                )

            # 4. Generar ZIP
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

    def _update_file_references(
        self, working_dir: Path, rename_map: Dict[str, str]
    ) -> None:
        """
        Actualizar referencias a archivos renombrados en HTML, XML y CSS.

        Args:
            working_dir: Directorio de trabajo
            rename_map: Mapeo de rutas originales a normalizadas
        """
        if not rename_map:
            return

        logger.debug(f"Updating file references for {len(rename_map)} renamed files")

        # Procesar todos los archivos que pueden contener referencias
        for file_path in working_dir.rglob("*"):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()

            try:
                if suffix in [".html", ".htm"]:
                    self._update_html_references(file_path, rename_map)
                elif suffix == ".xml":
                    self._update_xml_references(file_path, rename_map)
                elif suffix == ".css":
                    self._update_css_references(file_path, rename_map)
                elif suffix == ".js":
                    # JavaScript también puede tener referencias a imágenes
                    self._update_js_references(file_path, rename_map)
            except Exception as e:
                logger.warning(f"Error updating references in {file_path}: {e}")

    def _update_html_references(
        self, file_path: Path, rename_map: Dict[str, str]
    ) -> None:
        """Actualizar referencias en archivo HTML."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        updated_content = update_references_in_html(content, rename_map)

        if content != updated_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            logger.debug(f"Updated references in {file_path.name}")

    def _update_xml_references(
        self, file_path: Path, rename_map: Dict[str, str]
    ) -> None:
        """Actualizar referencias en archivo XML."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        updated_content = update_references_in_xml(content, rename_map)

        if content != updated_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            logger.debug(f"Updated references in {file_path.name}")

    def _update_css_references(
        self, file_path: Path, rename_map: Dict[str, str]
    ) -> None:
        """Actualizar referencias en archivo CSS."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        updated_content = update_references_in_css(content, rename_map)

        if content != updated_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            logger.debug(f"Updated references in {file_path.name}")

    def _update_js_references(
        self, file_path: Path, rename_map: Dict[str, str]
    ) -> None:
        """Actualizar referencias en archivo JavaScript."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        updated_content = content
        for original, normalized in rename_map.items():
            # Reemplazar strings literales que contengan el path
            updated_content = updated_content.replace(f'"{original}"', f'"{normalized}"')
            updated_content = updated_content.replace(f"'{original}'", f"'{normalized}'")

        if content != updated_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            logger.debug(f"Updated references in {file_path.name}")

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
