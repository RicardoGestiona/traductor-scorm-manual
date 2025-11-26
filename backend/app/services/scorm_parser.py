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
    ScormObjective,
    ScormSequencingRules,
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
        # SCORM 1.2
        "imscp": "http://www.imsproject.org/xsd/imscp_rootv1p1p2",
        "imscp12": "http://www.imsglobal.org/xsd/imscp_v1p1",
        "adlcp": "http://www.adlnet.org/xsd/adlcp_rootv1p2",
        "imsmd": "http://www.imsglobal.org/xsd/imsmd_v1p2",
        # SCORM 2004
        "imsss": "http://www.imsglobal.org/xsd/imsss",  # Sequencing
        "adlseq": "http://www.adlnet.org/xsd/adlseq_v1p3",  # Sequencing ADL
        "adlnav": "http://www.adlnet.org/xsd/adlnav_v1p3",  # Navigation
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

        # SCORM 2004: Parsear sequencing y objectives
        objectives = self._parse_objectives(item_elem)
        sequencing = self._parse_sequencing(item_elem)
        completion_threshold = self._parse_completion_threshold(item_elem)

        return ScormItem(
            identifier=item_id,
            title=title,
            identifierref=identifierref,
            parameters=parameters,
            is_visible=is_visible,
            children=children,
            objectives=objectives,
            sequencing=sequencing,
            completion_threshold=completion_threshold,
        )

    def _parse_objectives(self, item_elem: etree._Element) -> List[ScormObjective]:
        """Parsear objetivos de SCORM 2004."""
        objectives = []

        # Buscar sequencing/objectives
        seq_elem = item_elem.find(".//sequencing", self.NAMESPACES)
        if seq_elem is None:
            seq_elem = item_elem.find(".//{*}sequencing")

        if seq_elem is None:
            return objectives

        # Buscar objectives container dentro de sequencing
        objectives_container = seq_elem.find(".//objectives", self.NAMESPACES)
        if objectives_container is None:
            objectives_container = seq_elem.find(".//{*}objectives")

        if objectives_container is None:
            return objectives

        # Buscar AMBOS primaryObjective y objective dentro del container
        # SCORM 2004 puede tener primaryObjective y múltiples objective secundarios
        obj_elements = []

        # Buscar primaryObjective
        primary_objs = objectives_container.findall(".//primaryObjective", self.NAMESPACES)
        if not primary_objs:
            primary_objs = objectives_container.findall(".//{*}primaryObjective")
        obj_elements.extend(primary_objs)

        # Buscar objective (secundarios)
        secondary_objs = objectives_container.findall(".//objective", self.NAMESPACES)
        if not secondary_objs:
            secondary_objs = objectives_container.findall(".//{*}objective")
        obj_elements.extend(secondary_objs)

        for obj_elem in obj_elements:
            obj_id = obj_elem.get("objectiveID", "")
            if not obj_id:
                continue

            # Parsear minNormalizedMeasure si existe
            min_score_elem = obj_elem.find(".//minNormalizedMeasure", self.NAMESPACES)
            if min_score_elem is None:
                min_score_elem = obj_elem.find(".//{*}minNormalizedMeasure")

            min_score = None
            if min_score_elem is not None and min_score_elem.text:
                try:
                    min_score = float(min_score_elem.text)
                except ValueError:
                    pass

            satisfied_by_measure = obj_elem.get("satisfiedByMeasure", "false").lower() == "true"

            objectives.append(
                ScormObjective(
                    identifier=obj_id,
                    satisfied_by_measure=satisfied_by_measure,
                    min_normalized_measure=min_score,
                )
            )

        return objectives

    def _parse_sequencing(self, item_elem: etree._Element) -> Optional[ScormSequencingRules]:
        """Parsear reglas de secuenciación de SCORM 2004."""
        seq_elem = item_elem.find(".//sequencing", self.NAMESPACES)
        if seq_elem is None:
            seq_elem = item_elem.find(".//{*}sequencing")

        if seq_elem is None:
            return None

        # Buscar controlMode
        control_elem = seq_elem.find(".//controlMode", self.NAMESPACES)
        if control_elem is None:
            control_elem = seq_elem.find(".//{*}controlMode")

        if control_elem is None:
            # Si hay sequencing pero no controlMode, retornar reglas default
            return ScormSequencingRules()

        # Extraer atributos de control mode
        choice = control_elem.get("choice", "true").lower() == "true"
        flow = control_elem.get("flow", "false").lower() == "true"
        forward_only = control_elem.get("forwardOnly", "false").lower() == "true"

        # Buscar constrainedChoice
        constrained = seq_elem.get("constrainedChoice", "false").lower() == "true"
        prevent_activation = seq_elem.get("preventActivation", "false").lower() == "true"

        return ScormSequencingRules(
            control_mode_choice=choice,
            control_mode_flow=flow,
            control_mode_forward_only=forward_only,
            prevent_activation=prevent_activation,
            constrained_choice=constrained,
        )

    def _parse_completion_threshold(self, item_elem: etree._Element) -> Optional[float]:
        """Parsear completion threshold de SCORM 2004."""
        # Buscar completionThreshold
        threshold_elem = item_elem.find(".//completionThreshold", self.NAMESPACES)
        if threshold_elem is None:
            threshold_elem = item_elem.find(".//{*}completionThreshold")

        if threshold_elem is None:
            return None

        # Extraer minProgressMeasure
        min_progress = threshold_elem.get("minProgressMeasure")
        if min_progress:
            try:
                return float(min_progress)
            except ValueError:
                pass

        return None

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
