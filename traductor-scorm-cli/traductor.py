#!/usr/bin/env python3
"""
Traductor SCORM CLI - Versión simplificada

Traduce paquetes SCORM a múltiples idiomas usando Google Translate.
Soporta SCORM 1.2, 2004 y Articulate Rise.

Uso:
    python traductor.py mi-curso.zip --idioma ca
    python traductor.py mi-curso.zip --idioma en,fr,de
"""

import argparse
import asyncio
import base64
import json
import logging
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from lxml import etree

# ============================================================================
# LOGGING ESTRUCTURADO
# ============================================================================

class JsonFormatter(logging.Formatter):
    """Formatter que emite logs en formato JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class Segment:
    """Segmento de texto traducible."""
    id: str
    text: str
    path: str  # XPath o JSON path
    is_html: bool = False


@dataclass
class ScormPackage:
    """Paquete SCORM parseado."""
    zip_path: Path
    extracted_path: Path
    version: str
    title: Optional[str]
    html_files: List[str]


@dataclass
class ExtractionResult:
    """Resultado de extracción de contenido."""
    segments: List[Segment] = field(default_factory=list)
    files: Dict[str, List[Segment]] = field(default_factory=dict)


# ============================================================================
# PARSER DE SCORM
# ============================================================================

class ScormParser:
    """Parser de paquetes SCORM 1.2 y 2004."""
    
    NAMESPACES = {
        'imscp': 'http://www.imsproject.org/xsd/imscp_rootv1p1p2',
        'adlcp': 'http://www.adlnet.org/xsd/adlcp_rootv1p2',
        'imsmd': 'http://www.imsglobal.org/xsd/imsmd_rootv1p2p1',
    }
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp())
    
    def parse(self, zip_path: Path) -> ScormPackage:
        """Parsear un paquete SCORM."""
        extract_path = self.temp_dir / f"scorm_{zip_path.stem}"
        manifest_path = self._extract_zip(zip_path, extract_path)

        scorm_root = (extract_path / manifest_path).parent
        tree = etree.parse(str(extract_path / manifest_path))
        root = tree.getroot()

        return ScormPackage(
            zip_path=zip_path,
            extracted_path=scorm_root,
            version=self._detect_version(root),
            title=self._extract_title(root),
            html_files=self._find_html_files(scorm_root),
        )

    def _extract_zip(self, zip_path: Path, extract_path: Path) -> str:
        """Extraer ZIP y retornar ruta al manifest.

        Returns:
            Ruta relativa del imsmanifest.xml dentro del ZIP.

        Raises:
            ValueError: Si no encuentra manifest.
        """
        extract_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as z:
            manifest_path = self._find_manifest(z.namelist())
            if not manifest_path:
                raise ValueError("No se encontró imsmanifest.xml")

            # Extraer archivos (salvo __MACOSX)
            for member in z.namelist():
                if not member.startswith('__MACOSX'):
                    z.extract(member, extract_path)

        return manifest_path
    
    def _find_manifest(self, file_list: List[str]) -> Optional[str]:
        """Buscar imsmanifest.xml en el ZIP."""
        for name in file_list:
            if name.lower().endswith('imsmanifest.xml') and '__MACOSX' not in name:
                return name
        return None
    
    def _detect_version(self, root: etree._Element) -> str:
        """Detectar versión de SCORM."""
        ns_map = root.nsmap
        if any('2004' in str(v) for v in ns_map.values()):
            return "2004"
        return "1.2"
    
    def _extract_title(self, root: etree._Element) -> Optional[str]:
        """Extraer título del curso."""
        # Buscar en organizations
        for org in root.iter():
            if 'organization' in org.tag.lower():
                for child in org:
                    if 'title' in child.tag.lower() and child.text:
                        return child.text.strip()
        return None
    
    def _find_html_files(self, path: Path) -> List[str]:
        """Encontrar archivos HTML en el paquete."""
        html_files = []
        for ext in ['*.html', '*.htm']:
            for f in path.rglob(ext):
                rel_path = str(f.relative_to(path))
                html_files.append(rel_path)
        return sorted(html_files)


# ============================================================================
# EXTRACTOR DE CONTENIDO
# ============================================================================

class ContentExtractor:
    """Extractor de contenido traducible de SCORM."""
    
    # Tags HTML con contenido traducible
    TEXT_TAGS = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'li', 
                 'td', 'th', 'label', 'button', 'a', 'option', 'title'}
    
    # Tags a ignorar
    SKIP_TAGS = {'script', 'style', 'code', 'pre', 'noscript'}
    
    # Atributos traducibles
    TRANSLATABLE_ATTRS = {'alt', 'title', 'placeholder', 'aria-label'}
    
    # Campos de Articulate Rise
    RISE_FIELDS = {'title', 'heading', 'paragraph', 'description', 'caption',
                   'text', 'label', 'buttonText', 'question', 'answer', 'feedback'}
    
    def extract(self, package: ScormPackage) -> ExtractionResult:
        """Extraer contenido traducible del paquete."""
        result = ExtractionResult()
        
        # Extraer del manifest
        manifest_segments = self._extract_manifest(package.extracted_path)
        if manifest_segments:
            result.files['imsmanifest.xml'] = manifest_segments
            result.segments.extend(manifest_segments)
        
        # Extraer de archivos HTML
        for html_file in package.html_files:
            html_path = package.extracted_path / html_file
            
            # Verificar si es Articulate Rise
            if self._is_rise_course(html_path):
                segments = self._extract_rise(html_path, html_file)
            else:
                segments = self._extract_html(html_path, html_file)
            
            if segments:
                result.files[html_file] = segments
                result.segments.extend(segments)
        
        return result
    
    def _extract_manifest(self, scorm_root: Path) -> List[Segment]:
        """Extraer textos del manifest."""
        manifest_path = scorm_root / 'imsmanifest.xml'
        if not manifest_path.exists():
            return []
        
        segments = []
        tree = etree.parse(str(manifest_path))
        
        # Extraer títulos de organizaciones e items
        for i, elem in enumerate(tree.iter()):
            # Saltar elementos sin tag string (comments, PI, etc)
            if not isinstance(elem.tag, str):
                continue
                
            tag_name = elem.tag.split('}')[-1].lower() if '}' in elem.tag else elem.tag.lower()
            
            if tag_name == 'title' and elem.text and elem.text.strip():
                text = elem.text.strip()
                if len(text) >= 2:
                    parent = elem.getparent()
                    parent_tag = parent.tag.split('}')[-1] if parent is not None and isinstance(parent.tag, str) else 'root'
                    parent_id = parent.get('identifier', str(i)) if parent is not None else str(i)
                    
                    seg_id = f"{parent_tag}_{parent_id}_title"
                    path = tree.getpath(elem)
                    segments.append(Segment(id=seg_id, text=text, path=path))
        
        return segments
    
    def _is_rise_course(self, html_path: Path) -> bool:
        """Verificar si es un curso Articulate Rise."""
        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)
            return '__fetchCourse' in content and 'deserialize(' in content
        except (IOError, OSError) as e:
            logger.debug(f"Cannot read HTML file: {html_path}", exc_info=True)
            return False
    
    def _extract_rise(self, html_path: Path, rel_path: str) -> List[Segment]:
        """Extraer contenido de Articulate Rise."""
        segments = []

        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Buscar base64 encoded content
            match = re.search(r'deserialize\("([A-Za-z0-9+/=]+)"\)', content)
            if not match:
                return segments

            # Decodificar JSON
            decoded = base64.b64decode(match.group(1)).decode('utf-8')
            data = json.loads(decoded)

            # Extraer recursivamente
            self._extract_from_json(data, "", segments)

        except (IOError, OSError) as e:
            logger.error(f"Cannot read Rise file: {html_path}", exc_info=True)
        except (base64.binascii.Error, json.JSONDecodeError) as e:
            logger.error(f"Invalid Rise JSON encoding in {rel_path}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error extracting Rise from {rel_path}: {e}", exc_info=True)

        return segments
    
    def _extract_from_json(self, data: Any, path: str, segments: List[Segment]):
        """Extraer recursivamente de JSON de Rise."""
        if isinstance(data, dict):
            for key, value in data.items():
                # Saltar campos no traducibles
                if self._is_skippable_key(key):
                    continue

                new_path = f"{path}.{key}" if path else key

                if isinstance(value, str) and len(value) >= 3:
                    self._process_json_value(value, key, new_path, segments)
                else:
                    self._extract_from_json(value, new_path, segments)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._extract_from_json(item, f"{path}[{i}]", segments)

    def _is_skippable_key(self, key: str) -> bool:
        """Determinar si una clave de JSON debe ignorarse."""
        non_translatable = {'id', 'key', 'src', 'href', 'type', 'color', 'icon',
                           'media', 'settings', 'background'}
        return key in non_translatable

    def _process_json_value(self, value: str, key: str, path: str, segments: List[Segment]) -> None:
        """Procesar un valor de string en JSON Rise."""
        text = self._clean_html(value) if '<' in value else value.strip()

        if not text or len(text) < 3:
            return

        # Verificar si es texto traducible
        is_translatable = key.lower() in self.RISE_FIELDS
        is_ui_label = 'labelSet.labels' in path
        is_valid_text = not self._is_non_text(text) and (is_translatable or is_ui_label or self._is_real_text(text))

        if is_valid_text:
            seg_id = f"rise_{path.replace('.', '_')}"
            segments.append(Segment(
                id=seg_id,
                text=value,  # Mantener original con HTML
                path=path,
                is_html='<' in value
            ))
    
    def _extract_html(self, html_path: Path, rel_path: str) -> List[Segment]:
        """Extraer contenido de HTML estándar."""
        segments = []

        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'html.parser')

            # Eliminar tags a ignorar
            for tag in soup.find_all(self.SKIP_TAGS):
                tag.decompose()

            # Extraer textos y atributos
            for i, elem in enumerate(soup.find_all(self.TEXT_TAGS)):
                self._extract_element_and_attrs(elem, i, rel_path, segments)

        except (IOError, OSError) as e:
            logger.error(f"Cannot read HTML file: {html_path}", exc_info=True)
        except Exception as e:
            logger.error(f"Error parsing HTML from {rel_path}: {e}", exc_info=True)

        return segments

    def _extract_element_and_attrs(self, elem, index: int, rel_path: str, segments: List[Segment]) -> None:
        """Extraer texto de elemento HTML y sus atributos traducibles."""
        text = elem.get_text(strip=True)
        if text and len(text) >= 3:
            tag_name = elem.name
            seg_id = f"html_{rel_path}_{tag_name}_{index}"
            segments.append(Segment(id=seg_id, text=text, path=f"//{tag_name}[{index}]"))

        # Extraer atributos traducibles
        for attr in self.TRANSLATABLE_ATTRS:
            if elem.has_attr(attr):
                attr_text = elem[attr]
                if attr_text and len(attr_text) >= 3:
                    tag_name = elem.name
                    seg_id = f"html_{rel_path}_{tag_name}_{index}_{attr}"
                    segments.append(Segment(
                        id=seg_id,
                        text=attr_text,
                        path=f"//{tag_name}[{index}]/@{attr}"
                    ))
    
    def _clean_html(self, html: str) -> str:
        """Extraer texto de HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    
    def _is_non_text(self, text: str) -> bool:
        """Verificar si parece URL, ID, código, etc."""
        if text.startswith(('http://', 'https://', '//', 'mailto:')):
            return True
        if re.match(r'^[a-f0-9\-]{32,}$', text.lower()):
            return True
        if re.match(r'^#[0-9a-fA-F]{3,8}$', text):
            return True
        if re.match(r'^[\d.,\s]+$', text):
            return True
        return False
    
    def _is_real_text(self, text: str) -> bool:
        """Verificar si parece texto real traducible."""
        if not re.search(r'[a-zA-ZáéíóúñüÁÉÍÓÚÑÜàèìòùç]', text):
            return False
        words = re.findall(r'\b\w+\b', text)
        return len(words) >= 1


