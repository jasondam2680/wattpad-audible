"""
Wattpad AI Translation Domain Service (Unified Facade)
"""
import os
import time
import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable

from backend.database import DatabaseManager
from backend.models import TranslationRecord, TranslationConfig
from .models import (
    TranslationResult, TranslationError, TranslationValidationError,
    BookTranslationContext, LanguageDetectionResult
)
from .prompts import DEFAULT_PROMPT_VERSION
from .detector import LanguageDetector
from .segmenter import TextSegmenter
from .provider import TranslationProvider, OpenAITranslationProvider, MockTranslationProvider
from .cache import TranslationCache
from .context import TranslationContextManager
from .glossary import GlossaryManager

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        provider: Optional[TranslationProvider] = None,
        detector: Optional[LanguageDetector] = None,
        cache: Optional[TranslationCache] = None,
        context_mgr: Optional[TranslationContextManager] = None,
        glossary_mgr: Optional[Any] = None,
        segmenter: Optional[TextSegmenter] = None
    ):
        self.db = db if db is not None else DatabaseManager()
        self.detector = detector if detector is not None else LanguageDetector()
        self.segmenter = segmenter if segmenter is not None else TextSegmenter(max_chunk_chars=1800)
        self.cache = cache if cache is not None else TranslationCache(self.db)
        self.context_mgr = context_mgr if context_mgr is not None else TranslationContextManager(self.db)
        self.glossary_mgr = glossary_mgr if glossary_mgr is not None else GlossaryManager(self.db)

        # Provider initialization
        if provider:
            self.provider = provider
        else:
            provider_type = os.environ.get("TRANSLATION_PROVIDER", "mock").lower()
            if provider_type == "openai" and os.environ.get("OPENAI_API_KEY"):
                self.provider = OpenAITranslationProvider()
            else:
                self.provider = MockTranslationProvider()

        # Concurrency limit for translation requests
        max_translation_concurrency = int(os.environ.get("GLOBAL_TRANSLATION_CONCURRENCY", "4"))
        self.semaphore = asyncio.Semaphore(max_translation_concurrency)

    def detect_language(self, text: str, metadata_lang: Optional[str] = None) -> LanguageDetectionResult:
        """Nhận diện ngôn ngữ của đoạn văn bản"""
        return self.detector.detect_language(text, metadata_lang)

    async def translate_chapter(
        self,
        story_id: str,
        chapter_id: int,
        text: str,
        config: Optional[TranslationConfig] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        check_pause_cancel: Optional[Callable[[], None]] = None
    ) -> TranslationResult:
        """
        Dịch toàn bộ nội dung của một chương truyện:
        1. Kiểm tra cache
        2. Phân đoạn nếu chương dài
        3. Dịch từng đoạn với ngữ cảnh câu chuyện
        4. Xác thực và lưu trữ kết quả
        """
        clean_text = text.strip() if text else ""
        if not clean_text:
            raise TranslationValidationError(f"Chương {chapter_id} không có nội dung để dịch.")

        target_lang = (config.target_language if config else None) or "vi"
        prompt_ver = (config.prompt_version if config else None) or DEFAULT_PROMPT_VERSION
        
        # 1. Phát hiện ngôn ngữ nguồn
        det_result = self.detect_language(clean_text)
        src_lang = det_result.source_language
        if src_lang == "vi" and target_lang == "vi":
            # Truyện đã là tiếng Việt, không cần dịch
            return TranslationResult(
                translated_text=clean_text,
                source_language="vi",
                target_language="vi",
                provider="identity",
                model="none",
                prompt_version=prompt_ver,
                source_text_hash=self.cache.compute_hash(clean_text, "vi", "vi", "none", prompt_ver),
                input_chars=len(clean_text),
                output_chars=len(clean_text),
                cached=True
            )

        provider_name = getattr(self.provider, "model", "default")

        # 2. Kiểm tra Cache
        cached_rec = self.cache.get(
            text=clean_text,
            source_language=src_lang,
            target_language=target_lang,
            model=provider_name,
            prompt_version=prompt_ver
        )
        if cached_rec:
            logger.info(f"[Translation Cache HIT] Chương {chapter_id} của truyện {story_id}")
            if progress_callback:
                progress_callback(100)
            return TranslationResult(
                translated_text=cached_rec.translated_text,
                source_language=cached_rec.source_language,
                target_language=cached_rec.target_language,
                provider=cached_rec.provider,
                model=cached_rec.model,
                prompt_version=cached_rec.prompt_version,
                source_text_hash=cached_rec.source_text_hash,
                input_chars=cached_rec.input_chars,
                output_chars=cached_rec.output_chars,
                latency_ms=cached_rec.latency_ms,
                cached=True
            )

        # 3. Tải Ngữ cảnh truyện (Context & Glossary)
        context = self.context_mgr.get_context(story_id)

        # 4. Phân đoạn văn bản (Text Segmentation)
        chunks = self.segmenter.segment(clean_text)
        total_chunks = len(chunks)
        translated_chunks: List[str] = []
        total_latency = 0.0

        async with self.semaphore:
            previous_tail_context = ""
            for idx, chunk in enumerate(chunks):
                if check_pause_cancel:
                    await check_pause_cancel()

                res = await self.provider.translate(
                    text=chunk.text,
                    source_language=src_lang,
                    target_language=target_lang,
                    context=context,
                    previous_context=previous_tail_context,
                    prompt_version=prompt_ver
                )

                translated_chunks.append(res.translated_text)
                total_latency += res.latency_ms
                
                # Giữ 1-2 câu cuối của đoạn dịch làm ngữ cảnh cho đoạn kế tiếp
                words = res.translated_text.split()
                previous_tail_context = " ".join(words[-40:]) if len(words) > 40 else res.translated_text

                percent = int(((idx + 1) / total_chunks) * 100)
                if progress_callback:
                    progress_callback(percent)
                await asyncio.sleep(0.01)

        # 5. Hợp nhất bản dịch (Merge Chunks)
        full_translated_text = self.segmenter.merge(translated_chunks)
        
        # 6. Kiểm tra tính toàn vẹn (Integrity Validation)
        self._validate_translation(clean_text, full_translated_text, src_lang, target_lang)

        # 7. Lưu bản dịch vào Database & Cache
        text_hash = self.cache.compute_hash(clean_text, src_lang, target_lang, provider_name, prompt_ver)
        record = TranslationRecord(
            story_id=story_id,
            chapter_id=chapter_id,
            source_language=src_lang,
            target_language=target_lang,
            source_text_hash=text_hash,
            original_text=clean_text,
            translated_text=full_translated_text,
            provider=getattr(self.provider, "__class__", type(self.provider)).__name__,
            model=provider_name,
            prompt_version=prompt_ver,
            status="completed",
            input_chars=len(clean_text),
            output_chars=len(full_translated_text),
            latency_ms=round(total_latency, 2),
            created_at=time.time(),
            updated_at=time.time()
        )
        self.cache.set(record)

        logger.info(f"[Translation Success] Đã dịch chương {chapter_id} ({len(clean_text)} chars -> {len(full_translated_text)} chars, {total_latency:.1f}ms)")

        return TranslationResult(
            translated_text=full_translated_text,
            source_language=src_lang,
            target_language=target_lang,
            provider=record.provider,
            model=record.model,
            prompt_version=record.prompt_version,
            source_text_hash=text_hash,
            input_chars=record.input_chars,
            output_chars=record.output_chars,
            latency_ms=record.latency_ms,
            cached=False
        )

    async def translate_text(
        self,
        text: str,
        source_language: str = "auto",
        target_language: str = "vi",
        story_id: Optional[str] = None,
        chapter_id: Optional[int] = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION
    ) -> TranslationResult:
        """Dịch văn bản trực tiếp cho tính năng Preview hoặc thử nghiệm"""
        clean_text = text.strip() if text else ""
        if not clean_text:
            raise TranslationValidationError("Văn bản nguồn không được để trống.")

        if source_language == "auto":
            det = self.detect_language(clean_text)
            source_language = det.source_language

        if source_language == "vi" and target_language == "vi":
            return TranslationResult(
                translated_text=clean_text,
                source_language="vi",
                target_language="vi",
                provider="identity",
                model="none",
                prompt_version=prompt_version,
                source_text_hash=self.cache.compute_hash(clean_text, "vi", "vi", "none", prompt_version),
                input_chars=len(clean_text),
                output_chars=len(clean_text),
                cached=True
            )

        provider_name = getattr(self.provider, "model", "default")
        cached_rec = self.cache.get(clean_text, source_language, target_language, provider_name, prompt_version)
        if cached_rec:
            return TranslationResult(
                translated_text=cached_rec.translated_text,
                source_language=cached_rec.source_language,
                target_language=cached_rec.target_language,
                provider=cached_rec.provider,
                model=cached_rec.model,
                prompt_version=cached_rec.prompt_version,
                source_text_hash=cached_rec.source_text_hash,
                input_chars=cached_rec.input_chars,
                output_chars=cached_rec.output_chars,
                latency_ms=cached_rec.latency_ms,
                cached=True
            )

        context = self.context_mgr.get_context(story_id) if story_id else None

        chunks = self.segmenter.segment(clean_text)
        translated_chunks = []
        total_latency = 0.0

        async with self.semaphore:
            prev_tail = ""
            for chunk in chunks:
                res = await self.provider.translate(
                    text=chunk.text,
                    source_language=source_language,
                    target_language=target_language,
                    context=context,
                    previous_context=prev_tail,
                    prompt_version=prompt_version
                )
                translated_chunks.append(res.translated_text)
                total_latency += res.latency_ms
                words = res.translated_text.split()
                prev_tail = " ".join(words[-40:]) if len(words) > 40 else res.translated_text

        merged = self.segmenter.merge(translated_chunks)
        self._validate_translation(clean_text, merged, source_language, target_language)

        text_hash = self.cache.compute_hash(clean_text, source_language, target_language, provider_name, prompt_version)
        
        if story_id and chapter_id:
            record = TranslationRecord(
                story_id=story_id,
                chapter_id=chapter_id,
                source_language=source_language,
                target_language=target_language,
                source_text_hash=text_hash,
                original_text=clean_text,
                translated_text=merged,
                provider=getattr(self.provider, "__class__", type(self.provider)).__name__,
                model=provider_name,
                prompt_version=prompt_version,
                status="completed",
                input_chars=len(clean_text),
                output_chars=len(merged),
                latency_ms=round(total_latency, 2),
                created_at=time.time(),
                updated_at=time.time()
            )
            self.cache.set(record)

        return TranslationResult(
            translated_text=merged,
            source_language=source_language,
            target_language=target_language,
            provider=getattr(self.provider, "__class__", type(self.provider)).__name__,
            model=provider_name,
            prompt_version=prompt_version,
            source_text_hash=text_hash,
            input_chars=len(clean_text),
            output_chars=len(merged),
            latency_ms=round(total_latency, 2),
            cached=False
        )

    def _validate_translation(self, original: str, translated: str, src_lang: str, tgt_lang: str):
        """Kiểm tra tính hợp lệ cơ bản của bản dịch"""
        if not translated or not translated.strip():
            raise TranslationValidationError("Bản dịch hoàn tất nhưng nội dung rỗng.")

        # Nếu văn bản gốc dài trên 100 ký tự mà bản dịch quá ngắn bất thường (< 15% độ dài gốc)
        if len(original) > 100 and len(translated) < len(original) * 0.15:
            raise TranslationValidationError(f"Bản dịch quá ngắn bất thường ({len(translated)} chars so với {len(original)} chars gốc).")
