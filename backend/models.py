import time
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TranslationConfig(BaseModel):
    enabled: bool = True
    source_language: str = "auto"  # "auto" | "en" | "vi"
    target_language: str = "vi"
    provider: Optional[str] = None  # None uses system default (e.g. openai or mock)
    model: Optional[str] = None
    prompt_version: str = "literary_vi_v1"
    preserve_names: bool = True
    audiobook_optimization: bool = True

class LanguageDetectionResult(BaseModel):
    source_language: str
    confidence: float
    detection_method: str  # "metadata", "heuristic", "analysis"
    is_supported: bool = True

class ChapterInfo(BaseModel):
    id: int
    title: str
    url: str = ""
    text: Optional[str] = None
    language: Optional[str] = None
    length: Optional[int] = 0
    createDate: Optional[str] = None
    is_converted: bool = False
    audio_url: Optional[str] = None
    audio_duration: Optional[float] = None
    audio_size_bytes: Optional[int] = None
    audio_voice: Optional[str] = None
    audio_engine: Optional[str] = None
    detected_language: Optional[str] = None
    is_translated: bool = False
    translated_title: Optional[str] = None

class StoryInfo(BaseModel):
    id: str
    title: str
    author: str = "Tác giả"
    cover: Optional[str] = None
    description: str = ""
    url: str = ""
    language: Optional[Any] = "vi"
    detected_language: Optional[str] = None
    language_confidence: Optional[float] = None
    numParts: Optional[int] = 0
    parts: List[ChapterInfo] = Field(default_factory=list)

    @property
    def cover_url(self) -> Optional[str]:
        return self.cover

class VoiceConfig(BaseModel):
    engine: str = "vieneu" # "vieneu" | "edge-tts"
    voice: str = "Thái Sơn"
    emotion: str = "neutral"
    pitch: str = "+0Hz"
    rate: str = "+0%"
    volume: str = "+0%"
    emotion_cue: Optional[str] = None # Dùng cho VieNeu-TTS: "[cười]", "[thở dài]", "[hắng giọng]"

class ConvertRequest(BaseModel):
    story_id: str
    chapter_ids: List[int]
    voice_config: VoiceConfig
    translation_config: Optional[TranslationConfig] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None

class CustomStoryRequest(BaseModel):
    title: str
    author: str = "Tác giả ẩn danh"
    cover: Optional[str] = None
    description: Optional[str] = None
    text: Optional[str] = None
    chapters: List[Dict[str, str]] = Field(default_factory=list) # [{'title': 'Chương 1', 'content': 'Nội dung...'}]
    user_id: Optional[str] = None
    language: Optional[str] = "auto"

class SampleVoiceRequest(BaseModel):
    text: Optional[str] = "Xin chào, đây là giọng đọc AI của ứng dụng sách nói Wattpad."
    voice_config: VoiceConfig

class TaskProgress(BaseModel):
    task_id: str
    story_id: str
    total_chapters: int
    completed_chapters: int
    current_chapter_title: str
    current_chapter_percent: int
    current_phase: str = "queued" # "queued", "scraping", "detecting_language", "translating", "synthesizing", "completed", "failed", "cancelled", "paused"
    translation_percent: int = 0
    tts_percent: int = 0
    status: str # "queued", "processing", "paused", "completed", "failed", "cancelled"
    can_pause: bool = True
    error: Optional[str] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None
    resumed: bool = False

class TranslationRecord(BaseModel):
    id: Optional[int] = None
    story_id: str
    chapter_id: int
    source_language: str
    target_language: str
    source_text_hash: str
    original_text: str
    translated_text: str
    provider: str
    model: str
    prompt_version: str
    status: str = "completed" # "pending", "processing", "completed", "failed", "cached"
    error_message: Optional[str] = None
    input_chars: int = 0
    output_chars: int = 0
    latency_ms: float = 0.0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    @property
    def cached(self) -> bool:
        return True

class TranslationPreviewRequest(BaseModel):
    text: str
    source_language: Optional[str] = "auto"
    target_language: Optional[str] = "vi"
    story_id: Optional[str] = None
    chapter_id: Optional[int] = None
    prompt_version: Optional[str] = "literary_vi_v1"

class TranslationPreviewResponse(BaseModel):
    success: bool
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    cached: bool = False
    provider: str
    model: str
    prompt_version: str
    latency_ms: float = 0.0
    error: Optional[str] = None

# ----------------- CẤU TRÚC XÁC THỰC & NGƯỜI DÙNG -----------------

class LoginRequest(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    username: str
    name: str
    role: str
    avatar: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[UserProfile] = None
    message: Optional[str] = None

import time

class ReadingHistoryItem(BaseModel):
    story_id: str
    story_title: str
    story_cover: Optional[str] = None
    chapter_id: int
    chapter_title: str
    timestamp: Optional[float] = Field(default_factory=time.time)
    progress_percent: Optional[int] = 0

class ListeningHistoryItem(BaseModel):
    story_id: str
    story_title: str
    story_cover: Optional[str] = None
    chapter_id: int
    chapter_title: str
    current_time: float
    duration: float
    timestamp: Optional[float] = Field(default_factory=time.time)

class UserLibraryStory(BaseModel):
    id: str
    title: str
    author: str
    cover: str
    numParts: int
    url: Optional[str] = ""
    added_at: Optional[float] = Field(default_factory=time.time)
    is_custom: Optional[bool] = False


