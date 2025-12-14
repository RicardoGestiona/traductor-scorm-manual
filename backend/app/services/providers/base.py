"""
Base interface for translation providers.

Filepath: backend/app/services/providers/base.py
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from app.models.scorm import TranslatableSegment


class TranslationProvider(ABC):
    """
    Abstract base class for translation providers.

    All providers must implement translate_segments() method.
    """

    # Provider name for logging
    name: str = "base"

    @abstractmethod
    async def translate_segments(
        self,
        segments: List[TranslatableSegment],
        source_language: str,
        target_language: str,
        course_context: str = "",
    ) -> Dict[str, str]:
        """
        Translate multiple segments.

        Args:
            segments: List of segments to translate
            source_language: Source language code (e.g., "en", "es")
            target_language: Target language code (e.g., "fr", "de")
            course_context: Optional context about the course

        Returns:
            Dict mapping segment_id to translated_text
        """
        pass

    @abstractmethod
    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate a single text string.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code

        Returns:
            Translated text
        """
        pass

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of ISO 639-1 language codes
        """
        return [
            "es", "en", "fr", "de", "it", "pt",
            "nl", "pl", "zh", "ja", "ru", "ar"
        ]
