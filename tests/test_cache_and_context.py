import unittest
import os
import shutil
import tempfile
from backend.database import Database
from backend.translation.cache import TranslationCache
from backend.translation.context import TranslationContextManager
from backend.translation.glossary import TranslationGlossaryManager
from backend.translation.models import TranslationResult, BookTranslationContext, CharacterItem, GlossaryEntry

class TestCacheAndContext(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_audiobook.db")
        self.db = Database(db_path=self.db_path)
        self.cache = TranslationCache(self.db)
        self.context_mgr = TranslationContextManager(self.db)
        self.glossary_mgr = TranslationGlossaryManager(self.db)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cache_key_generation(self):
        text = "  The kingdom was shrouded in twilight.  "
        h1 = self.cache.compute_hash(text, "en", "vi", "gpt-4o-mini", "literary_vi_v1")
        h2 = self.cache.compute_hash(text.strip(), "en", "vi", "gpt-4o-mini", "literary_vi_v1")
        
        # Whitespace stripping guarantees hash idempotence
        self.assertEqual(h1, h2)

        # Different model or prompt_version changes hash
        h_diff_model = self.cache.compute_hash(text, "en", "vi", "claude-3-5", "literary_vi_v1")
        h_diff_ver = self.cache.compute_hash(text, "en", "vi", "gpt-4o-mini", "literary_vi_v2")
        self.assertNotEqual(h1, h_diff_model)
        self.assertNotEqual(h1, h_diff_ver)

    def test_cache_store_and_lookup(self):
        source_text = "The silver sword gleamed in the moonlight."
        translated_text = "Thanh kiếm bạc lấp lánh dưới ánh trăng huyền ảo."
        
        res = TranslationResult(
            translated_text=translated_text,
            source_text=source_text,
            source_lang="en",
            target_lang="vi",
            provider="mock",
            model="mock-model",
            prompt_version="literary_vi_v1",
            cached=False
        )

        # 1. First lookup: Miss
        miss = self.cache.get(source_text, "en", "vi", "mock-model", "literary_vi_v1")
        self.assertIsNone(miss)

        # 2. Store in cache
        record_id = self.cache.set(
            result=res,
            story_id="test_story_1",
            chapter_id=101,
            chapter_title="Chapter 1"
        )
        self.assertTrue(record_id > 0)

        # 3. Second lookup: Hit
        hit = self.cache.get(source_text, "en", "vi", "mock-model", "literary_vi_v1")
        self.assertIsNotNone(hit)
        self.assertEqual(hit.translated_text, translated_text)
        self.assertTrue(hit.cached)

        # 4. Lookup by chapter
        chapter_res = self.cache.get_by_chapter("test_story_1", 101)
        self.assertIsNotNone(chapter_res)
        self.assertEqual(chapter_res.translated_text, translated_text)

    def test_context_management(self):
        ctx = BookTranslationContext(
            story_id="story_fantasy_99",
            genre="High Fantasy",
            tone_style="Tráng lệ, cổ điển",
            characters=[
                CharacterItem(name="Sylvia", role="Nữ pháp sư", gender="female", pronouns="nàng / muội"),
                CharacterItem(name="Rowan", role="Hiệp sĩ cận vệ", gender="male", pronouns="chàng / huynh")
            ],
            glossary=[
                GlossaryEntry(source_term="Aetherium", target_term="Tinh Thể Huyền Linh")
            ]
        )

        self.context_mgr.save_context("story_fantasy_99", ctx)

        loaded_ctx = self.context_mgr.get_context("story_fantasy_99")
        self.assertEqual(loaded_ctx.genre, "High Fantasy")
        self.assertEqual(len(loaded_ctx.characters), 2)
        self.assertEqual(loaded_ctx.characters[0].name, "Sylvia")
        self.assertEqual(loaded_ctx.characters[0].pronouns, "nàng / muội")

    def test_glossary_crud(self):
        story_id = "story_sci_fi_01"
        
        # 1. Add terms
        self.glossary_mgr.add_term(story_id, "Warp Core", "Lõi Không Gian", "Bộ phận phi thuyền")
        self.glossary_mgr.add_term(story_id, "Quantum Gate", "Cổng Lượng Tử")

        # 2. Get glossary
        terms = self.glossary_mgr.get_glossary(story_id)
        self.assertEqual(len(terms), 2)
        source_terms = [t["source_term"] if isinstance(t, dict) else t.source_term for t in terms]
        self.assertIn("Warp Core", source_terms)
        self.assertIn("Quantum Gate", source_terms)

        # 3. Delete term
        self.glossary_mgr.delete_term(story_id, "Warp Core")
        remaining = self.glossary_mgr.get_glossary(story_id)
        self.assertEqual(len(remaining), 1)
        remaining_term = remaining[0]["source_term"] if isinstance(remaining[0], dict) else remaining[0].source_term
        self.assertEqual(remaining_term, "Quantum Gate")

if __name__ == "__main__":
    unittest.main()
