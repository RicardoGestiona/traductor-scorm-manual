"""
Translation providers package.

Supported providers:
- google: Google Translate via googletrans (free, online)
- argos: Argos Translate (free, offline)
- claude: Claude API (paid, high quality)
"""

from .base import TranslationProvider
from .google_provider import GoogleTranslateProvider
from .argos_provider import ArgosTranslateProvider
from .factory import get_translation_provider, TranslationProviderType

__all__ = [
    "TranslationProvider",
    "GoogleTranslateProvider",
    "ArgosTranslateProvider",
    "get_translation_provider",
    "TranslationProviderType",
]
