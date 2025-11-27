"""
Tests para el servicio de reconstrucción de SCORM traducido.

Feature alignment: STORY-008 - Reconstrucción de SCORM Traducido
"""

import pytest
import tempfile
import shutil
import zipfile
from pathlib import Path
from lxml import etree

from app.services.scorm_rebuilder import ScormRebuilder, ScormRebuilderError
from app.models.scorm import (
    ScormPackage,
    ScormManifest,
    ScormMetadata,
    ExtractionResult,
    TranslatableContent,
    TranslatableSegment,
    ContentType,
)


class TestScormRebuilder:
    """Tests para ScormRebuilder."""

    @pytest.fixture
    def rebuilder(self):
        """Fixture: ScormRebuilder instance."""
        return ScormRebuilder()

    @pytest.fixture
    def temp_scorm_package(self):
        """Fixture: Paquete SCORM temporal de prueba."""
        temp_dir = tempfile.mkdtemp()
        scorm_dir = Path(temp_dir) / "scorm_package"
        scorm_dir.mkdir()

        # Crear imsmanifest.xml
        manifest_content = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="TEST_SCORM" version="1.0">
    <metadata>
        <lom>
            <general>
                <title>
                    <langstring>Original Course Title</langstring>
                </title>
                <description>
                    <langstring>Original course description</langstring>
                </description>
            </general>
        </lom>
    </metadata>
    <organizations default="ORG-001">
        <organization identifier="ORG-001">
            <title>Original Organization</title>
            <item identifier="ITEM-001">
                <title>Original Item Title</title>
            </item>
        </organization>
    </organizations>
    <resources>
        <resource identifier="RES-001" type="webcontent" href="lesson.html">
            <file href="lesson.html"/>
        </resource>
    </resources>
