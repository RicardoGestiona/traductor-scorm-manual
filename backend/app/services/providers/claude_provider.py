"""
Claude API provider for high-quality translation.

Paid service, requires Anthropic API key.

Filepath: backend/app/services/providers/claude_provider.py
"""

import asyncio
import json
import re
import logging
from typing import Dict, List

import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.models.scorm import TranslatableSegment
from .base import TranslationProvider

logger = logging.getLogger(__name__)


class ClaudeTranslateProvider(TranslationProvider):
    """
    Translation provider using Claude API (Anthropic).

    High quality contextual translations, but requires paid API key.
    Best for complex e-learning content.
    """

    name = "claude"
    MODEL = "claude-3-5-sonnet-20241022"
    MAX_TOKENS_PER_REQUEST = 4096
    MAX_SEGMENTS_PER_BATCH = 50

    TRANSLATION_PROMPT = """Eres un traductor experto de contenido e-learning y SCORM.

TAREA:
Traduce los siguientes textos de {source_lang} a {target_lang}.

REGLAS CRITICAS:
1. PRESERVA toda estructura HTML si existe (tags, atributos, clases, IDs)
2. NO traduzcas: codigo JavaScript, nombres de variables, URLs, nombres de archivos
3. Manten terminologia e-learning estandar
4. Traduce de forma natural y fluida, no literal
5. Respeta mayusculas/minusculas del original cuando sea relevante

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

IMPORTANTE: Devuelve SOLO el JSON, sin explicaciones ni markdown.
"""

    def __init__(self, api_key: str):
        """Initialize Claude provider with API key."""
        if not api_key:
            raise ValueError("Anthropic API key is required")

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
        """Translate multiple segments using Claude API."""
        if not segments:
            return {}

        logger.info(
            f"[Claude] Translating {len(segments)} segments "
            f"from {source_language} to {target_language}"
        )

        # Divide into batches
        batches = self._create_batches(segments, self.MAX_SEGMENTS_PER_BATCH)
        all_translations = {}

        for batch_idx, batch in enumerate(batches):
            logger.debug(
                f"[Claude] Processing batch {batch_idx + 1}/{len(batches)}"
            )

            try:
                batch_translations = await self._translate_batch(
                    batch, source_language, target_language, course_context
                )
                all_translations.update(batch_translations)
            except Exception as e:
                logger.error(f"[Claude] Error in batch {batch_idx + 1}: {e}")
                # Keep originals on error
                for seg in batch:
                    all_translations[seg.segment_id] = seg.original_text

        return all_translations

    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate a single text using Claude."""
        if not text or not text.strip():
            return text

        segment = TranslatableSegment(
            segment_id="single",
            content_type="text",
            original_text=text,
            context="Single text translation"
        )

        translations = await self.translate_segments(
            [segment], source_language, target_language
        )

        return translations.get("single", text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (anthropic.RateLimitError, anthropic.APIConnectionError)
        ),
    )
    async def _translate_batch(
        self,
        segments: List[TranslatableSegment],
        source_lang: str,
        target_lang: str,
        course_context: str,
    ) -> Dict[str, str]:
        """Translate a batch of segments with retry logic."""
        texts_data = [
            {
                "segment_id": seg.segment_id,
                "text": seg.original_text,
                "context": seg.context,
                "type": seg.content_type.value if hasattr(seg.content_type, 'value') else str(seg.content_type),
            }
            for seg in segments
        ]

        prompt = self.TRANSLATION_PROMPT.format(
            source_lang=self._get_language_name(source_lang),
            target_lang=self._get_language_name(target_lang),
            course_context=course_context or "Curso de e-learning",
            texts_json=self._format_texts_for_prompt(texts_data),
        )

        # Run in executor since anthropic client is sync
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS_PER_REQUEST,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
        )

        self.total_requests += 1
        self.total_tokens_used += (
            response.usage.input_tokens + response.usage.output_tokens
        )

        return self._parse_response(response.content[0].text)

    def _create_batches(
        self, segments: List[TranslatableSegment], batch_size: int
    ) -> List[List[TranslatableSegment]]:
        """Divide segments into batches."""
        return [
            segments[i:i + batch_size]
            for i in range(0, len(segments), batch_size)
        ]

    def _format_texts_for_prompt(self, texts_data: List[Dict]) -> str:
        """Format texts for the prompt."""
        formatted = []
        for data in texts_data:
            formatted.append(
                f"[{data['segment_id']}] ({data['type']}) {data['context']}:\n"
                f'  "{data["text"]}"'
            )
        return "\n\n".join(formatted)

    def _parse_response(self, response_text: str) -> Dict[str, str]:
        """Parse JSON response from Claude."""
        cleaned = response_text.strip()

        # Remove markdown code blocks
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
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
            logger.error(f"[Claude] Failed to parse JSON: {response_text[:200]}")
            raise ValueError(f"Invalid JSON response: {e}")

    def _get_language_name(self, lang_code: str) -> str:
        """Convert language code to name."""
        names = {
            "en": "ingles", "es": "espanol", "fr": "frances",
            "de": "aleman", "it": "italiano", "pt": "portugues",
            "nl": "holandes", "pl": "polaco", "zh": "chino",
            "ja": "japones", "ru": "ruso", "ar": "arabe",
        }
        return names.get(lang_code.lower(), lang_code)

    def get_stats(self) -> Dict[str, any]:
        """Get translation statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": (self.total_tokens_used / 1_000_000) * 9.0,
        }
