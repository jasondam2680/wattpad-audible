"""
Wattpad AI Literary Translation Engine Module
"""
from .models import (
    TranslationResult, TranslationError, TranslationValidationError,
    TranslationProviderError, TranslationRateLimitError, TranslationTimeoutError,
    LanguageDetectionError, UnsupportedLanguageError,
    BookTranslationContext, CharacterItem, GlossaryEntry, ChunkData,
    LanguageDetectionResult
)
from .detector import LanguageDetector
from .segmenter import TextSegmenter
from .prompts import PromptBuilder, DEFAULT_PROMPT_VERSION, CANONICAL_PROMPT_V1
from .provider import TranslationProvider, OpenAITranslationProvider, MockTranslationProvider
from .cache import TranslationCache
from .context import TranslationContextManager
from .glossary import GlossaryManager
from .service import TranslationService

__all__ = [
    "TranslationService",
    "TranslationProvider",
    "OpenAITranslationProvider",
    "MockTranslationProvider",
    "LanguageDetector",
    "TextSegmenter",
    "TranslationCache",
    "TranslationContextManager",
    "GlossaryManager",
    "PromptBuilder",
    "DEFAULT_PROMPT_VERSION",
    "CANONICAL_PROMPT_V1",
    "TranslationResult",
    "LanguageDetectionResult",
    "BookTranslationContext",
    "CharacterItem",
    "GlossaryEntry",
    "ChunkData",
    "TranslationError",
    "TranslationValidationError",
    "TranslationProviderError",
    "TranslationRateLimitError",
    "TranslationTimeoutError",
    "LanguageDetectionError",
    "UnsupportedLanguageError"
]
