"""
Translation Cache with SHA-256 Hashing & SQLite Persistence
"""
import hashlib
from typing import Optional, Any, Dict, List
from backend.database import DatabaseManager
from backend.models import TranslationRecord

class TranslationCache:
    def __init__(self, db: DatabaseManager):
        self.db = db

    @staticmethod
    def compute_hash(
        text: str,
        source_language: str,
        target_language: str,
        model: str,
        prompt_version: str
    ) -> str:
        """Tạo khóa băm SHA-256 chuẩn hóa cho cache bản dịch"""
        raw_key = f"{text.strip()}||{source_language.lower()}||{target_language.lower()}||{model.lower()}||{prompt_version.lower()}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(
        self,
        text: str,
        source_language: str,
        target_language: str,
        model: str,
        prompt_version: str
    ) -> Optional[TranslationRecord]:
        """Tra cứu bản dịch hợp lệ trong cache"""
        text_hash = self.compute_hash(text, source_language, target_language, model, prompt_version)
        return self.db.get_translation_by_hash(
            source_text_hash=text_hash,
            source_language=source_language,
            target_language=target_language,
            model=model,
            prompt_version=prompt_version
        )

    def get_by_chapter(self, story_id: str, chapter_id: int) -> Optional[TranslationRecord]:
        """Lấy bản dịch đã lưu theo story_id và chapter_id"""
        rec = self.db.get_chapter_translation(story_id, chapter_id)
        if isinstance(rec, dict):
            return TranslationRecord(**rec)
        return rec

    def set(
        self,
        record: Optional[TranslationRecord] = None,
        result: Optional[Any] = None,
        story_id: str = "",
        chapter_id: int = 0,
        chapter_title: str = ""
    ) -> int:
        """Lưu bản dịch vào cache database"""
        if record is not None:
            return self.db.save_translation(record)
        
        if result is not None:
            src_text = getattr(result, "source_text", "") or ""
            text_hash = getattr(result, "source_text_hash", "") or self.compute_hash(
                src_text,
                result.source_language,
                result.target_language,
                result.model,
                result.prompt_version
            )
            rec = TranslationRecord(
                story_id=story_id,
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                source_language=result.source_language,
                target_language=result.target_language,
                source_text_hash=text_hash,
                original_text=src_text,
                translated_text=result.translated_text,
                provider=result.provider,
                model=result.model,
                prompt_version=result.prompt_version,
                input_chars=result.input_chars,
                output_chars=result.output_chars,
                latency_ms=result.latency_ms
            )
            return self.db.save_translation(rec)
        return 0
