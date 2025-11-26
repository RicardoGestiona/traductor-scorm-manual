"""
Servicio para parsear paquetes SCORM.

Soporta SCORM 1.2, 2004 y xAPI/TinCan.

Filepath: backend/app/services/scorm_parser.py
Feature alignment: STORY-005 - Parser de SCORM 1.2
"""

import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
from lxml import etree
import logging

from app.models.scorm import (
    ScormPackage,
    ScormManifest,
    ScormMetadata,
    ScormOrganization,
    ScormItem,
    ScormResource,
    ScormValidationResult,
)

logger = logging.getLogger(__name__)


class ScormParserError(Exception):
    """Error durante el parsing de SCORM."""

    pass


class ScormParser:
    """
    Parser para paquetes SCORM.

    Capabilities:
    - Extraer y validar archivos ZIP de SCORM
    - Parsear imsmanifest.xml
    - Detectar versión de SCORM (1.2, 2004, xAPI)
    - Extraer metadata, organizaciones y recursos
    - Identificar archivos HTML traducibles
    """

    # Namespaces comunes de SCORM
    NAMESPACES = {
        "imscp": "http://www.imsproject.org/xsd/imscp_rootv1p1p2",
        "imscp12": "http://www.imsglobal.org/xsd/imscp_v1p1",
        "adlcp": "http://www.adlnet.org/xsd/adlcp_rootv1p2",
        "imsmd": "http://www.imsglobal.org/xsd/imsmd_v1p2",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Inicializar el parser.

        Args:
            temp_dir: Directorio temporal para extraer archivos (opcional)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def validate_scorm_zip(self, zip_path: str) -> ScormValidationResult:
        """
        Validar que un ZIP contiene una estructura SCORM válida.

        Args:
            zip_path: Path al archivo ZIP

        Returns:
            ScormValidationResult con detalles de la validación
        """
        result = ScormValidationResult(is_valid=False)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                file_list = zf.namelist()

                # Verificar que existe imsmanifest.xml
                if "imsmanifest.xml" not in file_list:
                    result.errors.append("No se encontró imsmanifest.xml en la raíz del ZIP")
                    return result

                result.manifest_found = True

                # Extraer y parsear manifest para detectar versión
                manifest_content = zf.read("imsmanifest.xml")
                try:
                    tree = etree.fromstring(manifest_content)
                    version = self._detect_scorm_version(tree)
                    result.version = version

                    # Contar recursos
                    resources = tree.find(".//resources", self.NAMESPACES)
                    if resources is not None:
                        result.resources_found = len(resources.findall("resource", self.NAMESPACES))

                    result.is_valid = True

                except etree.XMLSyntaxError as e:
                    result.errors.append(f"XML malformado: {str(e)}")

        except zipfile.BadZipFile:
            result.errors.append("El archivo no es un ZIP válido")
        except Exception as e:
            result.errors.append(f"Error inesperado: {str(e)}")

        return result

    def parse_scorm_package(self, zip_path: str) -> ScormPackage:
        """
        Parsear un paquete SCORM completo.

        Args:
            zip_path: Path al archivo ZIP de SCORM

        Returns:
            ScormPackage con toda la información parseada

        Raises:
            ScormParserError: Si hay error en el parsing
        """
        # Validar primero
        validation = self.validate_scorm_zip(zip_path)
        if not validation.is_valid:
            raise ScormParserError(f"SCORM inválido: {', '.join(validation.errors)}")

        # Crear directorio temporal para extraer
        extract_path = Path(self.temp_dir) / f"scorm_{Path(zip_path).stem}"
        extract_path.mkdir(parents=True, exist_ok=True)

        try:
            # Extraer ZIP
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_path)

            # Parsear manifest
            manifest_path = extract_path / "imsmanifest.xml"
            manifest = self._parse_manifest(manifest_path)

            # Identificar archivos HTML
            html_files = self._find_html_files(extract_path)

            # Detectar idioma
            detected_language = self._detect_language(manifest)

            # Crear ScormPackage
            package = ScormPackage(
                filename=Path(zip_path).name,
                size_bytes=Path(zip_path).stat().st_size,
                extracted_path=str(extract_path),
                manifest=manifest,
                detected_language=detected_language,
                html_files=html_files,
            )

            return package

        except Exception as e:
            # Limpiar en caso de error
            if extract_path.exists():
                shutil.rmtree(extract_path)
            raise ScormParserError(f"Error parseando SCORM: {str(e)}")

    def _parse_manifest(self, manifest_path: Path) -> ScormManifest:
        """Parsear imsmanifest.xml."""
        tree = etree.parse(str(manifest_path))
        root = tree.getroot()

        # Extraer información básica
        manifest_id = root.get("identifier", "unknown")
        version = self._detect_scorm_version(root)

        # Parsear metadata
        metadata = self._parse_metadata(root)

        # Parsear organizaciones
        organizations = self._parse_organizations(root)

        # Parsear recursos
        resources = self._parse_resources(root)

        # Default organization
        orgs_element = root.find("organizations", self.NAMESPACES)
        default_org = orgs_element.get("default") if orgs_element is not None else None

        manifest = ScormManifest(
            identifier=manifest_id,
            version=version,
            metadata=metadata,
            organizations=organizations,
            resources=resources,
            default_organization=default_org,
            schema_version=root.get("schemaversion"),
            xml_namespace=root.nsmap.get(None) if hasattr(root, "nsmap") else None,
        )

        return manifest

    def _detect_scorm_version(self, root: etree._Element) -> str:
        """Detectar versión de SCORM desde el manifest."""
        schema_version = root.get("schemaversion", "").lower()

        if "1.2" in schema_version or "1.1" in schema_version:
            return "1.2"
        elif "2004" in schema_version or "1.3" in schema_version:
            return "2004"

        # Verificar namespace
        namespace = root.nsmap.get(None) if hasattr(root, "nsmap") else None
        if namespace and "tincan" in namespace.lower():
            return "xapi"

        # Default a 1.2
        return "1.2"

    def _parse_metadata(self, root: etree._Element) -> ScormMetadata:
        """Parsear sección de metadata."""
        metadata_elem = root.find("metadata", self.NAMESPACES)

        if metadata_elem is None:
            return ScormMetadata()

        # Intentar extraer title y description
        title = None
        description = None
        language = None

        # Buscar en metadata/lom o metadata directamente
        title_elem = metadata_elem.find(".//title/langstring", self.NAMESPACES)
        if title_elem is not None:
            title = title_elem.text

        desc_elem = metadata_elem.find(".//description/langstring", self.NAMESPACES)
        if desc_elem is not None:
            description = desc_elem.text

        lang_elem = metadata_elem.find(".//language", self.NAMESPACES)
        if lang_elem is not None:
            language = lang_elem.text

        return ScormMetadata(title=title, description=description, language=language)

    def _parse_organizations(self, root: etree._Element) -> List[ScormOrganization]:
        """Parsear organizaciones del manifest."""
        organizations = []

        # Buscar organizations (con o sin namespace)
        orgs_element = root.find("organizations", self.NAMESPACES)
        if orgs_element is None:
            # Intentar sin namespace
            orgs_element = root.find(".//{*}organizations")

        if orgs_element is None:
            return organizations

        # Buscar organization elements (con o sin namespace)
        org_elements = orgs_element.findall("organization", self.NAMESPACES)
        if not org_elements:
            org_elements = orgs_element.findall(".//{*}organization")

        for org in org_elements:
            org_id = org.get("identifier", "")

            # Buscar title
            title_elem = org.find("title", self.NAMESPACES)
            if title_elem is None:
                title_elem = org.find(".//{*}title")
            org_title = title_elem.text if title_elem is not None else ""

            # Parsear items recursivamente
            items = []
            item_elements = org.findall("item", self.NAMESPACES)
            if not item_elements:
                item_elements = org.findall(".//{*}item")
                # Filtrar solo items directos (no nietos)
                item_elements = [item for item in item_elements if item.getparent() == org]

            for item_elem in item_elements:
                items.append(self._parse_item(item_elem))

            organizations.append(
                ScormOrganization(
                    identifier=org_id,
                    title=org_title,
                    structure=org.get("structure"),
                    items=items,
                )
            )

        return organizations

    def _parse_item(self, item_elem: etree._Element) -> ScormItem:
        """Parsear un item (recursivo para items anidados)."""
        item_id = item_elem.get("identifier", "")

        # Buscar title
        title_elem = item_elem.find("title", self.NAMESPACES)
        if title_elem is None:
            title_elem = item_elem.find(".//{*}title")
        title = title_elem.text if title_elem is not None else ""

        identifierref = item_elem.get("identifierref")
        parameters = item_elem.get("parameters")
        is_visible = item_elem.get("isvisible", "true").lower() == "true"

        # Parsear items hijos
        children = []
        child_elements = item_elem.findall("item", self.NAMESPACES)
        if not child_elements:
            child_elements = item_elem.findall(".//{*}item")
            # Filtrar solo hijos directos
            child_elements = [child for child in child_elements if child.getparent() == item_elem]

        for child_elem in child_elements:
            children.append(self._parse_item(child_elem))

        return ScormItem(
            identifier=item_id,
            title=title,
            identifierref=identifierref,
            parameters=parameters,
            is_visible=is_visible,
            children=children,
        )

    def _parse_resources(self, root: etree._Element) -> List[ScormResource]:
        """Parsear recursos del manifest."""
        resources = []

        # Buscar resources (con o sin namespace)
        resources_elem = root.find("resources", self.NAMESPACES)
        if resources_elem is None:
            resources_elem = root.find(".//{*}resources")

        if resources_elem is None:
            return resources

        # Buscar resource elements
        res_elements = resources_elem.findall("resource", self.NAMESPACES)
        if not res_elements:
            res_elements = resources_elem.findall(".//{*}resource")
            # Filtrar solo recursos directos
            res_elements = [res for res in res_elements if res.getparent() == resources_elem]

        for res in res_elements:
            res_id = res.get("identifier", "")
            res_type = res.get("type", "webcontent")
            href = res.get("href")

            # Extraer archivos
            files = []
            file_elements = res.findall("file", self.NAMESPACES)
            if not file_elements:
                file_elements = res.findall(".//{*}file")
                # Filtrar solo files directos
                file_elements = [f for f in file_elements if f.getparent() == res]

            for file_elem in file_elements:
                file_href = file_elem.get("href")
                if file_href:
                    files.append(file_href)

            resources.append(
                ScormResource(identifier=res_id, type=res_type, href=href, files=files)
            )

        return resources

    def _find_html_files(self, extract_path: Path) -> List[str]:
        """Encontrar todos los archivos HTML en el paquete."""
        html_files = []
        for file_path in extract_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".html", ".htm"]:
                # Path relativo al directorio extraído
                rel_path = file_path.relative_to(extract_path)
                html_files.append(str(rel_path))

        return html_files

    def _detect_language(self, manifest: ScormManifest) -> Optional[str]:
        """Detectar idioma del paquete desde metadata."""
        if manifest.metadata.language:
            return manifest.metadata.language

        # TODO: Analizar contenido HTML para detectar idioma
        return None

    def cleanup(self, extract_path: str) -> None:
        """
        Limpiar archivos temporales extraídos.

        Args:
            extract_path: Path del directorio a eliminar
        """
        path = Path(extract_path)
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            logger.info(f"Limpiados archivos temporales: {extract_path}")
