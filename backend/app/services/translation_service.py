"""
Servicio de traducción usando Claude API (Anthropic).

Traduce textos extraídos de SCORM manteniendo contexto y formato.

Filepath: backend/app/services/translation_service.py
Feature alignment: STORY-007 - Integración con API de Traducción (Claude)
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.models.scorm import TranslatableSegment, ContentType

logger = logging.getLogger(__name__)


class TranslationServiceError(Exception):
    """Error durante la traducción."""

    pass


class TranslationService:
    """
    Servicio de traducción usando Claude API.

    Capabilities:
    - Traducción contextual con Claude (Sonnet 3.5)
    - Batch processing de múltiples textos
    - Retry logic con exponential backoff
    - Preservación de formato HTML/XML
    - Tracking de costos y tokens
    """

    # Modelo de Claude a usar
    MODEL = "claude-3-5-sonnet-20241022"

    # Límites de API
    MAX_TOKENS_PER_REQUEST = 4096
    MAX_SEGMENTS_PER_BATCH = 50  # Límite de segmentos por batch

    # Prompt templates
    TRANSLATION_PROMPT = """Eres un traductor experto de contenido e-learning y SCORM.

TAREA:
Traduce los siguientes textos de {source_lang} a {target_lang}.

REGLAS CRÍTICAS:
1. PRESERVA toda estructura HTML si existe (tags, atributos, clases, IDs)
2. NO traduzcas: código JavaScript, nombres de variables, URLs, nombres de archivos
3. Mantén terminología e-learning estándar (ej: "quiz" → "cuestionario" en ES)
4. Traduce de forma natural y fluida, no literal
5. Respeta mayúsculas/minúsculas del original cuando sea relevante
6. Para atributos HTML (alt, title, placeholder): traduce solo el texto, no las comillas

CONTEXTO DEL CURSO:
{course_context}

TEXTOS A TRADUCIR:
{texts_json}

FORMATO DE RESPUESTA:
Devuelve SOLO un objeto JSON con este formato exacto:
{{
  "translations": [
    {{"segment_id": "...", "translated_text": "..."}},
    {{"segment_id": "...", "translated_text": "..."}}
  ]
}}