# ============================================================================
# TRADUCTOR
# ============================================================================

class Translator:
    """Traductor usando Google Translate."""
    
    def __init__(self):
        self.chars_translated = 0
    
    async def translate(
        self,
        segments: List[Segment],
        source_lang: str,
        target_lang: str
    ) -> Dict[str, str]:
        """Traducir lista de segmentos."""
        translations = {}

        for i, seg in enumerate(segments):
            try:
                result = await self._translate_segment(seg, source_lang, target_lang)
                if result:
                    translations[seg.id] = result

                # Log de progreso cada 50 segmentos
                if (i + 1) % 50 == 0:
                    logger.debug("Translation progress", extra={"current": i + 1, "total": len(segments)})

                # Pequeña pausa para evitar rate limiting
                if (i + 1) % 20 == 0:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error translating segment {seg.id}", extra={"segment": seg.id}, exc_info=True)
                translations[seg.id] = seg.text  # Mantener original

        return translations

    async def _translate_segment(self, seg: Segment, source_lang: str, target_lang: str) -> Optional[str]:
        """Traducir un segmento individual."""
        text = self._clean_html(seg.text) if seg.is_html else seg.text

        if not text or len(text) < 2:
            return None

        translated = await self._translate_text(text, source_lang, target_lang)
        self.chars_translated += len(text)

        # Si era HTML, reconstruir con traducción
        if seg.is_html:
            return self._replace_in_html(seg.text, text, translated)
        else:
            return translated

    async def _translate_text(self, text: str, source: str, target: str) -> str:
        """Traducir texto individual."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: GoogleTranslator(source=source, target=target).translate(text)
        )
    
    def _clean_html(self, html: str) -> str:
        """Extraer texto de HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    def _replace_in_html(self, original_html: str, original_text: str, translated: str) -> str:
        """Reemplazar texto en HTML manteniendo estructura (primera ocurrencia solo)."""
        # Buscar la primera ocurrencia para evitar múltiples reemplazos
        idx = original_html.find(original_text)
        if idx != -1:
            return original_html[:idx] + translated + original_html[idx + len(original_text):]
        logger.warning(f"Text not found in HTML: {original_text[:50]}")
        return original_html