</manifest>"""

        manifest_path = scorm_dir / "imsmanifest.xml"
        manifest_path.write_text(manifest_content, encoding="utf-8")

        # Crear archivo HTML
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Lesson Title</title>
</head>
<body>
    <h1>Welcome to the course</h1>
    <p>This is a sample paragraph.</p>
    <img src="image.jpg" alt="Sample image" title="Image tooltip">
    <button>Click here</button>
</body>
</html>"""

        html_path = scorm_dir / "lesson.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Crear estructura de ScormPackage
        package = ScormPackage(
            filename="test_scorm.zip",
            size_bytes=1024,
            extracted_path=str(scorm_dir),
            manifest=ScormManifest(
                identifier="TEST_SCORM",
                version="1.2",
                metadata=ScormMetadata(
                    title="Original Course Title",
                    description="Original course description",
                ),
                organizations=[],
                resources=[],
            ),
            html_files=["lesson.html"],
        )

        yield package

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_extraction_result(self):
        """Fixture: ExtractionResult de ejemplo."""
        result = ExtractionResult(scorm_package="test_scorm.zip")

        # Contenido del manifest
        manifest_content = TranslatableContent(
            file_path="imsmanifest.xml", content_type=ContentType.XML
        )
        manifest_content.add_segment(
            TranslatableSegment(
                segment_id="manifest_title",
                content_type=ContentType.XML,
                original_text="Original Course Title",
                context="Course title",
                xpath="//title/langstring",
            )
        )
        manifest_content.add_segment(
            TranslatableSegment(
                segment_id="org_title",
                content_type=ContentType.XML,
                original_text="Original Organization",
                context="Organization title",
                xpath="//organization[@identifier='ORG-001']/title",
            )
        )

        result.add_file_content(manifest_content)

        # Contenido del HTML
        html_content = TranslatableContent(
            file_path="lesson.html", content_type=ContentType.HTML
        )
        html_content.add_segment(
            TranslatableSegment(
                segment_id="html_h1_1",
                content_type=ContentType.HTML,
                original_text="Welcome to the course",
                context="h1 element",
            )
        )
        html_content.add_segment(
            TranslatableSegment(
                segment_id="html_p_1",
                content_type=ContentType.HTML,
                original_text="This is a sample paragraph.",
                context="p element",
            )
        )
        html_content.add_segment(
            TranslatableSegment(
                segment_id="html_attr_alt_1",
                content_type=ContentType.ATTRIBUTE,
                original_text="Sample image",
                context="alt attribute",
                attribute_name="alt",
            )
        )
        html_content.add_segment(
            TranslatableSegment(
                segment_id="html_button_1",
                content_type=ContentType.HTML,
                original_text="Click here",
                context="button element",
            )
        )

        result.add_file_content(html_content)

        return result

    @pytest.fixture
    def sample_translations(self):
        """Fixture: Traducciones de ejemplo (EN -> ES)."""
        return {
            "manifest_title": "Título del Curso Original",
            "org_title": "Organización Original",
            "html_h1_1": "Bienvenido al curso",
            "html_p_1": "Este es un párrafo de ejemplo.",
            "html_attr_alt_1": "Imagen de ejemplo",
            "html_button_1": "Haz clic aquí",
        }

    def test_init_rebuilder(self, rebuilder):
        """Test: Inicializar rebuilder."""
        assert rebuilder.files_processed == 0
        assert rebuilder.segments_applied == 0

    def test_rebuild_scorm_success(
        self,
        rebuilder,
        temp_scorm_package,
        sample_extraction_result,
        sample_translations,
    ):
        """Test: Reconstruir SCORM con traducciones exitosamente."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            # Reconstruir SCORM
            zip_path = rebuilder.rebuild_scorm(
                original_package=temp_scorm_package,
                extraction_result=sample_extraction_result,
                translations=sample_translations,
                output_dir=output_dir,
                target_language="es",
            )

            # Verificar que se creó el ZIP
            assert zip_path.exists()
            assert zip_path.suffix == ".zip"
            assert "es" in zip_path.name
            assert zip_path.stat().st_size > 0

            # Verificar estadísticas
            stats = rebuilder.get_stats()
            assert stats["files_processed"] == 2  # manifest + html
            assert stats["segments_applied"] > 0

        finally:
            shutil.rmtree(output_dir)

    def test_apply_translations_to_xml(
        self,
        rebuilder,
        temp_scorm_package,
        sample_extraction_result,
        sample_translations,
    ):
        """Test: Aplicar traducciones a manifest XML."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            zip_path = rebuilder.rebuild_scorm(
                original_package=temp_scorm_package,
                extraction_result=sample_extraction_result,
                translations=sample_translations,
                output_dir=output_dir,
                target_language="es",
            )

            # Extraer ZIP y verificar manifest
            extract_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            manifest_path = extract_dir / "imsmanifest.xml"
            tree = etree.parse(str(manifest_path))
            root = tree.getroot()

            # Verificar que se aplicaron las traducciones
            title_elements = root.xpath("//title/langstring")
            if title_elements:
                # Debería contener "Título del Curso Original"
                assert "Título del Curso" in title_elements[0].text

            shutil.rmtree(extract_dir)

        finally:
            shutil.rmtree(output_dir)

    def test_apply_translations_to_html_text(
        self,
        rebuilder,
        temp_scorm_package,
        sample_extraction_result,
        sample_translations,
    ):
        """Test: Aplicar traducciones a texto HTML."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            zip_path = rebuilder.rebuild_scorm(
                original_package=temp_scorm_package,
                extraction_result=sample_extraction_result,
                translations=sample_translations,
                output_dir=output_dir,
                target_language="es",
            )

            # Extraer y verificar HTML
            extract_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            html_path = extract_dir / "lesson.html"
            html_content = html_path.read_text(encoding="utf-8")

            # Verificar traducciones
            assert "Bienvenido al curso" in html_content
            assert "Este es un párrafo de ejemplo" in html_content
            assert "Haz clic aquí" in html_content

            # Verificar que NO está el texto original
            assert "Welcome to the course" not in html_content

            shutil.rmtree(extract_dir)

        finally:
            shutil.rmtree(output_dir)

    def test_apply_translations_to_html_attributes(
        self,
        rebuilder,
        temp_scorm_package,
        sample_extraction_result,
        sample_translations,
    ):
        """Test: Aplicar traducciones a atributos HTML."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            zip_path = rebuilder.rebuild_scorm(
                original_package=temp_scorm_package,
                extraction_result=sample_extraction_result,
                translations=sample_translations,
                output_dir=output_dir,
                target_language="es",
            )

            # Extraer y verificar HTML
            extract_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            html_path = extract_dir / "lesson.html"
            html_content = html_path.read_text(encoding="utf-8")

            # Verificar que se tradujo el atributo alt
            assert 'alt="Imagen de ejemplo"' in html_content

            shutil.rmtree(extract_dir)

        finally:
            shutil.rmtree(output_dir)

    def test_zip_structure_preserved(
        self,
        rebuilder,
        temp_scorm_package,
        sample_extraction_result,
        sample_translations,
    ):
        """Test: Estructura de carpetas preservada en ZIP."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            zip_path = rebuilder.rebuild_scorm(
                original_package=temp_scorm_package,
                extraction_result=sample_extraction_result,
                translations=sample_translations,
                output_dir=output_dir,
                target_language="es",
            )

            # Verificar contenido del ZIP
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()

                # Verificar archivos esperados
                assert "imsmanifest.xml" in namelist
                assert "lesson.html" in namelist

        finally:
            shutil.rmtree(output_dir)

    def test_generate_output_filename(self, rebuilder):
        """Test: Generar nombre de archivo de salida."""
        filename = rebuilder._generate_output_filename("curso.zip", "es")
        assert filename == "curso_es.zip"

        filename = rebuilder._generate_output_filename("my_scorm_package.zip", "fr")
        assert filename == "my_scorm_package_fr.zip"

    def test_get_stats(self, rebuilder):
        """Test: Obtener estadísticas."""
        rebuilder.files_processed = 5
        rebuilder.segments_applied = 20

        stats = rebuilder.get_stats()

        assert stats["files_processed"] == 5
        assert stats["segments_applied"] == 20

    def test_partial_translations(
        self,
        rebuilder,
        temp_scorm_package,
        sample_extraction_result,
    ):
        """Test: Reconstruir con solo algunas traducciones disponibles."""
        # Solo traducir algunos segmentos
        partial_translations = {
            "html_h1_1": "Bienvenido al curso",
            # No traducir los demás
        }

        output_dir = Path(tempfile.mkdtemp())

        try:
            zip_path = rebuilder.rebuild_scorm(
                original_package=temp_scorm_package,
                extraction_result=sample_extraction_result,
                translations=partial_translations,
                output_dir=output_dir,
                target_language="es",
            )

            # Debe completarse sin error
            assert zip_path.exists()

            # Verificar que se aplicó la traducción disponible
            extract_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            html_path = extract_dir / "lesson.html"
            html_content = html_path.read_text(encoding="utf-8")

            # Verificar traducción aplicada
            assert "Bienvenido al curso" in html_content
            # Verificar que texto sin traducir se mantiene
            assert "This is a sample paragraph" in html_content

            shutil.rmtree(extract_dir)

        finally:
            shutil.rmtree(output_dir)

    def test_empty_translations(
        self,
        rebuilder,
        temp_scorm_package,
        sample_extraction_result,
    ):
        """Test: Reconstruir sin traducciones (copia del original)."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            zip_path = rebuilder.rebuild_scorm(
                original_package=temp_scorm_package,
                extraction_result=sample_extraction_result,
                translations={},  # Sin traducciones
                output_dir=output_dir,
                target_language="es",
            )

            # Debe completarse sin error
            assert zip_path.exists()

            # Verificar que el contenido es el original
            extract_dir = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            html_path = extract_dir / "lesson.html"
            html_content = html_path.read_text(encoding="utf-8")

            # Verificar textos originales
            assert "Welcome to the course" in html_content
            assert "This is a sample paragraph" in html_content

            shutil.rmtree(extract_dir)

        finally:
            shutil.rmtree(output_dir)
