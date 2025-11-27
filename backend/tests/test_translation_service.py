"""
Tests para el servicio de traducción con Claude API.

Feature alignment: STORY-007 - Integración con API de Traducción (Claude)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from app.services.translation_service import TranslationService, TranslationServiceError
from app.models.scorm import TranslatableSegment, ContentType


class TestTranslationService:
    """Tests para TranslationService."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Fixture: Cliente de Anthropic mockeado."""
        with patch("app.services.translation_service.anthropic.Anthropic") as mock:
            yield mock

    @pytest.fixture
    def translation_service(self, mock_anthropic_client):
        """Fixture: TranslationService instance con cliente mockeado."""
        return TranslationService(api_key="test-api-key")

    @pytest.fixture
    def sample_segments(self):
        """Fixture: Segmentos de ejemplo para traducir."""
        return [
            TranslatableSegment(
                segment_id="seg_001",
                content_type=ContentType.HTML,
                original_text="Welcome to the course",
                context="h1 element in lesson1.html",
            ),
            TranslatableSegment(
                segment_id="seg_002",
                content_type=ContentType.HTML,
                original_text="Click here to continue",
                context="button element in lesson1.html",
            ),
            TranslatableSegment(
                segment_id="seg_003",
                content_type=ContentType.ATTRIBUTE,
                original_text="Next lesson",
                context="alt attribute of img in lesson1.html",
                attribute_name="alt",
            ),
        ]

    def test_init_service(self):
        """Test: Inicializar servicio con API key."""
        service = TranslationService(api_key="test-key-123")
        assert service.total_tokens_used == 0
        assert service.total_requests == 0

    def test_init_without_api_key(self):
        """Test: Error al inicializar sin API key."""
        with pytest.raises(TranslationServiceError, match="API key de Anthropic es requerida"):
            TranslationService(api_key="")

    @pytest.mark.asyncio
    async def test_translate_empty_segments(self, translation_service):
        """Test: Traducir lista vacía devuelve dict vacío."""
        result = await translation_service.translate_segments(
            segments=[],
            source_language="en",
            target_language="es",
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_translate_segments_success(
        self, translation_service, sample_segments, mock_anthropic_client
    ):
        """Test: Traducir segmentos exitosamente."""
        # Mock de la respuesta de Claude
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text=json.dumps(
                    {
                        "translations": [
                            {
                                "segment_id": "seg_001",
                                "translated_text": "Bienvenido al curso",
                            },
                            {
                                "segment_id": "seg_002",
                                "translated_text": "Haz clic aquí para continuar",
                            },
                            {
                                "segment_id": "seg_003",
                                "translated_text": "Siguiente lección",
                            },
                        ]
                    }
                )
            )
        ]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        # Configurar mock
        translation_service.client.messages.create = Mock(return_value=mock_response)

        # Ejecutar traducción
        result = await translation_service.translate_segments(
            segments=sample_segments,
            source_language="en",
            target_language="es",
            course_context="Curso de introducción",
        )

        # Verificar resultados
        assert len(result) == 3
        assert result["seg_001"] == "Bienvenido al curso"
        assert result["seg_002"] == "Haz clic aquí para continuar"
        assert result["seg_003"] == "Siguiente lección"

        # Verificar que se llamó a la API
        assert translation_service.client.messages.create.called
        assert translation_service.total_requests == 1
        assert translation_service.total_tokens_used == 150  # 100 + 50

    @pytest.mark.asyncio
    async def test_translate_with_markdown_response(
        self, translation_service, sample_segments
    ):
        """Test: Manejar respuesta con bloques de código markdown."""
        # Mock de respuesta con markdown
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='```json\n{\n  "translations": [\n    {"segment_id": "seg_001", "translated_text": "Texto traducido"}\n  ]\n}\n```'
            )
        ]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)

        translation_service.client.messages.create = Mock(return_value=mock_response)

        result = await translation_service.translate_segments(
            segments=[sample_segments[0]],
            source_language="en",
            target_language="es",
        )

        assert result["seg_001"] == "Texto traducido"

    @pytest.mark.asyncio
    async def test_batch_processing(self, translation_service):
        """Test: Batch processing de múltiples segmentos."""
        # Crear 60 segmentos (más que MAX_SEGMENTS_PER_BATCH = 50)
        segments = [
            TranslatableSegment(
                segment_id=f"seg_{i:03d}",
                content_type=ContentType.HTML,
                original_text=f"Text {i}",
                context="test context",
            )
            for i in range(60)
        ]

        # Mock de respuesta
        def mock_create(*args, **kwargs):
            response = Mock()
            # Extraer segment_ids del prompt para generar respuesta apropiada
            response.content = [
                Mock(
                    text=json.dumps(
                        {
                            "translations": [
                                {"segment_id": f"seg_{i:03d}", "translated_text": f"Texto {i}"}
                                for i in range(60)
                            ]
                        }
                    )
                )
            ]
            response.usage = Mock(input_tokens=100, output_tokens=50)
            return response

        translation_service.client.messages.create = Mock(side_effect=mock_create)

        result = await translation_service.translate_segments(
            segments=segments, source_language="en", target_language="es"
        )

        # Verificar que se tradujeron todos
        assert len(result) == 60
        # Verificar que se hicieron 2 llamadas (60 / 50 = 2 batches)
        assert translation_service.client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, translation_service, sample_segments):
        """Test: Error al recibir JSON inválido."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Invalid JSON {malformed}")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)

        translation_service.client.messages.create = Mock(return_value=mock_response)

        with pytest.raises(
            TranslationServiceError, match="Invalid JSON response from API"
        ):
            await translation_service.translate_segments(
                segments=sample_segments,
                source_language="en",
                target_language="es",
            )

    def test_create_batches(self, translation_service, sample_segments):
        """Test: Dividir segmentos en batches."""
        batches = translation_service._create_batches(sample_segments, batch_size=2)

        assert len(batches) == 2  # 3 segmentos / 2 = 2 batches
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1

    def test_get_language_name(self, translation_service):
        """Test: Convertir códigos de idioma a nombres."""
        assert translation_service._get_language_name("en") == "inglés"
        assert translation_service._get_language_name("es") == "español"
        assert translation_service._get_language_name("fr") == "francés"
        assert translation_service._get_language_name("de") == "alemán"
        assert translation_service._get_language_name("unknown") == "unknown"

    def test_format_texts_for_prompt(self, translation_service):
        """Test: Formatear textos para el prompt."""
        texts_data = [
            {
                "segment_id": "seg_001",
                "text": "Hello world",
                "context": "h1 element",
                "type": "html",
            },
            {
                "segment_id": "seg_002",
                "text": "Click here",
                "context": "button element",
                "type": "html",
            },
        ]

        formatted = translation_service._format_texts_for_prompt(texts_data)

        assert "seg_001" in formatted
        assert "Hello world" in formatted
        assert "h1 element" in formatted
        assert "seg_002" in formatted
        assert "Click here" in formatted

    def test_usage_stats(self, translation_service):
        """Test: Obtener estadísticas de uso."""
        # Simular uso
        translation_service.total_requests = 5
        translation_service.total_tokens_used = 10000

        stats = translation_service.get_usage_stats()

        assert stats["total_requests"] == 5
        assert stats["total_tokens_used"] == 10000
        assert "estimated_cost_usd" in stats
        assert stats["estimated_cost_usd"] > 0

    def test_estimate_cost(self, translation_service):
        """Test: Estimación de costos."""
        # 1 millón de tokens debería costar ~$9 (precio promedio)
        cost = translation_service._estimate_cost(1_000_000)
        assert cost == pytest.approx(9.0, rel=0.1)

        # 100k tokens
        cost = translation_service._estimate_cost(100_000)
        assert cost == pytest.approx(0.9, rel=0.1)

    @pytest.mark.asyncio
    async def test_parse_response_with_empty_translations(self, translation_service):
        """Test: Parsear respuesta con traducción vacía."""
        response_text = json.dumps(
            {
                "translations": [
                    {"segment_id": "seg_001", "translated_text": ""},
                    {"segment_id": "seg_002", "translated_text": "Texto válido"},
                ]
            }
        )

        result = translation_service._parse_response(response_text)

        assert result["seg_001"] == ""
        assert result["seg_002"] == "Texto válido"

    def test_parse_response_without_segment_id(self, translation_service):
        """Test: Ignorar traducciones sin segment_id."""
        response_text = json.dumps(
            {
                "translations": [
                    {"translated_text": "Sin ID"},  # Sin segment_id
                    {"segment_id": "seg_002", "translated_text": "Con ID"},
                ]
            }
        )

        result = translation_service._parse_response(response_text)

        assert len(result) == 1
        assert "seg_002" in result
        assert result["seg_002"] == "Con ID"