# ============================================================================
# RECONSTRUCTOR
# ============================================================================

class ScormRebuilder:
    """Reconstructor de paquetes SCORM traducidos."""
    
    def rebuild(
        self,
        package: ScormPackage,
        extraction: ExtractionResult,
        translations: Dict[str, str],
        output_dir: Path,
        target_lang: str
    ) -> Path:
        """Reconstruir SCORM con traducciones."""
        working_dir = output_dir / f"work_{target_lang}"
        self._prepare_working_dir(working_dir, package.extracted_path)
        self._apply_translations_to_files(working_dir, extraction, translations)

        output_path = self._create_zip(package, working_dir, output_dir, target_lang)
        shutil.rmtree(working_dir, ignore_errors=True)

        return output_path

    def _prepare_working_dir(self, working_dir: Path, source_path: Path) -> None:
        """Preparar directorio de trabajo limpio."""
        if working_dir.exists():
            shutil.rmtree(working_dir)
        shutil.copytree(source_path, working_dir)

    def _apply_translations_to_files(
        self,
        working_dir: Path,
        extraction: ExtractionResult,
        translations: Dict[str, str]
    ) -> None:
        """Aplicar traducciones a cada archivo del paquete."""
        for file_path, segments in extraction.files.items():
            full_path = working_dir / file_path

            if file_path == 'imsmanifest.xml':
                self._apply_to_manifest(full_path, segments, translations)
            elif self._is_rise_file(full_path):
                self._apply_to_rise(full_path, segments, translations)
            else:
                self._apply_to_html(full_path, segments, translations)

    def _create_zip(self, package: ScormPackage, working_dir: Path, output_dir: Path, target_lang: str) -> Path:
        """Crear archivo ZIP del paquete traducido."""
        output_name = f"{package.zip_path.stem}_{target_lang}.zip"
        output_path = output_dir / output_name

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for file in working_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(working_dir)
                    z.write(file, arcname)

        return output_path
    
    def _is_rise_file(self, path: Path) -> bool:
        """Verificar si es archivo Rise."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)
            return 'deserialize(' in content
        except (IOError, OSError) as e:
            logger.debug(f"Cannot read file to check if Rise: {path}", exc_info=True)
            return False
    
    def _apply_to_manifest(self, path: Path, segments: List[Segment], translations: Dict[str, str]):
        """Aplicar traducciones al manifest XML."""
        try:
            tree = etree.parse(str(path))

            for seg in segments:
                if seg.id in translations:
                    # Buscar elemento por XPath
                    try:
                        elements = tree.xpath(seg.path)
                        if elements:
                            elements[0].text = translations[seg.id]
                    except etree.XPathError as e:
                        logger.warning(f"Invalid XPath {seg.path}: {e}")

            tree.write(str(path), encoding='utf-8', xml_declaration=True)
        except etree.XMLSyntaxError as e:
            logger.error(f"Invalid XML in manifest {path}", exc_info=True)
        except (IOError, OSError) as e:
            logger.error(f"Cannot write manifest {path}", exc_info=True)
        except Exception as e:
            logger.error(f"Error applying translations to manifest: {e}", exc_info=True)
    
    def _apply_to_rise(self, path: Path, segments: List[Segment], translations: Dict[str, str]):
        """Aplicar traducciones a archivo Rise."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Encontrar y decodificar base64
            match = re.search(r'deserialize\("([A-Za-z0-9+/=]+)"\)', content)
            if not match:
                logger.debug(f"No Rise deserialize pattern found in {path}")
                return

            try:
                decoded = base64.b64decode(match.group(1)).decode('utf-8')
                data = json.loads(decoded)
            except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Invalid Rise JSON encoding in {path}", exc_info=True)
                return

            # Aplicar traducciones
            self._apply_to_json(data, "", segments, translations)

            # Re-encodificar y validar
            new_json = json.dumps(data, ensure_ascii=False)
            new_base64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')

            if not new_base64:
                logger.error(f"Base64 encoding failed for {path}")
                return

            # Reemplazar en contenido
            new_content = content[:match.start(1)] + new_base64 + content[match.end(1):]

            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        except (IOError, OSError) as e:
            logger.error(f"Cannot read/write Rise file {path}", exc_info=True)
        except Exception as e:
            logger.error(f"Error applying translations to Rise {path}: {e}", exc_info=True)
    
    def _apply_to_json(self, data: Any, path: str, segments: List[Segment], translations: Dict[str, str]):
        """Aplicar traducciones recursivamente a JSON."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                
                if isinstance(value, str):
                    seg_id = f"rise_{new_path.replace('.', '_')}"
                    if seg_id in translations:
                        data[key] = translations[seg_id]
                else:
                    self._apply_to_json(value, new_path, segments, translations)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._apply_to_json(item, f"{path}[{i}]", segments, translations)
    
    def _apply_to_html(self, path: Path, segments: List[Segment], translations: Dict[str, str]):
        """Aplicar traducciones a HTML estándar (primera ocurrencia por segmento)."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Aplicar cada segmento solo una vez (primera ocurrencia)
            for seg in segments:
                if seg.id in translations:
                    idx = content.find(seg.text)
                    if idx != -1:
                        content = content[:idx] + translations[seg.id] + content[idx + len(seg.text):]
                    else:
                        logger.warning(f"Segment text not found in HTML: {seg.id}")

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

        except (IOError, OSError) as e:
            logger.error(f"Cannot write HTML file: {path}", exc_info=True)
        except Exception as e:
            logger.error(f"Error applying translations to HTML {path}: {e}", exc_info=True)


