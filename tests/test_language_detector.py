import unittest
from backend.translation.detector import LanguageDetector

class TestLanguageDetector(unittest.TestCase):
    def setUp(self):
        self.detector = LanguageDetector()

    def test_detect_vietnamese_standard(self):
        text = "Đêm mùa thu lạnh buốt, những cơn gió rít qua rặng cây trơ trụi lá. Eleanor khẽ kéo chiếc áo khoác len lại gần hơn."
        result = self.detector.detect(text)
        self.assertEqual(result.detected_language, "vi")
        self.assertTrue(result.confidence > 0.8)
        self.assertFalse(result.requires_translation)
        self.assertFalse(self.detector.should_translate(text))

    def test_detect_english_standard(self):
        text = "The cold autumn wind howled through the barren trees as Eleanor pulled her woolen coat tighter around her shivering shoulders. She walked through the dark forest alone."
        result = self.detector.detect(text)
        self.assertEqual(result.detected_language, "en")
        self.assertTrue(result.confidence > 0.8)
        self.assertTrue(result.requires_translation)
        self.assertTrue(self.detector.should_translate(text))

    def test_detect_short_texts(self):
        vi_short = "Xin chào các bạn"
        en_short = "Hello and welcome to the world"
        
        res_vi = self.detector.detect(vi_short)
        res_en = self.detector.detect(en_short)
        
        self.assertEqual(res_vi.detected_language, "vi")
        self.assertEqual(res_en.detected_language, "en")

    def test_detect_empty_or_whitespace(self):
        res = self.detector.detect("   \n\t  ")
        self.assertEqual(res.detected_language, "unknown")
        self.assertFalse(res.requires_translation)

    def test_detect_with_metadata_hint(self):
        # When text is ambiguous or unaccented, hint is used
        text = "Chapter 1: The Beginning"
        res_with_vi_hint = self.detector.detect(text, metadata_lang_hint="vi")
        self.assertEqual(res_with_vi_hint.detected_language, "vi")
        
        res_without_hint = self.detector.detect(text)
        self.assertEqual(res_without_hint.detected_language, "en")

    def test_mixed_text_dominant_language(self):
        # Vietnamese text with a few English loan words/terms (e.g. "CEO", "smartphone")
        mixed_vi = "Vị CEO trẻ tuổi bước ra khỏi chiếc xe sang trọng, cầm trên tay chiếc smartphone đời mới và mỉm cười chào đón đối tác."
        res = self.detector.detect(mixed_vi)
        self.assertEqual(res.detected_language, "vi")
        self.assertFalse(res.requires_translation)

if __name__ == "__main__":
    unittest.main()
