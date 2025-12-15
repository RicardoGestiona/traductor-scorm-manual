"""
Utilidad para normalizar nombres de archivo con caracteres especiales.

Reemplaza tildes y caracteres especiales por sus equivalentes ASCII
para garantizar compatibilidad en todos los sistemas y navegadores.

Filepath: backend/app/services/filename_normalizer.py
"""

import unicodedata
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import shutil

logger = logging.getLogger(__name__)

# Mapeo de caracteres especiales a ASCII
CHAR_MAP = {
    # Vocales con tilde (minúsculas)
    'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ã': 'a',
    'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
    'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
    'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'õ': 'o',
    'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u',
    # Vocales con tilde (mayúsculas)
    'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ã': 'A',
    'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E',
    'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I',
    'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Õ': 'O',
    'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U',
    # Otros caracteres especiales
    'ñ': 'n', 'Ñ': 'N',
    'ç': 'c', 'Ç': 'C',
    'ß': 'ss',
    # Caracteres catalanes/gallegos/portugueses
    'ï': 'i', 'Ï': 'I',  # diéresis catalana
    'ü': 'u', 'Ü': 'U',
    # Espacios y caracteres problemáticos en URLs
    ' ': '_',
    '(': '',
    ')': '',
    '[': '',
    ']': '',
    '{': '',
    '}': '',
    "'": '',
    '"': '',
    '`': '',
    '´': '',
    '¨': '',
}


def normalize_filename(filename: str) -> str:
    """
    Normalizar un nombre de archivo reemplazando caracteres especiales.

    Args:
        filename: Nombre de archivo original

    Returns:
        Nombre de archivo normalizado (ASCII-safe)
    """
    # Separar nombre y extensión
    path = Path(filename)
    name = path.stem
    ext = path.suffix

    # Si hay subdirectorios, procesar cada parte
    parts = Path(filename).parts
    if len(parts) > 1:
        normalized_parts = [normalize_single_name(part) for part in parts[:-1]]
        normalized_parts.append(normalize_single_name(path.stem) + ext)
        return str(Path(*normalized_parts))

    # Normalizar solo el nombre (mantener extensión)
    normalized_name = normalize_single_name(name)

    return normalized_name + ext


def normalize_single_name(name: str) -> str:
    """
    Normalizar un solo nombre (sin extensión ni path).

    Args:
        name: Nombre a normalizar

    Returns:
        Nombre normalizado
    """
    result = []

    for char in name:
        if char in CHAR_MAP:
            result.append(CHAR_MAP[char])
        elif char.isascii() and (char.isalnum() or char in '._-'):
            result.append(char)
        else:
            # Intentar descomponer Unicode y tomar solo la base
            normalized = unicodedata.normalize('NFD', char)
            base_char = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
            if base_char.isascii() and base_char.isalnum():
                result.append(base_char)
            elif base_char:
                result.append('_')

    # Limpiar múltiples guiones bajos consecutivos
    normalized = ''.join(result)
    normalized = re.sub(r'_+', '_', normalized)
    normalized = normalized.strip('_')

    return normalized if normalized else 'file'


