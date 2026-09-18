"""
Text Segmenter for Long Chapter Processing in Wattpad AI Translation Engine
Preserves paragraph, sentence, and dialogue boundaries.
"""
import re
from typing import List
from .models import ChunkData

class TextSegmenter:
    def __init__(self, max_chunk_chars: int = 2000, min_chunk_chars: int = 300, max_chars: int = None, overlap_chars: int = 0):
        self.max_chunk_chars = max_chars if max_chars is not None else max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.overlap_chars = overlap_chars

    def split(self, text: str) -> List[ChunkData]:
        """Alias cho segment"""
        return self.segment(text)

    def segment(self, text: str) -> List[ChunkData]:
        """
        Phân đoạn văn bản dài thành các khối văn bản (chunks) mạch lạc.
        Ưu tiên ranh giới đoạn văn (\n\n), sau đó đến ranh giới câu (.!?).
        """
        text = text.strip() if text else ""
        if not text:
            return []

        # Chuẩn hóa ngắt dòng
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        paragraphs = text.split('\n\n')
        chunks: List[str] = []
        current_buffer = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Nếu một đoạn văn riêng lẻ dài hơn max_chunk_chars, chia nhỏ theo câu
            if len(para) > self.max_chunk_chars:
                sentences = [s.strip() for s in re.findall(r'.*?[.!?…]+["\'»”]?(?:\s+|$)', para) if s.strip()]
                if not sentences:
                    sentences = [para]
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_buffer) + len(sentence) + 1 <= self.max_chunk_chars:
                        current_buffer = f"{current_buffer} {sentence}".strip()
                    else:
                        if current_buffer:
                            chunks.append(current_buffer)
                        current_buffer = sentence
            else:
                if len(current_buffer) + len(para) + 2 <= self.max_chunk_chars:
                    current_buffer = f"{current_buffer}\n\n{para}".strip() if current_buffer else para
                else:
                    if current_buffer:
                        chunks.append(current_buffer)
                    current_buffer = para

        if current_buffer:
            chunks.append(current_buffer)

        chunk_data_list = []
        for idx, c in enumerate(chunks):
            is_dial = bool(re.search(r'^[“"\'—\-]', c.strip()))
            chunk_data_list.append(ChunkData(
                index=idx,
                text=c,
                char_count=len(c),
                is_dialogue=is_dial
            ))

        return chunk_data_list

    @staticmethod
    def merge(translated_chunks: List[str]) -> str:
        """Ghép các đoạn dịch lại thành văn bản hoàn chỉnh theo đúng thứ tự"""
        cleaned_chunks = [c.strip() for c in translated_chunks if c and c.strip()]
        return "\n\n".join(cleaned_chunks)
