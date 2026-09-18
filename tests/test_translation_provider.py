import unittest
import asyncio
from backend.translation.prompts import PromptBuilder, CANONICAL_SYSTEM_PROMPT_V1
from backend.translation.models import BookTranslationContext, CharacterItem, GlossaryEntry, TranslationError
from backend.translation.provider import MockTranslationProvider, OpenAITranslationProvider, create_translation_provider

class TestTranslationProvider(unittest.TestCase):
    def test_canonical_prompt_builder(self):
        builder = PromptBuilder(prompt_version="literary_vi_v1")
        context = BookTranslationContext(
            story_id="story_123",
            genre="Dark Fantasy / Romance",
            tone_style="U tối, sâu lắng, văn phong quý tộc châu Âu",
            characters=[
                CharacterItem(name="Eleanor", role="Nữ chính, tiểu thư gia tộc suy tàn", gender="female", pronouns="nàng / em"),
                CharacterItem(name="Lord Arthur", role="Bá tước bí ẩn", gender="male", pronouns="chàng / ta")
            ],
            glossary=[
                GlossaryEntry(source_term="The Citadel", target_term="Thành Trì Cổ", notes="Địa danh linh thiêng"),
                GlossaryEntry(source_term="Shadowmancer", target_term="Hắc Pháp Sư")
            ]
        )

        messages = builder.build_messages(
            text="Eleanor walked into The Citadel to meet Lord Arthur.",
            source_lang="en",
            target_lang="vi",
            context=context,
            chapter_title="Chapter 1: The Dark Encounter"
        )

        self.assertEqual(len(messages), 2)
        system_msg = messages[0]["content"]
        user_msg = messages[1]["content"]

        # Verify Canonical 22 clauses are present
        self.assertIn("WATTPAD LITERARY TRANSLATION ENGINE", system_msg)
        self.assertIn("AUDIOBOOK OPTIMIZATION", system_msg)
        self.assertIn("PRONOUNS AND FORMS OF ADDRESS", system_msg)
        self.assertIn("Return ONLY the translated Vietnamese text", system_msg)

        # Verify Context injection
        self.assertIn("Dark Fantasy / Romance", user_msg)
        self.assertIn("Eleanor", user_msg)
        self.assertIn("The Citadel -> Thành Trì Cổ", user_msg)
        self.assertIn("Chapter 1: The Dark Encounter", user_msg)
        self.assertIn("Eleanor walked into The Citadel to meet Lord Arthur.", user_msg)

    def test_mock_provider_success(self):
        provider = MockTranslationProvider()
        
        async def run():
            messages = [{"role": "system", "content": "Prompt"}, {"role": "user", "content": "Hello world"}]
            result = await provider.translate(messages=messages, source_text="Hello world", model="mock-model")
            return result

        result = asyncio.run(run())
        res_text = result.translated_text if hasattr(result, 'translated_text') else result
        self.assertEqual(res_text, "Xin chào thế giới")

    def test_mock_provider_custom_mapping(self):
        custom_dict = {"Good morning, sunshine!": "Chào buổi sáng, ánh dương rực rỡ!"}
        provider = MockTranslationProvider(custom_translations=custom_dict)
        
        async def run():
            messages = [{"role": "user", "content": "Good morning, sunshine!"}]
            return await provider.translate(messages, source_text="Good morning, sunshine!")

        result = asyncio.run(run())
        self.assertEqual(result.translated_text, "Chào buổi sáng, ánh dương rực rỡ!")

    def test_mock_provider_failure_simulation(self):
        provider = MockTranslationProvider(should_fail=True, fail_error_msg="OpenAI API rate limit exceeded (429)")
        
        async def run():
            messages = [{"role": "user", "content": "Fail this text"}]
            return await provider.translate(messages, source_text="Fail this text")

        with self.assertRaises(TranslationError) as ctx:
            asyncio.run(run())
        self.assertIn("rate limit exceeded", str(ctx.exception))

    def test_provider_factory(self):
        mock = create_translation_provider("mock")
        self.assertIsInstance(mock, MockTranslationProvider)

        openai_prov = create_translation_provider("openai", api_key="sk-test-fake-key")
        self.assertIsInstance(openai_prov, OpenAITranslationProvider)
        self.assertEqual(openai_prov.api_key, "sk-test-fake-key")

if __name__ == "__main__":
    unittest.main()