# ============================================================================
# FUNCIONES CLI AUXILIARES
# ============================================================================

def _validate_args(args) -> tuple[Path, list[str], str, Path]:
    """Validar y procesar argumentos de línea de comandos.

    Returns:
        (zip_path, target_langs, source_lang, output_dir)
    """
    zip_path = Path(args.archivo)
    if not zip_path.exists():
        logger.error(f"File not found: {zip_path}")
        sys.exit(1)

    if not zip_path.suffix.lower() == '.zip':
        logger.error("File must be .zip format")
        sys.exit(1)

    target_langs = [lang.strip() for lang in args.idioma.split(',')]
    source_lang = args.origen
    output_dir = Path(args.salida)
    output_dir.mkdir(parents=True, exist_ok=True)

    return zip_path, target_langs, source_lang, output_dir


async def _run_translation(
    zip_path: Path,
    target_langs: list[str],
    source_lang: str,
    output_dir: Path,
    temp_dir: Path
) -> None:
    """Orquestar el proceso de traducción."""
    # 1. Parsear SCORM
    logger.info("Starting SCORM parsing", extra={"file": str(zip_path)})
    scorm_parser = ScormParser(temp_dir)
    package = scorm_parser.parse(zip_path)
    logger.info("SCORM parsed", extra={
        "version": package.version,
        "html_files": len(package.html_files),
        "title": package.title
    })

    # 2. Extraer contenido
    logger.info("Starting content extraction")
    extractor = ContentExtractor()
    extraction = extractor.extract(package)
    logger.info("Content extracted", extra={
        "segments": len(extraction.segments),
        "files": len(extraction.files)
    })

    if not extraction.segments:
        logger.warning("No translatable content found")
        return

    # 3. Traducir para cada idioma
    translator = Translator()
    rebuilder = ScormRebuilder()

    for target_lang in target_langs:
        logger.info("Starting translation", extra={
            "source": source_lang,
            "target": target_lang
        })
        translations = await translator.translate(
            extraction.segments,
            source_lang,
            target_lang
        )
        logger.info("Translation completed", extra={
            "target": target_lang,
            "segments": len(translations),
            "chars": translator.chars_translated
        })

        # 4. Reconstruir SCORM
        logger.info("Rebuilding SCORM package", extra={"lang": target_lang})
        output_path = rebuilder.rebuild(
            package, extraction, translations, output_dir, target_lang
        )
        logger.info("Package built", extra={
            "lang": target_lang,
            "output": str(output_path)
        })

    logger.info("Translation pipeline completed successfully", extra={
        "chars_total": translator.chars_translated,
        "langs": len(target_langs)
    })


