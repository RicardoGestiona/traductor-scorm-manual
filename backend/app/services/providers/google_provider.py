"""
Google Translate provider using googletrans library.

Free, no API key required, uses Google Translate web service.

Filepath: backend/app/services/providers/google_provider.py
"""

import asyncio
import logging
from typing import Dict, List
from googletrans import Translator

from app.models.scorm import TranslatableSegment
from .base import TranslationProvider

logger = logging.getLogger(__name__)


class GoogleTranslateProvider(TranslationProvider):
    """
    Translation provider using Google Translate (free).

    Uses googletrans library which accesses Google Translate web API.
    No API key required, but may have rate limits.
    """

    name = "google"

    def __init__(self):
        """Initialize the Google Translate client."""
        self.translator = Translator()
        self.total_chars_translated = 0
        self.total_requests = 0

    async def translate_segments(
        self,
        segments: List[TranslatableSegment],
        source_language: str,
        target_language: str,
        course_context: str = "",
    ) -> Dict[str, str]:
        """
        Translate multiple segments using Google Translate.

        Args:
            segments: List of segments to translate
            source_language: Source language code
            target_language: Target language code
            course_context: Ignored (Google doesn't use context)

        Returns:
            Dict mapping segment_id to translated_text
        """
        if not segments:
            return {}

        logger.info(
            f"[GoogleTranslate] Translating {len(segments)} segments "
            f"from {source_language} to {target_language}"
        )

        translations = {}

        # Process in batches to avoid rate limits
        batch_size = 20
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]

            for segment in batch:
                try:
                    translated = await self.translate_text(
                        segment.original_text,
                        source_language,
                        target_language
                    )
                    translations[segment.segment_id] = translated
                    self.total_chars_translated += len(segment.original_text)

                except Exception as e:
                    logger.error(
                        f"[GoogleTranslate] Error translating segment "
                        f"{segment.segment_id}: {e}"
                    )
                    # Keep original on error
                    translations[segment.segment_id] = segment.original_text

            # Small delay between batches to avoid rate limiting
            if i + batch_size < len(segments):
                await asyncio.sleep(0.5)

        logger.info(
            f"[GoogleTranslate] Completed: {len(translations)}/{len(segments)} segments"
        )
        return translations

    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate a single text using Google Translate.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        self.total_requests += 1

        # Run in thread pool since googletrans is synchronous
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.translator.translate(
                text,
                src=source_language,
                dest=target_language
            )
        )

        return result.text

    def get_stats(self) -> Dict[str, int]:
        """Get translation statistics."""
        return {
            "total_requests": self.total_requests,
            "total_chars_translated": self.total_chars_translated,
            "estimated_cost_usd": 0.0,  # Free!
        }
