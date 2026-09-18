import os
import re
import uuid
import asyncio
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from .models import TaskProgress, VoiceConfig, StoryInfo, ChapterInfo, TranslationConfig
from .tts_engine import TTSEngine, AUDIO_DIR
from .scraper import WattpadScraper
from .database import DatabaseManager
from .translation import TranslationService, TranslationError

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_DIR = DATA_DIR / "archives"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

class TaskManager:
    def __init__(
        self,
        tts_engine: Optional[TTSEngine] = None,
        scraper: Optional[WattpadScraper] = None,
        db: Optional[DatabaseManager] = None,
        translation_service: Optional[TranslationService] = None,
        **kwargs
    ):
        self.tts = tts_engine if tts_engine is not None else TTSEngine()
        self.scraper = scraper if scraper is not None else WattpadScraper()
        self.db = db if db is not None else DatabaseManager()
        self.translation = translation_service if translation_service is not None else TranslationService(self.db)
        self.translation_service = self.translation
        self.tasks: Dict[str, TaskProgress] = {}
        self.pause_events: Dict[str, asyncio.Event] = {}
        self.cancel_flags: Dict[str, bool] = {}
        # Theo dõi phiên chuyển đổi đang chạy theo thiết bị đầu cuối: key -> task_id
        self.device_active_tasks: Dict[str, str] = {}
        # Giới hạn số tác vụ tổng thể, tự động co giãn theo số nhân CPU
        max_task_workers = int(os.environ.get("MAX_TASK_CONCURRENCY", max(2, os.cpu_count() or 2)))
        self.concurrency_semaphore = asyncio.Semaphore(max_task_workers)

    def _save_task_state(self, task: TaskProgress):
        """Lưu trạng thái tác vụ vào SQLite và cập nhật memory cache"""
        self.tasks[task.task_id] = task
        try:
            self.db.save_task(task)
        except Exception as e:
            logger.error(f"Lỗi lưu trạng thái task {task.task_id} vào DB: {e}")

    def save_story(self, story: StoryInfo):
        """Lưu story vào SQLite"""
        try:
            self.db.save_story(story)
        except Exception as e:
            logger.error(f"Lỗi lưu story {story.id} vào DB: {e}")

    def load_story(self, story_id: str) -> Optional[StoryInfo]:
        """Tải thông tin story từ SQLite"""
        safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
        return self.db.get_story(safe_sid)

    def update_chapter_audio_status(
        self,
        story_id: str,
        chapter_id: int,
        duration: float,
        size_bytes: int,
        voice_name: Optional[str] = None,
        engine: Optional[str] = None
    ):
        """Cập nhật trạng thái audio của chương trong SQLite"""
        safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
        self.db.update_chapter_audio(
            safe_sid, chapter_id, duration, size_bytes, voice_name, engine
        )

    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        """Lấy thông tin tiến trình tác vụ từ memory hoặc SQLite"""
        if task_id in self.tasks:
            return self.tasks[task_id]
        task = self.db.get_task(task_id)
        if task:
            self.tasks[task_id] = task
        return task

    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Alias cho get_task"""
        return self.get_task(task_id)

    def get_active_task_for_device(self, device_id: str, story_id: Optional[str] = None) -> Optional[TaskProgress]:
        """Tìm tác vụ đang thực thi hoặc tạm dừng của thiết bị đầu cuối"""
        if not device_id:
            return None

        # 1. Tìm trong memory cache theo (device_id, story_id)
        if story_id:
            dev_key = f"{device_id}_{story_id}"
            if dev_key in self.device_active_tasks:
                tid = self.device_active_tasks[dev_key]
                t = self.get_task(tid)
                if t and t.status in ["processing", "queued", "paused"]:
                    return t

        # 2. Tìm trong SQLite
        return self.db.get_active_task_for_device(device_id, story_id)

    def pause_task(self, task_id: str) -> bool:
        """Tạm dừng tiến trình đang chuyển đổi"""
        task = self.get_task(task_id)
        if not task or task.status != "processing":
            return False
        task.status = "paused"
        task.current_phase = "paused"
        if task_id in self.pause_events:
            self.pause_events[task_id].clear()
        self._save_task_state(task)
        logger.info(f"Tác vụ {task_id} đã tạm dừng.")
        return True

    def resume_task(self, task_id: str) -> bool:
        """Tiếp tục tiến trình đã tạm dừng"""
        task = self.get_task(task_id)
        if not task or task.status != "paused":
            return False
        task.status = "processing"
        task.current_phase = "synthesizing"
        if task_id in self.pause_events:
            self.pause_events[task_id].set()
        self._save_task_state(task)
        logger.info(f"Tác vụ {task_id} đã tiếp tục.")
        return True

    def cancel_task(self, task_id: str) -> bool:
        """Hủy bỏ hoàn toàn tiến trình"""
        task = self.get_task(task_id)
        if not task or task.status in ["completed", "failed", "cancelled"]:
            return False
        task.status = "cancelled"
        task.current_phase = "cancelled"
        self.cancel_flags[task_id] = True
        if task_id in self.pause_events:
            self.pause_events[task_id].set()

        # Xóa khỏi danh sách tác vụ tích cực của thiết bị
        if task.device_id and task.story_id:
            dev_key = f"{task.device_id}_{task.story_id}"
            self.device_active_tasks.pop(dev_key, None)

        self._save_task_state(task)
        logger.info(f"Tác vụ {task_id} đã bị hủy.")
        return True

    async def start_conversion_task(
        self,
        story_id: str,
        chapter_ids: List[int],
        voice_config: VoiceConfig,
        translation_config: Optional[TranslationConfig] = None,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Bắt đầu hoặc tiếp nối phiên chuyển đổi sách nói và tự động dịch AI nếu cần.
        """
        safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
        dev_key = f"{device_id}_{safe_sid}" if device_id else None

        # 1. Kiểm tra phiên đang hoạt động từ cùng thiết bị đầu cuối
        if dev_key and dev_key in self.device_active_tasks:
            existing_task_id = self.device_active_tasks[dev_key]
            existing_task = self.get_task(existing_task_id)
            if existing_task:
                if existing_task.status in ["processing", "queued"]:
                    logger.info(f"[Phiên tiếp nối] Thiết bị {device_id} tiếp tục phiên hiện có: {existing_task_id}.")
                    existing_task.resumed = True
                    return existing_task_id
                elif existing_task.status == "paused":
                    logger.info(f"[Phiên tiếp nối] Đang tự động tiếp tục tác vụ đã tạm dừng: {existing_task_id}.")
                    self.resume_task(existing_task_id)
                    existing_task.resumed = True
                    return existing_task_id

        # 2. Đếm số chương đã được chuyển đổi trước đó
        already_completed = 0
        for cid in chapter_ids:
            p = self.tts.get_audio_path(safe_sid, cid)
            if p and p.exists() and p.stat().st_size > 1000:
                already_completed += 1

        task_id = str(uuid.uuid4())[:8]
        is_all_done = (already_completed == len(chapter_ids) and len(chapter_ids) > 0)

        task = TaskProgress(
            task_id=task_id,
            story_id=safe_sid,
            total_chapters=len(chapter_ids),
            completed_chapters=already_completed,
            current_chapter_title="Hoàn tất chuyển đổi tất cả các chương!" if is_all_done else ("Tiếp tục phiên chuyển đổi..." if already_completed > 0 else "Đang khởi tạo..."),
            current_chapter_percent=100 if is_all_done else 0,
            current_phase="completed" if is_all_done else "queued",
            status="completed" if is_all_done else "queued",
            can_pause=True,
            device_id=device_id,
            user_id=user_id,
            resumed=already_completed > 0
        )

        self._save_task_state(task)

        if dev_key:
            self.device_active_tasks[dev_key] = task_id

        if is_all_done:
            logger.info(f"Tất cả {len(chapter_ids)} chương đã có sẵn audio, hoàn tất ngay.")
            return task_id

        self.pause_events[task_id] = asyncio.Event()
        self.pause_events[task_id].set()
        self.cancel_flags[task_id] = False

        # Khởi chạy tác vụ nền tiếp tục chuyển đổi các chương còn thiếu
        asyncio.create_task(self._process_conversion(
            task_id=task_id,
            story_id=safe_sid,
            chapter_ids=chapter_ids,
            voice_config=voice_config,
            translation_config=translation_config,
            dev_key=dev_key
        ))
        return task_id

    async def _process_conversion(
        self,
        task_id: str,
        story_id: str,
        chapter_ids: List[int],
        voice_config: VoiceConfig,
        translation_config: Optional[TranslationConfig] = None,
        dev_key: Optional[str] = None
    ):
        task = self.get_task(task_id)
        if not task:
            return

        async with self.concurrency_semaphore:
            task.status = "processing"
            task.current_phase = "scraping"
            self._save_task_state(task)

            story = self.load_story(story_id)
            if not story:
                task.status = "failed"
                task.current_phase = "failed"
                task.error = f"Không tìm thấy dữ liệu truyện {story_id}"
                self._save_task_state(task)
                if dev_key:
                    self.device_active_tasks.pop(dev_key, None)
                return

            chapter_map = {p.id: p for p in story.parts}

            async def check_pause_cancel():
                if self.cancel_flags.get(task_id, False):
                    raise asyncio.CancelledError("Tác vụ đã bị hủy bởi người dùng.")
                if task.status == "paused":
                    event = self.pause_events.get(task_id)
                    if event:
                        await event.wait()
                    if self.cancel_flags.get(task_id, False):
                        raise asyncio.CancelledError("Tác vụ đã bị hủy bởi người dùng.")

            try:
                cpu_cores = os.cpu_count() or 2
                if voice_config.engine == "edge-tts":
                    chap_concurrency = int(os.environ.get("EDGE_TTS_CONCURRENCY", "4"))
                else:
                    chap_concurrency = int(os.environ.get("VIENEU_CONCURRENCY", str(max(1, cpu_cores // 2))))

                chap_semaphore = asyncio.Semaphore(chap_concurrency)
                task_lock = asyncio.Lock()
                logger.info(f"Khởi chạy chuyển đổi task {task_id} với mức song song {chap_concurrency} chương ({voice_config.engine}).")

                async def process_single_chapter(cid: int):
                    async with chap_semaphore:
                        await check_pause_cancel()

                        chapter_obj = chapter_map.get(cid)
                        chapter_title = chapter_obj.title if chapter_obj else f"Chương {cid}"

                        # Kiểm tra nếu chương này ĐÃ có audio: BỎ QUA chuyển đổi lại
                        existing_audio = self.tts.get_audio_path(story_id, cid)
                        if existing_audio and existing_audio.exists() and existing_audio.stat().st_size > 1000:
                            logger.info(f"[Tiếp tục phiên] Chương {cid} ({chapter_title}) đã có file audio từ trước.")
                            meta = self.tts.get_audio_metadata(story_id, cid)
                            v_name = (meta.get("voice") if meta else None) or (chapter_obj.audio_voice if chapter_obj else None) or "Thái Sơn"
                            v_eng = (meta.get("engine") if meta else None) or (chapter_obj.audio_engine if chapter_obj else None) or "vieneu"
                            self.update_chapter_audio_status(
                                story_id,
                                cid,
                                duration=0.0,
                                size_bytes=existing_audio.stat().st_size,
                                voice_name=v_name,
                                engine=v_eng
                            )
                            return

                        async with task_lock:
                            task.current_chapter_title = chapter_title
                            task.current_phase = "scraping"
                            self._save_task_state(task)

                        # 1. Lấy nội dung chữ của chương
                        logger.info(f"Đang lấy nội dung chương {cid}: {chapter_title}")
                        raw_text = ""
                        custom_file = DATA_DIR / "custom_texts" / story_id / f"{cid}.txt"
                        if custom_file.exists():
                            try:
                                with open(custom_file, "r", encoding="utf-8") as f:
                                    raw_text = f.read()
                            except Exception as e:
                                logger.error(f"Lỗi đọc file custom text {custom_file}: {e}")

                        if not raw_text:
                            try:
                                raw_text = await asyncio.to_thread(self.scraper.get_chapter_text, cid)
                            except Exception as e:
                                logger.error(f"Lỗi tải text chương {cid}: {e}")

                        if not raw_text or not raw_text.strip():
                            logger.warning(f"Chương {cid} không có nội dung chữ, bỏ qua.")
                            async with task_lock:
                                task.completed_chapters += 1
                                self._save_task_state(task)
                            return

                        # 2. Nhận diện ngôn ngữ & Quyết định dịch thuật
                        det_res = self.translation.detect_language(raw_text, metadata_lang=str(story.language or ""))
                        src_lang = det_res.source_language
                        
                        # Cập nhật detected language vào story và chapter
                        if chapter_obj:
                            chapter_obj.detected_language = src_lang

                        # Xác định translation policy
                        should_translate = False
                        if src_lang == "vi":
                            should_translate = False
                        elif src_lang == "en":
                            if translation_config is not None:
                                should_translate = translation_config.enabled and translation_config.target_language == "vi"
                            else:
                                # Mặc định tự động dịch nếu tiếng Anh và config không được chỉ định
                                should_translate = True

                        final_tts_text = raw_text

                        if should_translate:
                            async with task_lock:
                                task.current_phase = "translating"
                                task.current_chapter_title = f"[Đang dịch AI] {chapter_title}"
                                self._save_task_state(task)

                            def on_translation_progress(percent: int):
                                task.translation_percent = percent

                            try:
                                trans_res = await self.translation.translate_chapter(
                                    story_id=story_id,
                                    chapter_id=cid,
                                    text=raw_text,
                                    config=translation_config,
                                    progress_callback=on_translation_progress,
                                    check_pause_cancel=check_pause_cancel
                                )
                                final_tts_text = trans_res.translated_text
                                if chapter_obj:
                                    chapter_obj.is_translated = True
                            except asyncio.CancelledError:
                                raise
                            except Exception as te:
                                logger.exception(f"Lỗi khi dịch chương {cid}: {te}")
                                async with task_lock:
                                    task.status = "failed"
                                    task.current_phase = "failed"
                                    task.error = f"Lỗi dịch chương {cid}: {str(te)}"
                                    self._save_task_state(task)
                                return

                        # 3. Chuyển đổi Text-to-Speech
                        async with task_lock:
                            task.current_phase = "synthesizing"
                            task.current_chapter_title = f"[Đang đọc AI] {chapter_title}"
                            self._save_task_state(task)

                        def on_tts_progress(percent: int):
                            task.tts_percent = percent
                            if chap_concurrency == 1:
                                task.current_chapter_percent = percent
                            else:
                                overall = int(((task.completed_chapters + (percent / 100.0)) / max(1, task.total_chapters)) * 100)
                                task.current_chapter_percent = min(99, overall)

                        try:
                            res = await self.tts.convert_chapter_to_audio(
                                story_id=story_id,
                                chapter_id=cid,
                                chapter_title=chapter_title,
                                story_title=story.title,
                                story_author=story.author,
                                text=final_tts_text,
                                config=voice_config,
                                progress_callback=on_tts_progress,
                                check_pause_cancel=check_pause_cancel
                            )
                            self.update_chapter_audio_status(
                                story_id=story_id,
                                chapter_id=cid,
                                duration=res["duration"],
                                size_bytes=res["size_bytes"],
                                voice_name=voice_config.voice,
                                engine=voice_config.engine
                            )
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            logger.exception(f"Lỗi khi chuyển đổi TTS chương {cid}: {e}")
                            async with task_lock:
                                task.status = "failed"
                                task.current_phase = "failed"
                                task.error = f"Lỗi chuyển đổi âm thanh chương {cid}: {str(e)}"
                                self._save_task_state(task)
                            return

                        async with task_lock:
                            task.completed_chapters += 1
                            if chap_concurrency > 1:
                                task.current_chapter_percent = int((task.completed_chapters / max(1, task.total_chapters)) * 100)
                            self._save_task_state(task)

                # Thực thi chuyển đổi các chương song song có kiểm soát
                await asyncio.gather(*(process_single_chapter(cid) for cid in chapter_ids))

                if task.status != "failed":
                    task.status = "completed"
                    task.current_phase = "completed"
                    task.current_chapter_title = "Hoàn tất chuyển đổi tất cả các chương!"
                    task.current_chapter_percent = 100
                    self._save_task_state(task)
                    logger.info(f"Hoàn thành trọn vẹn task {task_id}")

            except asyncio.CancelledError:
                task.status = "cancelled"
                task.current_phase = "cancelled"
                task.current_chapter_title = "Đã dừng và hủy bỏ tiến trình."
                self._save_task_state(task)
                logger.info(f"Tác vụ {task_id} đã dừng theo yêu cầu của người dùng.")
            finally:
                self.pause_events.pop(task_id, None)
                self.cancel_flags.pop(task_id, None)
                if dev_key:
                    self.device_active_tasks.pop(dev_key, None)

    def create_story_zip(self, story_id: str) -> Optional[Path]:
        """Gom toàn bộ các file MP3 của truyện thành một file ZIP duy nhất để tải về"""
        safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
        story = self.load_story(safe_sid)
        if not story:
            return None

        audio_folder = AUDIO_DIR / safe_sid
        if not audio_folder.exists():
            return None

        mp3_files = list(audio_folder.glob("*.mp3"))
        if not mp3_files:
            return None

        zip_path = ARCHIVE_DIR / f"story_{safe_sid}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for mp3 in mp3_files:
                cid = int(mp3.stem) if mp3.stem.isdigit() else 0
                part = next((p for p in story.parts if p.id == cid), None)
                raw_title = part.title if part else mp3.stem
                clean_title = re.sub(r'[/\\:*?"<>|]', '_', raw_title).strip()
                in_zip_name = f"{clean_title or f'Chuong_{cid}'}.mp3"
                zipf.write(mp3, arcname=in_zip_name)

        return zip_path
