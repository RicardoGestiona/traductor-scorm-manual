"""
Tests para el servicio de extracción de contenido traducible.

Feature alignment: STORY-006 - Extracción de Contenido Traducible
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from app.services.content_extractor import ContentExtractor
from app.models.scorm import (
    ScormManifest,
    ScormMetadata,
    ScormOrganization,
    ScormItem,
    ContentType,
)


class TestContentExtractor:
    """Tests para ContentExtractor."""

    @pytest.fixture
    def extractor(self):
        """Fixture: ContentExtractor instance."""
        return ContentExtractor()

    @pytest.fixture
    def sample_manifest(self):
        """Fixture: Manifest de ejemplo."""
        return ScormManifest(
            identifier="SCORM_TEST",
            version="1.2",
            metadata=ScormMetadata(
                title="Curso de Ejemplo",
                description="Este es un curso de prueba para testear extracción",
            ),
            organizations=[
                ScormOrganization(
                    identifier="ORG-001",
                    title="Organización Principal",
                    items=[
                        ScormItem(
                            identifier="ITEM-001",
                            title="Módulo 1: Introducción",
                            children=[
                                ScormItem(
                                    identifier="ITEM-001-1",
                                    title="Lección 1.1: Conceptos Básicos",
                                ),
                                ScormItem(
                                    identifier="ITEM-001-2",
                                    title="Lección 1.2: Práctica",
                                ),
                            ],
                        ),
                        ScormItem(
                            identifier="ITEM-002",
                            title="Módulo 2: Avanzado",
                        ),
                    ],
                )
            ],
            resources=[],
        )

    @pytest.fixture
    def temp_html_file(self):
        """Fixture: Archivo HTML temporal de prueba."""
        temp_dir = tempfile.mkdtemp()
        html_path = Path(temp_dir) / "lesson.html"

        html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <title>Lección de Prueba</title>
    <script>
        // Este código NO debe traducirse
        console.log("Hello world");
    </script>
    <style>
        /* Este CSS NO debe traducirse */
        .test { color: red; }
    </style>
</head>
<body>
    <h1>Título Principal</h1>
    <p>Este es un párrafo de ejemplo que debe traducirse.</p>
    <p>Otro párrafo con <strong>texto en negrita</strong> incluido.</p>

    <div>
        <span>Texto en span</span>
    </div>

    <ul>
        <li>Item de lista 1</li>
        <li>Item de lista 2</li>
    </ul>

    <img src="image.jpg" alt="Descripción de la imagen" title="Tooltip de la imagen">

    <input type="text" placeholder="Escribe aquí">

    <button aria-label="Botón de acción">Hacer clic</button>

    <!-- Elementos que NO deben traducirse -->
    <code>var x = 10;</code>
    <pre>function test() { return true; }</pre>
</body>
</html>"""

        html_path.write_text(html_content, encoding="utf-8")

        yield html_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_extract_from_manifest(self, extractor, sample_manifest):
        """Test: Extraer contenido del manifest."""
        content = extractor.extract_from_manifest(sample_manifest)

        assert content.file_path == "imsmanifest.xml"
        assert content.content_type == ContentType.XML
        assert len(content.segments) > 0

        # Verificar que se extrajo el título del curso
        titles = [seg.original_text for seg in content.segments]
        assert "Curso de Ejemplo" in titles
        assert "Este es un curso de prueba para testear extracción" in titles

        # Verificar que se extrajeron títulos de organizaciones
        assert "Organización Principal" in titles

        # Verificar que se extrajeron títulos de items
        assert "Módulo 1: Introducción" in titles
        assert "Lección 1.1: Conceptos Básicos" in titles
        assert "Lección 1.2: Práctica" in titles
        assert "Módulo 2: Avanzado" in titles

    def test_extract_manifest_context(self, extractor, sample_manifest):
        """Test: Verificar que se captura contexto correcto en manifest."""
        content = extractor.extract_from_manifest(sample_manifest)

        # Buscar segmento del título del curso
        title_segment = next(
            (seg for seg in content.segments if seg.original_text == "Curso de Ejemplo"),
            None,
        )
        assert title_segment is not None
        assert "metadata" in title_segment.context.lower()
        assert title_segment.content_type == ContentType.XML

        # Buscar segmento de un item
        item_segment = next(
            (
                seg
                for seg in content.segments
                if seg.original_text == "Módulo 1: Introducción"
            ),
            None,
        )
        assert item_segment is not None
        assert "ITEM-001" in item_segment.segment_id

    def test_extract_from_html_file(self, extractor, temp_html_file):
        """Test: Extraer contenido de archivo HTML."""
        content = extractor.extract_from_html_file(
            temp_html_file, "content/lesson.html"
        )

        assert content.file_path == "content/lesson.html"
        assert content.content_type == ContentType.HTML
        assert len(content.segments) > 0

        # Obtener todos los textos extraídos
        texts = [seg.original_text for seg in content.segments]

        # Verificar que se extrajeron textos visibles
        assert "Título Principal" in texts
        assert "Este es un párrafo de ejemplo que debe traducirse." in texts
        assert "Item de lista 1" in texts
        assert "Item de lista 2" in texts

    def test_html_no_extract_script_style(self, extractor, temp_html_file):
        """Test: NO extraer contenido de script, style, code, pre."""
        content = extractor.extract_from_html_file(
            temp_html_file, "content/lesson.html"
        )

        texts = [seg.original_text for seg in content.segments]

        # Verificar que NO se extrajeron estos contenidos
        assert "Hello world" not in texts
        assert "console.log" not in texts
        assert "color: red" not in texts
        assert "var x = 10;" not in texts
        assert "function test()" not in texts

    def test_html_extract_attributes(self, extractor, temp_html_file):
        """Test: Extraer atributos traducibles (alt, title, placeholder)."""
        content = extractor.extract_from_html_file(
            temp_html_file, "content/lesson.html"
        )

        # Filtrar solo segmentos de atributos
        attribute_segments = [
            seg for seg in content.segments if seg.content_type == ContentType.ATTRIBUTE
        ]

        assert len(attribute_segments) > 0

        # Verificar que se extrajeron atributos
        attr_texts = [seg.original_text for seg in attribute_segments]
        assert "Descripción de la imagen" in attr_texts  # alt
        assert "Tooltip de la imagen" in attr_texts  # title
        assert "Escribe aquí" in attr_texts  # placeholder
        assert "Botón de acción" in attr_texts  # aria-label

        # Verificar metadata de atributos
        alt_segment = next(
            (
                seg
                for seg in attribute_segments
                if seg.original_text == "Descripción de la imagen"
            ),
            None,
        )
        assert alt_segment is not None
        assert alt_segment.attribute_name == "alt"
        assert alt_segment.element_tag == "img"

    def test_html_min_length_filter(self, extractor):
        """Test: Filtrar textos muy cortos (< 3 caracteres)."""
        temp_dir = tempfile.mkdtemp()
        html_path = Path(temp_dir) / "short.html"

        html_content = """<html>
<body>
    <p>OK</p>
    <p>A</p>
    <p>12</p>
    <p>Este sí es suficientemente largo</p>
</body>
</html>"""

        html_path.write_text(html_content, encoding="utf-8")

        try:
            content = extractor.extract_from_html_file(html_path, "short.html")
            texts = [seg.original_text for seg in content.segments]

            # Solo debe extraerse el texto largo
            assert "Este sí es suficientemente largo" in texts
            assert "OK" not in texts  # Muy corto
            assert "A" not in texts  # Muy corto
            assert "12" not in texts  # Muy corto
        finally:
            shutil.rmtree(temp_dir)

    def test_html_direct_text_only(self, extractor):
        """Test: Extraer solo texto directo, no de elementos hijos."""
        temp_dir = tempfile.mkdtemp()
        html_path = Path(temp_dir) / "nested.html"

        html_content = """<html>
<body>
    <div>
        Texto del div padre
        <span>Texto del span hijo</span>
        Más texto del div
    </div>
</body>
</html>"""

        html_path.write_text(html_content, encoding="utf-8")

        try:
            content = extractor.extract_from_html_file(html_path, "nested.html")
            texts = [seg.original_text for seg in content.segments]

            # Debe extraerse texto del div Y del span por separado
            assert any("Texto del div padre" in text for text in texts)
            assert "Texto del span hijo" in texts

        finally:
            shutil.rmtree(temp_dir)

    def test_total_characters_count(self, extractor, sample_manifest):
        """Test: Contador de caracteres totales."""
        content = extractor.extract_from_manifest(sample_manifest)

        # Verificar que se cuenta correctamente
        expected_chars = sum(len(seg.original_text) for seg in content.segments)
        assert content.total_characters == expected_chars
        assert content.total_characters > 0

    def test_get_all_texts(self, extractor, sample_manifest):
        """Test: Método get_all_texts() devuelve lista de textos."""
        content = extractor.extract_from_manifest(sample_manifest)

        texts = content.get_all_texts()

        assert isinstance(texts, list)
        assert len(texts) == len(content.segments)
        assert "Curso de Ejemplo" in texts
