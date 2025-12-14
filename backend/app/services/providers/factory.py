"""
Factory for creating translation providers.

Filepath: backend/app/services/providers/factory.py
"""

import logging
from enum import Enum
from typing import Optional

from .base import TranslationProvider
from .google_provider import GoogleTranslateProvider
from .argos_provider import ArgosTranslateProvider

logger = logging.getLogger(__name__)


class TranslationProviderType(str, Enum):
    """Available translation providers."""
    GOOGLE = "google"      # Google Translate (free, online)
    ARGOS = "argos"        # Argos Translate (free, offline)
    CLAUDE = "claude"      # Claude API (paid, high quality)


def get_translation_provider(
    provider_type: str = "google",
    **kwargs
) -> TranslationProvider:
    """
    Factory function to create a translation provider.

    Args:
        provider_type: Type of provider ("google", "argos", "claude")
        **kwargs: Additional arguments for specific providers

    Returns:
        TranslationProvider instance

    Raises:
        ValueError: If provider type is not supported

    Example:
        >>> provider = get_translation_provider("google")
        >>> translations = await provider.translate_segments(segments, "en", "es")
    """
    provider_type = provider_type.lower()

    if provider_type == TranslationProviderType.GOOGLE:
        logger.info("Using Google Translate provider (free, online)")
        return GoogleTranslateProvider()

    elif provider_type == TranslationProviderType.ARGOS:
        logger.info("Using Argos Translate provider (free, offline)")
        auto_download = kwargs.get("auto_download_models", True)
        return ArgosTranslateProvider(auto_download_models=auto_download)

    elif provider_type == TranslationProviderType.CLAUDE:
        # Import here to avoid circular dependency
        from app.services.providers.claude_provider import ClaudeTranslateProvider
        api_key = kwargs.get("api_key")
        if not api_key:
            raise ValueError("Claude provider requires api_key")
        logger.info("Using Claude API provider (paid, high quality)")
        return ClaudeTranslateProvider(api_key=api_key)

    else:
        raise ValueError(
            f"Unknown provider type: {provider_type}. "
            f"Supported: {[p.value for p in TranslationProviderType]}"
        )


def get_default_provider() -> TranslationProvider:
    """
    Get the default translation provider based on environment.

    Checks for available providers in order:
    1. Google Translate (always available)

    Returns:
        Default TranslationProvider instance
    """
    # Default to Google Translate as it requires no setup
    return GoogleTranslateProvider()