# ============================================================================
# CLI PRINCIPAL
# ============================================================================

async def main():
    """CLI principal del Traductor SCORM."""
    parser = argparse.ArgumentParser(
        description='Traduce paquetes SCORM a múltiples idiomas.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python traductor.py curso.zip --idioma ca
  python traductor.py curso.zip --idioma en,fr,de
  python traductor.py curso.zip --idioma ca --salida ./traducciones/
        '''
    )

    parser.add_argument('archivo', help='Archivo SCORM (.zip) a traducir')
    parser.add_argument('--idioma', '-i', required=True,
                        help='Idioma(s) destino (ej: ca, en,fr,de)')
    parser.add_argument('--origen', '-o', default='es',
                        help='Idioma origen (default: es)')
    parser.add_argument('--salida', '-s', default='.',
                        help='Carpeta de salida (default: directorio actual)')

    args = parser.parse_args()
    zip_path, target_langs, source_lang, output_dir = _validate_args(args)

    logger.info("Starting SCORM Translator CLI", extra={
        "file": str(zip_path),
        "source_lang": source_lang,
        "target_langs": target_langs,
        "output_dir": str(output_dir)
    })

    # Crear directorio temporal
    temp_dir = Path(tempfile.mkdtemp())

    try:
        await _run_translation(zip_path, target_langs, source_lang, output_dir, temp_dir)
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Limpiar temporal
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    asyncio.run(main())
