"""
Language Detection Engine for Wattpad AI Audiobook Localization
Supports Vietnamese, English, and unknown/mixed language detection.
"""
import re
from typing import Optional, Tuple
from .models import LanguageDetectionResult

VIETNAMESE_CHARS_REGEX = re.compile(r'[àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ]', re.IGNORECASE)

ENGLISH_COMMON_WORDS = {
    "the", "and", "that", "have", "for", "not", "with", "you", "this", "but", "his", "from",
    "they", "say", "her", "she", "will", "one", "all", "would", "there", "their", "what",
    "out", "about", "who", "get", "which", "when", "make", "can", "like", "time", "just",
    "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them",
    "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"
}

VIETNAMESE_COMMON_WORDS = {
    "và", "của", "là", "có", "được", "trong", "đã", "cho", "không", "với", "các", "người",
    "khi", "những", "này", "về", "một", "đến", "thì", "đó", "ra", "lại", "tại", "tôi",
    "anh", "cô", "em", "ông", "bà", "hắn", "nàng", "chúng", "mình", "nhưng", "như", "đang",
    "sẽ", "phải", "được", "nhiều", "hơn", "rất", "biết", "thấy", "làm", "đi", "nói"
}

class LanguageDetector:
    @staticmethod
    def detect_language(text: str, metadata_lang: Optional[str] = None) -> LanguageDetectionResult:
        """
        Xác định ngôn ngữ của văn bản kết hợp phân tích văn bản thực tế và metadata gợi ý.
        Trả về LanguageDetectionResult chứa source_language ('vi', 'en', 'unknown'), confidence (0.0 - 1.0).
        """
        clean_text = text.strip() if text else ""
        if not clean_text or len(clean_text) < 10:
            if metadata_lang:
                normalized_meta = metadata_lang.strip().lower()
                if normalized_meta in ["vi", "vietnamese", "tiếng việt"]:
                    return LanguageDetectionResult(source_language="vi", confidence=0.7, detection_method="metadata")
                elif normalized_meta in ["en", "english", "tiếng anh"]:
                    return LanguageDetectionResult(source_language="en", confidence=0.7, detection_method="metadata")
            return LanguageDetectionResult(source_language="unknown", confidence=0.0, detection_method="heuristic")

        # 1. Đếm ký tự dấu tiếng Việt
        vi_chars = VIETNAMESE_CHARS_REGEX.findall(clean_text)
        vi_char_count = len(vi_chars)
        total_alpha = sum(1 for c in clean_text if c.isalpha())
        
        # Nếu có metadata hint và văn bản ngắn (< 50 chars), ưu tiên metadata hint
        if metadata_lang and len(clean_text) < 50:
            normalized_meta = metadata_lang.strip().lower()
            if normalized_meta in ["vi", "vietnamese", "tiếng việt"]:
                return LanguageDetectionResult(source_language="vi", confidence=0.85, detection_method="metadata_hint")
            elif normalized_meta in ["en", "english", "tiếng anh"] and vi_char_count == 0:
                return LanguageDetectionResult(source_language="en", confidence=0.85, detection_method="metadata_hint")

        vi_char_ratio = (vi_char_count / max(1, total_alpha))

        # 2. Phân tích token từ vựng
        words = re.findall(r'\b\w+\b', clean_text.lower())
        total_words = len(words)
        if total_words == 0:
            return LanguageDetectionResult(source_language="unknown", confidence=0.0, detection_method="heuristic")

        en_matches = sum(1 for w in words if w in ENGLISH_COMMON_WORDS)
        vi_word_matches = sum(1 for w in words if w in VIETNAMESE_COMMON_WORDS)

        en_word_ratio = en_matches / total_words
        vi_word_ratio = vi_word_matches / total_words

        # Quyết định dựa trên tỷ lệ
        if vi_char_ratio > 0.03 or vi_word_ratio > 0.06:
            confidence = min(1.0, 0.7 + vi_char_ratio * 3 + vi_word_ratio)
            return LanguageDetectionResult(
                source_language="vi",
                confidence=round(confidence, 2),
                detection_method="analysis"
            )

        if en_word_ratio > 0.05 and vi_char_count == 0:
            confidence = min(1.0, 0.75 + en_word_ratio * 2)
            return LanguageDetectionResult(
                source_language="en",
                confidence=round(confidence, 2),
                detection_method="analysis"
            )

        if vi_char_count == 0 and en_word_ratio > 0.02:
            return LanguageDetectionResult(
                source_language="en",
                confidence=0.8,
                detection_method="analysis"
            )

        # Fallback vào metadata nếu văn bản ngắn hoặc không rõ ràng
        if metadata_lang:
            m = metadata_lang.strip().lower()
            if m in ["vi", "vietnamese"]:
                return LanguageDetectionResult(source_language="vi", confidence=0.6, detection_method="metadata_fallback")
            if m in ["en", "english"]:
                return LanguageDetectionResult(source_language="en", confidence=0.6, detection_method="metadata_fallback")

        return LanguageDetectionResult(
            source_language="unknown",
            confidence=0.3,
            detection_method="heuristic"
        )

    def detect(self, text: str, metadata_lang_hint: Optional[str] = None) -> LanguageDetectionResult:
        """Alias cho detect_language tương thích cả instance và static call"""
        return self.detect_language(text, metadata_lang=metadata_lang_hint)

    def should_translate(self, text: str, metadata_lang: Optional[str] = None) -> bool:
        """Trả về True nếu văn bản là tiếng Anh/khác và cần dịch sang tiếng Việt"""
        res = self.detect_language(text, metadata_lang=metadata_lang)
        return res.requires_translation
