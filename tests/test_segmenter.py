import unittest
from backend.translation.segmenter import TextSegmenter

class TestTextSegmenter(unittest.TestCase):
    def setUp(self):
        self.segmenter = TextSegmenter(max_chars=300, overlap_chars=0)

    def test_short_text_single_chunk(self):
        text = "This is a short paragraph of text for testing."
        chunks = self.segmenter.split(text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].index, 0)
        self.assertEqual(chunks[0].text, text)

    def test_multi_paragraph_split(self):
        p1 = "Paragraph 1: Eleanor stepped into the ancient cathedral. The cold wind howled outside while candle lights flickered softly against the damp stone walls."
        p2 = "Paragraph 2: She noticed a shadowy figure standing silently near the grand altar, holding a mysterious leather-bound grimoire with silver runes."
        p3 = "Paragraph 3: 'Who is there?' she whispered softly, her heart pounding against her ribs as the mysterious man turned around slowly."
        
        full_text = f"{p1}\n\n{p2}\n\n{p3}"
        chunks = self.segmenter.split(full_text)
        
        self.assertTrue(len(chunks) >= 2)
        # Ensure paragraphs are cleanly preserved without mid-word truncation
        for chunk in chunks:
            self.assertTrue(len(chunk.text) <= 350)
            self.assertTrue(chunk.text.strip().endswith((".", "'", "?", "!")))

    def test_sentence_boundary_splitting(self):
        # Long single paragraph without double newlines
        long_paragraph = (
            "Eleanor arrived at the gates of the abandoned manor just as midnight struck. "
            "The iron gates creaked open with an unsettling groan as if welcoming her into a trap. "
            "She hesitated for a brief moment before taking her first step onto the overgrown stone path. "
            "A sudden gust of wind blew her hood back, revealing her determined expression in the moonlight."
        )
        
        segmenter_small = TextSegmenter(max_chars=120)
        chunks = segmenter_small.split(long_paragraph)
        
        self.assertTrue(len(chunks) > 1)
        for chunk in chunks:
            self.assertTrue(chunk.text.strip().endswith("."))

    def test_merge_chunks(self):
        translated_chunks = [
            "Đoạn văn dịch 1: Eleanor bước vào nhà thờ cổ kính.",
            "Đoạn văn dịch 2: Nàng nhìn thấy bóng người bí ẩn đứng cạnh bàn thờ.",
            "Đoạn văn dịch 3: 'Ai đó?' nàng thì thầm trong bóng đêm."
        ]
        
        merged = self.segmenter.merge(translated_chunks)
        self.assertIn("Đoạn văn dịch 1", merged)
        self.assertIn("Đoạn văn dịch 2", merged)
        self.assertIn("Đoạn văn dịch 3", merged)
        self.assertIn("\n\n", merged)

    def test_empty_and_whitespace_text(self):
        chunks = self.segmenter.split("   \n\n   ")
        self.assertEqual(len(chunks), 0)
        
        merged = self.segmenter.merge([])
        self.assertEqual(merged, "")

if __name__ == "__main__":
    unittest.main()