IMPORTANTE:
- Devuelve SOLO el JSON, sin explicaciones ni markdown
- Mantén el segment_id original
- Si un texto está vacío, devuelve string vacío
"""

    def __init__(self, api_key: str):
        """
        Inicializar servicio de traducción.

        Args:
            api_key: API key de Anthropic
        """
        if not api_key:
            raise TranslationServiceError("API key de Anthropic es requerida")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.total_tokens_used = 0
        self.total_requests = 0

    async def translate_segments(
        self,
        segments: List[TranslatableSegment],
        source_language: str,
        target_language: str,
        course_context: str = "",
    ) -> Dict[str, str]:
        """
        Traducir múltiples segmentos con batch processing.

        Args:
            segments: Lista de segmentos a traducir
            source_language: Idioma origen (ej: "en", "es")
            target_language: Idioma destino (ej: "fr", "de")
            course_context: Contexto del curso para mejor traducción

        Returns:
            Dict con segment_id -> translated_text

        Raises:
            TranslationServiceError: Si falla la traducción
        """
        if not segments:
            return {}

        logger.info(
            f"Translating {len(segments)} segments from {source_language} to {target_language}"
        )

        # Dividir en batches para no exceder límites de API
        batches = self._create_batches(segments, self.MAX_SEGMENTS_PER_BATCH)
        all_translations = {}

        for batch_idx, batch in enumerate(batches):
            logger.debug(
                f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} segments)"
            )

            try:
                batch_translations = await self._translate_batch(
                    batch, source_language, target_language, course_context
                )
                all_translations.update(batch_translations)

            except Exception as e:
                logger.error(f"Error translating batch {batch_idx + 1}: {e}")
                raise TranslationServiceError(
                    f"Failed to translate batch {batch_idx + 1}: {str(e)}"
                )

        logger.info(
            f"Translation complete: {len(all_translations)}/{len(segments)} segments translated"
        )
        return all_translations

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIConnectionError)),
    )
    async def _translate_batch(
        self,
        segments: List[TranslatableSegment],
        source_lang: str,
        target_lang: str,
        course_context: str,
    ) -> Dict[str, str]:
        """
        Traducir un batch de segmentos con retry logic.

        Args:
            segments: Segmentos a traducir
            source_lang: Idioma origen
            target_lang: Idioma destino
            course_context: Contexto del curso

        Returns:
            Dict con segment_id -> translated_text
        """
        # Preparar textos para el prompt
        texts_data = [
            {
                "segment_id": seg.segment_id,
                "text": seg.original_text,
                "context": seg.context,
                "type": seg.content_type.value,
            }
            for seg in segments
        ]

        # Crear prompt con contexto
        prompt = self.TRANSLATION_PROMPT.format(
            source_lang=self._get_language_name(source_lang),
            target_lang=self._get_language_name(target_lang),
            course_context=course_context or "Curso de e-learning",
            texts_json=self._format_texts_for_prompt(texts_data),
        )

        # Llamar a Claude API
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS_PER_REQUEST,
                temperature=0.3,  # Baja temperatura para traducciones consistentes
                messages=[{"role": "user", "content": prompt}],
            )

            # Actualizar métricas
            self.total_requests += 1
            self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

            logger.debug(
                f"API call successful. Tokens: {response.usage.input_tokens} in, "
                f"{response.usage.output_tokens} out"
            )

            # Parsear respuesta JSON
            translations = self._parse_response(response.content[0].text)
            return translations

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise TranslationServiceError(f"Claude API error: {str(e)}")

    def _create_batches(
        self, segments: List[TranslatableSegment], batch_size: int
    ) -> List[List[TranslatableSegment]]:
        """
        Dividir segmentos en batches.

        Args:
            segments: Lista de segmentos
            batch_size: Tamaño máximo del batch

        Returns:
            Lista de batches
        """
        batches = []
        for i in range(0, len(segments), batch_size):
            batches.append(segments[i : i + batch_size])
        return batches

    def _format_texts_for_prompt(self, texts_data: List[Dict]) -> str:
        """
        Formatear textos para el prompt de forma legible.

        Args:
            texts_data: Lista de dicts con segment_id, text, context, type

        Returns:
            String formateado para el prompt
        """
        formatted = []
        for data in texts_data:
            formatted.append(
                f"[{data['segment_id']}] ({data['type']}) {data['context']}:\n"
                f'  "{data["text"]}"'
            )
        return "\n\n".join(formatted)

    def _parse_response(self, response_text: str) -> Dict[str, str]:
        """
        Parsear respuesta JSON de Claude.

        Args:
            response_text: Texto de respuesta

        Returns:
            Dict con segment_id -> translated_text

        Raises:
            TranslationServiceError: Si el JSON es inválido
        """
        import json
        import re

        # Limpiar respuesta (a veces Claude incluye markdown)
        cleaned = response_text.strip()

        # Remover bloques de código si existen
        if "```" in cleaned:
            # Extraer JSON entre ```json y ```
            match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                # Intentar encontrar JSON sin los backticks
                cleaned = re.sub(r"```(?:json)?", "", cleaned)
                cleaned = re.sub(r"```", "", cleaned)

        try:
            data = json.loads(cleaned)
            translations = {}

            for item in data.get("translations", []):
                segment_id = item.get("segment_id")
                translated = item.get("translated_text", "")
                if segment_id:
                    translations[segment_id] = translated

            return translations

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}...")
            raise TranslationServiceError(f"Invalid JSON response from API: {str(e)}")

    def _get_language_name(self, lang_code: str) -> str:
        """
        Convertir código de idioma a nombre completo.

        Args:
            lang_code: Código de idioma (ej: "es", "en", "fr")

        Returns:
            Nombre del idioma
        """
        lang_names = {
            "en": "inglés",
            "es": "español",
            "fr": "francés",
            "de": "alemán",
            "it": "italiano",
            "pt": "portugués",
            "nl": "holandés",
            "pl": "polaco",
            "zh": "chino",
            "ja": "japonés",
            "ru": "ruso",
            "ar": "árabe",
        }
        return lang_names.get(lang_code.lower(), lang_code)

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Obtener estadísticas de uso de la API.

        Returns:
            Dict con total_requests y total_tokens_used
        """
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": self._estimate_cost(self.total_tokens_used),
        }

    def _estimate_cost(self, total_tokens: int) -> float:
        """
        Estimar costo aproximado basado en tokens.

        Claude 3.5 Sonnet pricing (approximate):
        - Input: $3 per million tokens
        - Output: $15 per million tokens
        Asumimos ratio 1:1 para simplicidad

        Args:
            total_tokens: Total de tokens usados

        Returns:
            Costo estimado en USD
        """
        # Precio promedio: (3 + 15) / 2 = 9 USD por millón de tokens
        avg_price_per_million = 9.0
        return (total_tokens / 1_000_000) * avg_price_per_million
