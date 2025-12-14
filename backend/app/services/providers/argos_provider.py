"""
Argos Translate provider for offline translation.

Free, open source, runs locally without internet.

Filepath: backend/app/services/providers/argos_provider.py
"""

import asyncio
import logging
from typing import Dict, List, Optional

from app.models.scorm import TranslatableSegment
from .base import TranslationProvider

logger = logging.getLogger(__name__)

# Lazy import to avoid errors if not installed
argostranslate = None
argostranslate_package = None


def _ensure_argos_installed():
    """Lazy import argostranslate modules."""
    global argostranslate, argostranslate_package
    if argostranslate is None:
        try:
            import argostranslate.translate as at
            import argostranslate.package as ap
            argostranslate = at
            argostranslate_package = ap
        except ImportError:
            raise ImportError(
                "argostranslate not installed. "
                "Run: pip install argostranslate"
            )


class ArgosTranslateProvider(TranslationProvider):
    """
    Translation provider using Argos Translate (offline).

    Uses neural machine translation models that run locally.
    No internet required, completely free, private.

    First run will download language models (~100MB each).
    """

    name = "argos"

    def __init__(self, auto_download_models: bool = True):
        """
        Initialize Argos Translate provider.

        Args:
            auto_download_models: If True, automatically download missing models
        """
        _ensure_argos_installed()
        self.auto_download = auto_download_models
        self.total_chars_translated = 0
        self.total_requests = 0
        self._installed_languages: Optional[set] = None

    def _ensure_model_installed(
        self,
        source_lang: str,
        target_lang: str
    ) -> bool:
        """
        Ensure translation model is installed for language pair.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            True if model is available
        """
        # Check if translation is available
        installed = argostranslate.get_installed_languages()
        source = next((l for l in installed if l.code == source_lang), None)

        if source:
            target = next(
                (l for l in source.get_translation(installed)
                 if l.code == target_lang),
                None
            )
            if target:
                return True

        # Model not installed, try to download
        if self.auto_download:
            logger.info(
                f"[Argos] Downloading model for {source_lang} -> {target_lang}"
            )
            try:
                self._download_model(source_lang, target_lang)
                return True
            except Exception as e:
                logger.error(f"[Argos] Failed to download model: {e}")
                return False

        return False

    def _download_model(self, source_lang: str, target_lang: str):
        """Download translation model for language pair."""
        # Update package index
        argostranslate_package.update_package_index()

        # Find and install package
        available = argostranslate_package.get_available_packages()
        package = next(
            (p for p in available
             if p.from_code == source_lang and p.to_code == target_lang),
            None
        )

        if package:
            logger.info(f"[Argos] Installing package: {package}")
            argostranslate_package.install_from_path(package.download())
        else:
            raise ValueError(
                f"No Argos package available for {source_lang} -> {target_lang}"
            )

    async def translate_segments(
        self,
        segments: List[TranslatableSegment],
        source_language: str,
        target_language: str,
        course_context: str = "",
    ) -> Dict[str, str]:
        """
        Translate multiple segments using Argos Translate.

        Args:
            segments: List of segments to translate
            source_language: Source language code
            target_language: Target language code
            course_context: Ignored (Argos doesn't use context)

        Returns:
            Dict mapping segment_id to translated_text
        """
        if not segments:
            return {}

        logger.info(
            f"[Argos] Translating {len(segments)} segments "
            f"from {source_language} to {target_language}"
        )

        # Ensure model is installed
        if not self._ensure_model_installed(source_language, target_language):
            logger.error(
                f"[Argos] Model not available for {source_language} -> {target_language}"
            )
            # Return originals if model not available
            return {s.segment_id: s.original_text for s in segments}

        translations = {}

        for segment in segments:
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
                    f"[Argos] Error translating segment {segment.segment_id}: {e}"
                )
                translations[segment.segment_id] = segment.original_text

        logger.info(
            f"[Argos] Completed: {len(translations)}/{len(segments)} segments"
        )
        return translations

    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate a single text using Argos Translate.

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

        # Run in thread pool since Argos is synchronous and CPU-intensive
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: argostranslate.translate(
                text,
                source_language,
                target_language
            )
        )

        return result

    def get_installed_languages(self) -> List[str]:
        """Get list of installed language codes."""
        installed = argostranslate.get_installed_languages()
        return [lang.code for lang in installed]

    def get_stats(self) -> Dict[str, any]:
        """Get translation statistics."""
        return {
            "total_requests": self.total_requests,
            "total_chars_translated": self.total_chars_translated,
            "estimated_cost_usd": 0.0,  # Free!
            "installed_languages": self.get_installed_languages(),
        }
