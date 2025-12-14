"""
Translation service with configurable providers.

Supports multiple translation backends:
- google: Google Translate (free, online)
- argos: Argos Translate (free, offline)
- claude: Claude API (paid, high quality)

Filepath: backend/app/services/translation_service.py
Feature alignment: STORY-007 - Integración con API de Traducción
"""

import logging
from typing import Dict, List, Optional

from app.core.config import settings
from app.models.scorm import TranslatableSegment, ExtractionResult
from app.services.providers import (
    TranslationProvider,
    get_translation_provider,
    TranslationProviderType,
)

logger = logging.getLogger(__name__)


class TranslationServiceError(Exception):
    """Error during translation."""
    pass


class TranslationService:
    """
    Translation service with configurable providers.

    Usage:
        # Use default provider from config
        service = TranslationService()

        # Or specify provider explicitly
        service = TranslationService(provider_type="argos")

        # Translate segments
        translations = await service.translate_segments(
            segments, "en", "es"
        )
    """

    def __init__(
        self,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize translation service.

        Args:
            provider_type: Override config provider (google, argos, claude)
            api_key: API key for paid providers (claude)
        """
        self.provider_type = provider_type or settings.TRANSLATION_PROVIDER

        # Build kwargs for provider factory
        kwargs = {}
        if self.provider_type == TranslationProviderType.CLAUDE:
            kwargs["api_key"] = api_key or settings.ANTHROPIC_API_KEY
        elif self.provider_type == TranslationProviderType.ARGOS:
            kwargs["auto_download_models"] = settings.ARGOS_AUTO_DOWNLOAD

        self.provider: TranslationProvider = get_translation_provider(
            self.provider_type, **kwargs
        )

        logger.info(f"TranslationService initialized with provider: {self.provider.name}")

    async def translate_extraction_result(
        self,
        extraction_result: ExtractionResult,
        source_language: str,
        target_language: str,
        course_context: str = "",
    ) -> Dict[str, str]:
        """
        Translate all segments from an extraction result.

        Args:
            extraction_result: Result from ContentExtractor
            source_language: Source language code
            target_language: Target language code
            course_context: Optional course context for better translations

        Returns:
            Dict mapping segment_id to translated_text
        """
        # Collect all segments from all files
        all_segments: List[TranslatableSegment] = []
        for file_content in extraction_result.files_processed:
            all_segments.extend(file_content.segments)

        if not all_segments:
            logger.warning("No segments to translate")
            return {}

        logger.info(
            f"Translating {len(all_segments)} segments "
            f"from {source_language} to {target_language} "
            f"using {self.provider.name} provider"
        )

        return await self.translate_segments(
            all_segments, source_language, target_language, course_context
        )

    async def translate_segments(
        self,
        segments: List[TranslatableSegment],
        source_language: str,
        target_language: str,
        course_context: str = "",
    ) -> Dict[str, str]:
        """
        Translate a list of segments.

        Args:
            segments: List of TranslatableSegment
            source_language: Source language code
            target_language: Target language code
            course_context: Optional course context

        Returns:
            Dict mapping segment_id to translated_text

        Raises:
            TranslationServiceError: If translation fails
        """
        try:
            return await self.provider.translate_segments(
                segments, source_language, target_language, course_context
            )
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise TranslationServiceError(f"Translation failed: {str(e)}")

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
        return await self.provider.translate_text(
            text, source_language, target_language
        )

    def get_provider_info(self) -> Dict[str, any]:
        """
        Get information about the current provider.

        Returns:
            Dict with provider name, type, and stats
        """
        stats = {}
        if hasattr(self.provider, 'get_stats'):
            stats = self.provider.get_stats()

        return {
            "provider": self.provider.name,
            "type": self.provider_type,
            "supported_languages": self.provider.get_supported_languages(),
            "stats": stats,
        }


# Convenience function for quick translation
async def quick_translate(
    text: str,
    source_language: str = "auto",
    target_language: str = "en",
    provider: str = "google",
) -> str:
    """
    Quick translation of a single text.

    Args:
        text: Text to translate
        source_language: Source language (default: auto-detect)
        target_language: Target language (default: English)
        provider: Provider to use (default: google)

    Returns:
        Translated text

    Example:
        >>> translated = await quick_translate("Hola mundo", "es", "en")
        >>> print(translated)  # "Hello world"
    """
    service = TranslationService(provider_type=provider)
    return await service.translate_text(text, source_language, target_language)
