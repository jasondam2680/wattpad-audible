from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChapterInfo(BaseModel):
    id: int
    title: str
    url: str
    length: Optional[int] = 0
    createDate: Optional[str] = None
    is_converted: bool = False
    audio_url: Optional[str] = None
    audio_duration: Optional[float] = None
    audio_size_bytes: Optional[int] = None
    audio_voice: Optional[str] = None
    audio_engine: Optional[str] = None

class StoryInfo(BaseModel):
    id: str
    title: str
    author: str
    cover: str
    description: str
    url: str
    language: Optional[Any] = "vi"
    numParts: int
    parts: List[ChapterInfo]

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
    device_id: Optional[str] = None
    user_id: Optional[str] = None

class CustomStoryRequest(BaseModel):
    title: str
    author: str = "Tác giả ẩn danh"
    cover: Optional[str] = None
    chapters: List[Dict[str, str]] # [{'title': 'Chương 1', 'content': 'Nội dung...'}]
    user_id: Optional[str] = None

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
    status: str # "queued", "processing", "paused", "completed", "failed", "cancelled"
    can_pause: bool = True
    error: Optional[str] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None
    resumed: bool = False

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


