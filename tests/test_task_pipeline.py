import unittest
import asyncio
import os
import shutil
import tempfile
import json
from unittest.mock import AsyncMock, patch

from backend.database import Database
from backend.models import StoryInfo, ChapterInfo, VoiceConfig, TranslationConfig
from backend.tasks import TaskManager
from backend.translation.service import TranslationService
from backend.translation.provider import MockTranslationProvider
from backend.translation.detector import LanguageDetector
from backend.translation.cache import TranslationCache
from backend.translation.context import TranslationContextManager
from backend.translation.glossary import TranslationGlossaryManager

class TestTaskPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.stories_dir = os.path.join(self.test_dir, "stories")
        self.audio_dir = os.path.join(self.test_dir, "audio")
        self.archives_dir = os.path.join(self.test_dir, "archives")
        self.db_path = os.path.join(self.test_dir, "audiobook.db")
        os.makedirs(self.stories_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)

        self.db = Database(db_path=self.db_path)
        self.mock_provider = MockTranslationProvider()
        self.detector = LanguageDetector()
        self.cache = TranslationCache(self.db)
        self.context_mgr = TranslationContextManager(self.db)
        self.glossary_mgr = TranslationGlossaryManager(self.db)

        self.translation_service = TranslationService(
            provider=self.mock_provider,
            detector=self.detector,
            cache=self.cache,
            context_mgr=self.context_mgr,
            glossary_mgr=self.glossary_mgr
        )

        self.task_manager = TaskManager(
            db=self.db,
            stories_dir=self.stories_dir,
            audio_dir=self.audio_dir,
            archives_dir=self.archives_dir,
            translation_service=self.translation_service
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_story(self, story_id: str, title: str, chapters: list[dict]) -> StoryInfo:
        parts = []
        text_map = {}
        for ch in chapters:
            parts.append(ChapterInfo(
                id=ch["id"],
                title=ch["title"],
                url=""
            ))
            text_map[ch["id"]] = ch["text"]

        story = StoryInfo(
            id=story_id,
            title=title,
            author="Author Test",
            description="Description test",
            cover_url=None,
            parts=parts,
            numParts=len(parts)
        )
        self.task_manager.save_story(story)
        self.task_manager.scraper.get_chapter_text = lambda cid: text_map.get(cid, "")
        return story

    def test_pipeline_vietnamese_story_skips_translation(self):
        # Vietnamese story
        story = self._create_test_story(
            story_id="vi_story_01",
            title="Truyện Tiếng Việt",
            chapters=[{
                "id": 1,
                "title": "Chương 1: Mở Đầu",
                "text": "Mặt trời vừa ló rạng qua rặng tre đầu làng. Tiếng chim hót líu lo chào ngày mới bình yên và tươi đẹp."
            }]
        )

        voice_cfg = VoiceConfig(engine="edge-tts", voice="vi-VN-HoaiMyNeural")
        trans_cfg = TranslationConfig(enabled=True, source_language="auto", target_language="vi")

        with patch("backend.tts_engine.TTSEngine.convert_chapter_to_audio", new_callable=AsyncMock) as mock_tts:
            mock_tts.return_value = {
                "chapter_id": 1,
                "status": "success",
                "duration": 12.5,
                "file_path": "/fake/audio/1.mp3",
                "size_bytes": 20480
            }

            async def run():
                task_id = await self.task_manager.start_conversion_task(
                    story_id="vi_story_01",
                    chapter_ids=[1],
                    voice_config=voice_cfg,
                    translation_config=trans_cfg
                )
                
                # Wait for background task to complete
                for _ in range(50):
                    progress = self.task_manager.get_task_progress(task_id)
                    if progress and progress.status in ["completed", "failed"]:
                        break
                    await asyncio.sleep(0.05)
                return self.task_manager.get_task_progress(task_id)

            progress = asyncio.run(run())
            self.assertIsNotNone(progress)
            self.assertEqual(progress.status, "completed")
            self.assertEqual(progress.completed_chapters, 1)
            
            # Verify TTS was called with the ORIGINAL Vietnamese text
            mock_tts.assert_called_once()
            called_text = mock_tts.call_args[1]["text"]
            self.assertIn("Mặt trời vừa ló rạng", called_text)

    def test_pipeline_english_story_translates_to_vietnamese(self):
        # English story
        story = self._create_test_story(
            story_id="en_story_01",
            title="English Novel",
            chapters=[{
                "id": 101,
                "title": "Chapter 1: The Dark Forest",
                "text": "The cold wind howled across the barren moors as Eleanor walked silently toward the mysterious castle gates."
            }]
        )

        voice_cfg = VoiceConfig(engine="edge-tts", voice="vi-VN-HoaiMyNeural")
        trans_cfg = TranslationConfig(enabled=True, source_language="auto", target_language="vi")

        with patch("backend.tts_engine.TTSEngine.convert_chapter_to_audio", new_callable=AsyncMock) as mock_tts:
            mock_tts.return_value = {
                "chapter_id": 101,
                "status": "success",
                "duration": 15.0,
                "file_path": "/fake/audio/101.mp3",
                "size_bytes": 30000
            }

            async def run():
                task_id = await self.task_manager.start_conversion_task(
                    story_id="en_story_01",
                    chapter_ids=[101],
                    voice_config=voice_cfg,
                    translation_config=trans_cfg
                )

                for _ in range(50):
                    progress = self.task_manager.get_task_progress(task_id)
                    if progress and progress.status in ["completed", "failed"]:
                        break
                    await asyncio.sleep(0.05)
                return self.task_manager.get_task_progress(task_id)

            progress = asyncio.run(run())
            self.assertEqual(progress.status, "completed")
            self.assertEqual(progress.completed_chapters, 1)

            # Verify TTS received translated text
            mock_tts.assert_called_once()
            called_text = mock_tts.call_args[1]["text"]
            self.assertTrue(len(called_text) > 0)
            
            # Verify translation record was persisted in database
            record = self.db.get_chapter_translation("en_story_01", 101)
            self.assertIsNotNone(record)
            self.assertEqual(record.source_language if hasattr(record, "source_language") else record["source_language"], "en")
            self.assertEqual(record.target_language if hasattr(record, "target_language") else record["target_language"], "vi")

    def test_pipeline_translation_error_blocks_tts(self):
        # Configure translation provider to fail
        failing_provider = MockTranslationProvider(should_fail=True, fail_error_msg="OpenAI API rate limit 429")
        self.task_manager.translation_service.provider = failing_provider

        story = self._create_test_story(
            story_id="en_story_fail",
            title="Failing Translation Story",
            chapters=[{
                "id": 202,
                "title": "Chapter 2: The Failure",
                "text": "This chapter is written in English and translation will purposely fail to test error blocking."
            }]
        )

        voice_cfg = VoiceConfig(engine="edge-tts", voice="vi-VN-HoaiMyNeural")
        trans_cfg = TranslationConfig(enabled=True, source_language="auto", target_language="vi")

        with patch("backend.tts_engine.TTSEngine.convert_chapter_to_audio", new_callable=AsyncMock) as mock_tts:
            async def run():
                task_id = await self.task_manager.start_conversion_task(
                    story_id="en_story_fail",
                    chapter_ids=[202],
                    voice_config=voice_cfg,
                    translation_config=trans_cfg
                )

                for _ in range(50):
                    progress = self.task_manager.get_task_progress(task_id)
                    if progress and progress.status in ["completed", "failed"]:
                        break
                    await asyncio.sleep(0.05)
                return self.task_manager.get_task_progress(task_id)

            progress = asyncio.run(run())
            self.assertEqual(progress.status, "failed")
            self.assertIn("Lỗi dịch chương 202", progress.error)
            
            # Critical constraint: TTS must NOT be called with broken or un-translated text
            mock_tts.assert_not_called()

if __name__ == "__main__":
    unittest.main()