def normalize_files_in_directory(directory: Path) -> Dict[str, str]:
    """
    Normalizar todos los nombres de archivo en un directorio.

    Args:
        directory: Path al directorio

    Returns:
        Dict mapping de rutas originales a rutas normalizadas
    """
    rename_map: Dict[str, str] = {}
    files_to_rename: List[Tuple[Path, Path]] = []

    # Primero, identificar todos los archivos que necesitan renombrado
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            normalized_rel_path = normalize_path(str(rel_path))

            if str(rel_path) != normalized_rel_path:
                original_str = str(rel_path)
                rename_map[original_str] = normalized_rel_path

                new_path = directory / normalized_rel_path
                files_to_rename.append((file_path, new_path))

                logger.debug(f"File to rename: {original_str} -> {normalized_rel_path}")

    # También verificar directorios que necesitan renombrado
    dirs_to_rename: List[Tuple[Path, Path]] = []
    for dir_path in sorted(directory.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if dir_path.is_dir():
            rel_path = dir_path.relative_to(directory)
            normalized_rel_path = normalize_path(str(rel_path))

            if str(rel_path) != normalized_rel_path:
                new_path = directory / normalized_rel_path
                dirs_to_rename.append((dir_path, new_path))

    # Renombrar archivos
    for old_path, new_path in files_to_rename:
        try:
            # Crear directorio padre si no existe
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Mover archivo
            shutil.move(str(old_path), str(new_path))
            logger.info(f"Renamed: {old_path.name} -> {new_path.name}")
        except Exception as e:
            logger.error(f"Error renaming {old_path}: {e}")

    # Renombrar directorios (de más profundo a menos profundo)
    for old_path, new_path in dirs_to_rename:
        try:
            if old_path.exists() and not new_path.exists():
                old_path.rename(new_path)
                logger.info(f"Renamed directory: {old_path.name} -> {new_path.name}")
        except Exception as e:
            logger.error(f"Error renaming directory {old_path}: {e}")

    # Limpiar directorios vacíos
    for dir_path in sorted(directory.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            try:
                dir_path.rmdir()
            except Exception:
                pass

    return rename_map


def normalize_path(path: str) -> str:
    """
    Normalizar una ruta completa (con directorios).

    Args:
        path: Ruta a normalizar

    Returns:
        Ruta normalizada
    """
    parts = Path(path).parts
    normalized_parts = []

    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            # Último elemento: es un archivo, normalizar con extensión
            normalized_parts.append(normalize_filename(part))
        else:
            # Es un directorio
            normalized_parts.append(normalize_single_name(part))

    return str(Path(*normalized_parts)) if normalized_parts else path


def update_references_in_html(html_content: str, rename_map: Dict[str, str]) -> str:
    """
    Actualizar referencias a archivos en contenido HTML.

    Args:
        html_content: Contenido HTML
        rename_map: Mapeo de rutas originales a normalizadas

    Returns:
        HTML con referencias actualizadas
    """
    updated_content = html_content

    for original, normalized in rename_map.items():
        # Reemplazar en atributos src, href, data-src, poster, etc.
        # Escapar caracteres especiales en el original para regex
        escaped_original = re.escape(original)

        # Patrones comunes de referencia a archivos
        patterns = [
            # src="path" o src='path'
            (rf'(src\s*=\s*["\'])({escaped_original})(["\'])', rf'\1{normalized}\3'),
            # href="path" o href='path'
            (rf'(href\s*=\s*["\'])({escaped_original})(["\'])', rf'\1{normalized}\3'),
            # data-src="path"
            (rf'(data-src\s*=\s*["\'])({escaped_original})(["\'])', rf'\1{normalized}\3'),
            # poster="path"
            (rf'(poster\s*=\s*["\'])({escaped_original})(["\'])', rf'\1{normalized}\3'),
            # background="path"
            (rf'(background\s*=\s*["\'])({escaped_original})(["\'])', rf'\1{normalized}\3'),
            # url("path") en CSS inline
            (rf'(url\s*\(\s*["\']?)({escaped_original})(["\']?\s*\))', rf'\1{normalized}\3'),
        ]

        for pattern, replacement in patterns:
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.IGNORECASE)

    return updated_content


def update_references_in_xml(xml_content: str, rename_map: Dict[str, str]) -> str:
    """
    Actualizar referencias a archivos en contenido XML (imsmanifest.xml).

    Args:
        xml_content: Contenido XML
        rename_map: Mapeo de rutas originales a normalizadas

    Returns:
        XML con referencias actualizadas
    """
    updated_content = xml_content

    for original, normalized in rename_map.items():
        escaped_original = re.escape(original)

        # Patrones para XML (atributos href en <file> y <resource>)
        patterns = [
            # href="path"
            (rf'(href\s*=\s*["\'])({escaped_original})(["\'])', rf'\1{normalized}\3'),
            # xml:base="path"
            (rf'(xml:base\s*=\s*["\'])({escaped_original})(["\'])', rf'\1{normalized}\3'),
        ]

        for pattern, replacement in patterns:
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.IGNORECASE)

    return updated_content


def update_references_in_css(css_content: str, rename_map: Dict[str, str]) -> str:
    """
    Actualizar referencias a archivos en contenido CSS.

    Args:
        css_content: Contenido CSS
        rename_map: Mapeo de rutas originales a normalizadas

    Returns:
        CSS con referencias actualizadas
    """
    updated_content = css_content

    for original, normalized in rename_map.items():
        escaped_original = re.escape(original)

        # url("path") o url('path') o url(path)
        patterns = [
            (rf'(url\s*\(\s*["\']?)({escaped_original})(["\']?\s*\))', rf'\1{normalized}\3'),
        ]

        for pattern, replacement in patterns:
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.IGNORECASE)

    return updated_content
