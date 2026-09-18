from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LanguageDetectionResult(BaseModel):
    source_language: str
    confidence: float
    detection_method: str  # "metadata", "heuristic", "analysis"
    is_supported: bool = True

    @property
    def detected_language(self) -> str:
        return self.source_language

    @property
    def requires_translation(self) -> bool:
        return self.source_language not in ["vi", "vietnamese", "unknown"]

class CharacterItem(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    gender: Optional[str] = None  # "Male", "Female", "Unknown"
    relationship: Optional[str] = None
    preferred_pronouns: Optional[str] = None  # e.g., "anh / em", "tôi / bạn", "ta / ngươi"
    pronouns: Optional[str] = None
    speaking_style: Optional[str] = None
    notes: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.preferred_pronouns and self.pronouns:
            self.preferred_pronouns = self.pronouns
        elif not self.pronouns and self.preferred_pronouns:
            self.pronouns = self.preferred_pronouns

class GlossaryEntry(BaseModel):
    source_term: str
    target_term: str
    notes: Optional[str] = None

class BookTranslationContext(BaseModel):
    story_id: str
    title: str = ""
    author: str = ""
    genre: str = ""
    characters: List[CharacterItem] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)
    glossary: List[GlossaryEntry] = Field(default_factory=list)
    style_notes: str = ""
    previous_terminology: Dict[str, str] = Field(default_factory=dict)

class ChunkData(BaseModel):
    index: int
    text: str
    char_count: int
    is_dialogue: bool = False

class TranslationResult(BaseModel):
    translated_text: str
    source_language: str = "en"
    target_language: str = "vi"
    provider: str = "mock"
    model: str = "default"
    prompt_version: str = "literary_vi_v1"
    source_text_hash: str = ""
    source_text: Optional[str] = None
    input_chars: int = 0
    output_chars: int = 0
    latency_ms: float = 0.0
    cached: bool = False
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def source_lang(self) -> str:
        return self.source_language

    @property
    def target_lang(self) -> str:
        return self.target_language

class TranslationError(Exception):
    """Base error for translation operations"""
    pass

class LanguageDetectionError(TranslationError):
    pass

class TranslationProviderError(TranslationError):
    pass

class TranslationRateLimitError(TranslationProviderError):
    pass

class TranslationTimeoutError(TranslationProviderError):
    pass

class TranslationValidationError(TranslationError):
    pass

class UnsupportedLanguageError(TranslationError):
    pass
