import os
import re
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import soundfile as sf
import numpy as np
import json
import edge_tts
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB

from .models import VoiceConfig

logger = logging.getLogger(__name__)

# Thư mục lưu trữ audio
DATA_DIR = Path(__file__).parent / "data"
AUDIO_DIR = DATA_DIR / "audio"
SAMPLE_DIR = DATA_DIR / "samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

# ----------------- DANH SÁCH GIỌNG ĐỌC VIENEU-TTS (48kHz ONNX) -----------------
VIENEU_VOICES = [
    # Nhóm: Phong cách kể chuyện & đọc truyện (Tối ưu cho Sách nói / Audiobook)
    {"id": "Thái Sơn", "name": "Thái Sơn (Nam · Nam · Kể chuyện)", "accent": "Miền Nam", "gender": "Male", "style": "Kể chuyện", "desc": "Giọng nam miền Nam truyền cảm, ấm áp, nhịp kể lôi cuốn"},
    {"id": "Ngọc Linh", "name": "Ngọc Linh (Nữ · Bắc · Kể chuyện)", "accent": "Miền Bắc", "gender": "Female", "style": "Kể chuyện", "desc": "Giọng nữ miền Bắc ngọt ngào, sâu lắng, đậm chất văn học"},
    {"id": "Thanh Bình", "name": "Thanh Bình (Nam · Bắc · Kể chuyện)", "accent": "Miền Bắc", "gender": "Male", "style": "Kể chuyện", "desc": "Giọng nam miền Bắc đĩnh đạc, trầm hùng, diễn cảm"},
    {"id": "Thục Đoan", "name": "Thục Đoan (Nữ · Nam · Kể chuyện)", "accent": "Miền Nam", "gender": "Female", "style": "Kể chuyện", "desc": "Giọng nữ miền Nam dịu dàng, êm tai, truyền cảm sâu sắc"},
    {"id": "Mỹ Duyên", "name": "Mỹ Duyên (Nữ · Nam · Đọc truyện)", "accent": "Miền Nam", "gender": "Female", "style": "Đọc truyện", "desc": "Giọng nữ miền Nam mềm mại, diễn đọc truyện ngôn tình rất hay"},
    {"id": "Quỳnh Anh", "name": "Quỳnh Anh (Nữ · Bắc · Đọc truyện)", "accent": "Miền Bắc", "gender": "Female", "style": "Đọc truyện", "desc": "Giọng nữ miền Bắc thanh thoát, truyền cảm tự nhiên"},
    {"id": "Đức Trí", "name": "Đức Trí (Nam · Nam · Đọc truyện)", "accent": "Miền Nam", "gender": "Male", "style": "Đọc truyện", "desc": "Giọng nam miền Nam trầm ấm, chân chất, lôi cuốn"},
    {"id": "Kim Thanh", "name": "Kim Thanh (Nữ · Nam · Đọc truyện)", "accent": "Miền Nam", "gender": "Female", "style": "Đọc truyện", "desc": "Giọng nữ miền Nam trầm ấm, giàu tình cảm"},
    {"id": "Anh Khôi", "name": "Anh Khôi (Nam · Bắc · Kể chuyện)", "accent": "Miền Bắc", "gender": "Male", "style": "Kể chuyện", "desc": "Giọng nam miền Bắc uy lực, kịch tính, phong cách kể chuyện"},

    # Nhóm: Phong cách tự nhiên
    {"id": "Phạm Tuyên", "name": "Phạm Tuyên (Nam · Bắc · Tự nhiên)", "accent": "Miền Bắc", "gender": "Male", "style": "Tự nhiên", "desc": "Giọng nam tự nhiên như người thật đang trò chuyện"},
    {"id": "Trúc Ly", "name": "Trúc Ly (Nữ · Bắc · Tự nhiên)", "accent": "Miền Bắc", "gender": "Female", "style": "Tự nhiên", "desc": "Giọng nữ tự nhiên, gần gũi, biểu cảm chân thực"},
    {"id": "Xuân Vĩnh", "name": "Xuân Vĩnh (Nam · Bắc · Tự nhiên)", "accent": "Miền Bắc", "gender": "Male", "style": "Tự nhiên", "desc": "Giọng nam tự nhiên, nhịp điệu trẻ trung"},
    {"id": "Đoan Trang", "name": "Đoan Trang (Nữ · Bắc · Tự nhiên)", "accent": "Miền Bắc", "gender": "Female", "style": "Tự nhiên", "desc": "Giọng nữ thanh lịch, nhẹ nhàng, tự nhiên"},
    {"id": "Ngọc Huyền", "name": "Ngọc Huyền (Nữ · Bắc · Tự nhiên)", "accent": "Miền Bắc", "gender": "Female", "style": "Tự nhiên", "desc": "Giọng nữ miền Bắc tự nhiên, trong trẻo"},
    {"id": "Quang Sơn", "name": "Quang Sơn (Nam · Trung · Tự nhiên)", "accent": "Miền Trung", "gender": "Male", "style": "Tự nhiên", "desc": "Giọng nam miền Trung mộc mạc, gần gũi"},
    {"id": "Ngọc Trân", "name": "Ngọc Trân (Nữ · Trung · Tự nhiên)", "accent": "Miền Trung", "gender": "Female", "style": "Tự nhiên", "desc": "Giọng nữ miền Trung ngọt ngào, truyền cảm"},
    {"id": "Adam", "name": "Adam (Nam · Nam · Tự nhiên)", "accent": "Miền Nam", "gender": "Male", "style": "Tự nhiên", "desc": "Giọng nam miền Nam hiện đại, trẻ trung"},
    {"id": "Mạnh Dũng", "name": "Mạnh Dũng (Nam · Bắc · Tự nhiên)", "accent": "Miền Bắc", "gender": "Male", "style": "Tự nhiên", "desc": "Giọng nam miền Bắc khỏe khoắn, tự nhiên"},
    {"id": "Minh Quân", "name": "Minh Quân (Nam · Bắc · Tự nhiên)", "accent": "Miền Bắc", "gender": "Male", "style": "Tự nhiên", "desc": "Giọng nam miền Bắc hoạt ngôn, phong thái tự nhiên"},

    # Nhóm: Phong cách tin tức / Chuyên nghiệp
    {"id": "Minh Đức", "name": "Minh Đức (Nam · Bắc · Tin tức)", "accent": "Miền Bắc", "gender": "Male", "style": "Tin tức", "desc": "Giọng nam miền Bắc chuẩn mực phát thanh truyền hình"},
    {"id": "Mai Anh", "name": "Mai Anh (Nữ · Bắc · Tin tức)", "accent": "Miền Bắc", "gender": "Female", "style": "Tin tức", "desc": "Giọng nữ miền Bắc chuẩn thời sự, phát âm rõ ràng"},
    {"id": "Minh Triết", "name": "Minh Triết (Nam · Nam · Tin tức)", "accent": "Miền Nam", "gender": "Male", "style": "Tin tức", "desc": "Giọng nam miền Nam phát thanh chững chạc"},
    {"id": "Thùy Dung", "name": "Thùy Dung (Nữ · Nam · Tin tức)", "accent": "Miền Nam", "gender": "Female", "style": "Tin tức", "desc": "Giọng nữ miền Nam chuẩn phát thanh viên, duyên dáng"}
]

# Thẻ biểu cảm cảm xúc của VieNeu-TTS
VIENEU_EMOTION_CUES = [
    {"id": "none", "label": "Tự nhiên (Mặc định)", "tag": "", "desc": "Không chèn ngữ điệu phụ"},
    {"id": "laugh", "label": "Tươi vui [cười]", "tag": "[cười]", "desc": "Chèn tiếng cười nhẹ tươi tắn"},
    {"id": "sigh", "label": "Lắng đọng [thở dài]", "tag": "[thở dài]", "desc": "Chèn tiếng thở dài sâu sắc"},
    {"id": "throat", "label": "Trầm ngâm [hắng giọng]", "tag": "[hắng giọng]", "desc": "Chèn tiếng hắng giọng ngập ngừng"}
]

# ----------------- CẤU HÌNH EDGE-TTS MẶC ĐỊNH -----------------
EDGE_EMOTIONS = {
    "neutral": {"label": "Bình thản (Tự nhiên)", "desc": "Điềm đạm, vừa phải, phù hợp dẫn truyện và tản văn", "pitch": "+0Hz", "rate": "+0%", "volume": "+0%", "icon": "sparkles"},
    "expressive": {"label": "Truyền cảm (Ngôn tình)", "desc": "Chậm rãi, ấm áp, sâu lắng, phù hợp truyện tình cảm", "pitch": "-4Hz", "rate": "-8%", "volume": "+0%", "icon": "heart"},
    "suspense": {"label": "Hồi hộp / Kịch tính", "desc": "Dồn dập, cao trào, lôi cuốn, phù hợp trinh thám, kinh dị", "pitch": "+6Hz", "rate": "+10%", "volume": "+5%", "icon": "zap"},
    "cheerful": {"label": "Vui vẻ / Hào hứng", "desc": "Tươi tắn, nhịp nhanh, tươi sáng, phù hợp truyện hài hước", "pitch": "+14Hz", "rate": "+12%", "volume": "+5%", "icon": "smile"},
    "sad": {"label": "Trầm buồn / Sâu lắng", "desc": "Trầm và chậm, lắng đọng, phù hợp các phân cảnh bi kịch", "pitch": "-12Hz", "rate": "-14%", "volume": "-5%", "icon": "cloud-rain"},
    "whisper": {"label": "Thì thầm / Nhẹ nhàng", "desc": "Nhỏ nhẹ, thư thái, phù hợp nghe trước khi đi ngủ", "pitch": "-6Hz", "rate": "-10%", "volume": "-15%", "icon": "moon"}
}

EDGE_VOICES = [
    {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My (Nữ - Edge)", "lang": "vi-VN", "gender": "Female", "desc": "Giọng nữ miền Bắc ngọt ngào, phát âm chuẩn xác"},
    {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh (Nam - Edge)", "lang": "vi-VN", "gender": "Male", "desc": "Giọng nam miền Bắc trầm ấm, chững chạc"},
    {"id": "en-US-JennyNeural", "name": "Jenny (Nữ - English)", "lang": "en-US", "gender": "Female", "desc": "Giọng nữ tiếng Anh chuẩn Mỹ, biểu cảm tự nhiên"},
    {"id": "en-US-GuyNeural", "name": "Guy (Nam - English)", "lang": "en-US", "gender": "Male", "desc": "Giọng nam tiếng Anh chuẩn Mỹ, đĩnh đạc"}
]

class TTSEngine:
    def __init__(self):
        self._vieneu = None

    def get_vieneu(self):
        """Khởi tạo lười (lazy loading) VieNeu-TTS v3 Turbo qua ONNX"""
        if self._vieneu is None:
            try:
                import sys
                cpu_cores = os.cpu_count() or 4
                # Trên Linux/Codespaces CPU: int8 cho tốc độ nhanh gấp ~3x với tập lệnh AVX-512/VNNI
                default_prec = "int8" if sys.platform != "darwin" else "fp32"
                precision = os.environ.get("VIENEU_PRECISION", default_prec).lower()
                threads = int(os.environ.get("VIENEU_THREADS", str(cpu_cores)))

                logger.info(f"Đang khởi tạo mô hình VieNeu-TTS v3 Turbo via ONNX (precision={precision}, threads={threads})...")
                from vieneu import Vieneu
                try:
                    self._vieneu = Vieneu(mode="v3turbo", precision=precision, threads=threads)
                except Exception as pe:
                    logger.warning(f"Không thể khởi tạo với precision={precision} ({pe}), tự động chuyển sang fp32...")
                    self._vieneu = Vieneu(mode="v3turbo", precision="fp32", threads=threads)
                logger.info("VieNeu-TTS v3 Turbo đã sẵn sàng!")
            except ImportError as ie:
                logger.error(f"Thư viện vieneu chưa được cài đặt hoặc thiếu runtime ONNX: {ie}")
                raise RuntimeError("Mô hình VieNeu-TTS chưa sẵn sàng trong môi trường này. Vui lòng chọn engine Microsoft Edge Neural TTS để tiếp tục.") from ie
            except Exception as e:
                logger.error(f"Lỗi khởi tạo mô hình VieNeu-TTS: {e}")
                raise RuntimeError(f"Lỗi khi khởi tạo VieNeu-TTS: {str(e)}") from e
        return self._vieneu

    def get_presets_and_voices(self) -> Dict[str, Any]:
        """Trả về toàn bộ thông tin về 2 engine (VieNeu-TTS & Edge-TTS) và danh sách giọng đọc"""
        return {
            "engines": [
                {
                    "id": "vieneu",
                    "name": "VieNeu-TTS v3 Turbo (48kHz AI)",
                    "badge": "Khuyên dùng - 48kHz",
                    "desc": "Mô hình AI Neural tiếng Việt mới nhất, chạy On-device CPU qua ONNX, 23 giọng đọc Bắc/Trung/Nam",
                    "sample_rate": "48000 Hz"
                },
                {
                    "id": "edge-tts",
                    "name": "Microsoft Edge Neural TTS",
                    "badge": "Miễn phí",
                    "desc": "Giọng đọc đám mây của Microsoft, tốc độ nhanh, có Hoài My và Nam Minh",
                    "sample_rate": "24000 Hz"
                }
            ],
            "vieneu_voices": VIENEU_VOICES,
            "vieneu_cues": VIENEU_EMOTION_CUES,
            "edge_voices": EDGE_VOICES,
            "edge_emotions": EDGE_EMOTIONS
        }

    def chunk_text(self, text: str, max_chars: int = 1500) -> List[str]:
        """Chia nhỏ văn bản dài thành các đoạn nhỏ dưới max_chars để xử lý mượt mà"""
        text = text.strip()
        if not text:
            return []
            
        text = re.sub(r'[\r\t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        raw_paragraphs = text.split('\n\n')
        chunks: List[str] = []
        current_chunk = ""

        for p in raw_paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(p) > max_chars:
                sentences = re.split(r'(?<=[.!?…])\s+', p)
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    if len(current_chunk) + len(s) + 1 <= max_chars:
                        current_chunk = f"{current_chunk} {s}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = s
            else:
                if len(current_chunk) + len(p) + 2 <= max_chars:
                    current_chunk = f"{current_chunk}\n\n{p}".strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def generate_sample(self, text: str, config: VoiceConfig) -> str:
        """Tạo đoạn âm thanh mẫu để nghe thử cấu hình giọng đọc và biểu cảm"""
        import unicodedata
        safe_voice = unicodedata.normalize('NFKD', config.voice).encode('ascii', 'ignore').decode('ascii')
        safe_voice = re.sub(r'[^a-zA-Z0-9_-]', '', safe_voice) or "voice"
        
        if config.engine == "vieneu":
            cue_str = config.emotion_cue.strip("[]") if config.emotion_cue else "none"
            safe_cue = unicodedata.normalize('NFKD', cue_str).encode('ascii', 'ignore').decode('ascii')
            safe_cue = re.sub(r'[^a-zA-Z0-9_-]', '', safe_cue) or "none"
            sample_filename = f"sample_vieneu_{safe_voice}_{safe_cue}.mp3"
            sample_path = SAMPLE_DIR / sample_filename
            
            if sample_path.exists() and sample_path.stat().st_size > 1000:
                return f"/api/audio/sample/{sample_filename}"

            sample_text = text
            if config.emotion_cue and config.emotion_cue not in sample_text:
                sample_text = f"{config.emotion_cue} {sample_text}"

            vieneu = self.get_vieneu()
            audio_arr = await asyncio.to_thread(vieneu.infer, sample_text, voice=config.voice)
            sf.write(str(sample_path), audio_arr, 48000)
            return f"/api/audio/sample/{sample_filename}"

        else:
            # Edge-TTS
            sample_filename = f"sample_edge_{safe_voice}_{config.emotion}_{config.pitch}_{config.rate}.mp3"
            sample_path = SAMPLE_DIR / sample_filename
            
            if sample_path.exists() and sample_path.stat().st_size > 1000:
                return f"/api/audio/sample/{sample_filename}"

            communicate = edge_tts.Communicate(
                text=text,
                voice=config.voice,
                rate=config.rate,
                pitch=config.pitch,
                volume=config.volume
            )
            await communicate.save(str(sample_path))
            return f"/api/audio/sample/{sample_filename}"

    async def convert_chapter_to_audio(
        self,
        story_id: str,
        chapter_id: int,
        chapter_title: str,
        story_title: str,
        story_author: str,
        text: str,
        config: VoiceConfig,
        progress_callback: Optional[Callable[[int], None]] = None,
        check_pause_cancel: Optional[Callable[[], None]] = None
    ) -> Dict[str, Any]:
        """
        Chuyển đổi toàn bộ nội dung một chương truyện thành file MP3.
        Hỗ trợ cả VieNeu-TTS (48kHz) và Edge-TTS.
        """
        safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id)) or "default"
        dest_dir = AUDIO_DIR / safe_story_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / f"{int(chapter_id)}.mp3"

        chunks = self.chunk_text(text, max_chars=700 if config.engine == "vieneu" else 1800)
        if not chunks:
            raise ValueError(f"Chương {chapter_id} không có nội dung văn bản để chuyển đổi.")

        total_chunks = len(chunks)
        duration = 0.0

        logger.info(f"Bắt đầu chuyển đổi chương {chapter_id} [{config.engine}] ({total_chunks} đoạn)...")

        # ----------------- XỬ LÝ VIENEU-TTS (48kHz) -----------------
        if config.engine == "vieneu":
            vieneu = self.get_vieneu()
            audio_arrays: List[np.ndarray] = []

            for idx, chunk in enumerate(chunks):
                if check_pause_cancel:
                    await check_pause_cancel()

                chunk_text = chunk
                # Chèn emotion cue vào đoạn đầu tiên nếu có
                if idx == 0 and config.emotion_cue:
                    chunk_text = f"{config.emotion_cue} {chunk}"

                audio_data = await asyncio.to_thread(
                    vieneu.infer,
                    chunk_text,
                    voice=config.voice,
                    apply_watermark=False
                )
                audio_arrays.append(audio_data)

                percent = int(((idx + 1) / total_chunks) * 100)
                if progress_callback:
                    progress_callback(percent)
                await asyncio.sleep(0.01)

            full_audio = np.concatenate(audio_arrays)
            sf.write(str(dest_file), full_audio, 48000)
            duration = float(len(full_audio) / 48000.0)

        # ----------------- XỬ LÝ EDGE-TTS (24kHz) -----------------
        else:
            audio_bytes_list: List[bytes] = []
            for idx, chunk in enumerate(chunks):
                if check_pause_cancel:
                    await check_pause_cancel()

                communicate = edge_tts.Communicate(
                    text=chunk,
                    voice=config.voice,
                    rate=config.rate,
                    pitch=config.pitch,
                    volume=config.volume
                )

                chunk_bytes = b""
                async for data in communicate.stream():
                    if data['type'] == 'audio':
                        chunk_bytes += data['data']

                audio_bytes_list.append(chunk_bytes)
                percent = int(((idx + 1) / total_chunks) * 100)
                if progress_callback:
                    progress_callback(percent)
                await asyncio.sleep(0.02)

            combined_audio = b"".join(audio_bytes_list)
            with open(dest_file, "wb") as f:
                f.write(combined_audio)

        # Gắn ID3 tag metadata
        try:
            mp3_obj = MP3(str(dest_file))
            if duration == 0.0:
                duration = float(mp3_obj.info.length)
            
            try:
                tags = ID3(str(dest_file))
            except Exception:
                tags = ID3()

            tags.add(TIT2(encoding=3, text=chapter_title))
            tags.add(TPE1(encoding=3, text=story_author))
            tags.add(TALB(encoding=3, text=story_title))
            tags.save(str(dest_file))
        except Exception as e:
            logger.warning(f"Không thể gắn ID3 tag: {e}")

        file_size = dest_file.stat().st_size

        # Lưu file metadata sidecar chứa thông tin giọng đọc AI và engine
        try:
            meta_file = dest_file.with_suffix(".json")
            with open(meta_file, "w", encoding="utf-8") as mf:
                json.dump({
                    "voice": config.voice,
                    "engine": config.engine,
                    "duration": duration,
                    "size_bytes": file_size,
                    "emotion": config.emotion
                }, mf, ensure_ascii=False, indent=2)
        except Exception as me:
            logger.warning(f"Không thể lưu metadata file audio {dest_file}: {me}")

        logger.info(f"Hoàn tất chương {chapter_id} [{config.engine} - {config.voice}]: {duration:.1f}s, {file_size/1024:.1f} KB")

        return {
            "chapter_id": chapter_id,
            "file_path": str(dest_file),
            "file_name": f"{chapter_id}.mp3",
            "duration": duration,
            "size_bytes": file_size,
            "url": f"/api/audio/{story_id}/{chapter_id}",
            "audio_voice": config.voice,
            "audio_engine": config.engine
        }

    def get_audio_path(self, story_id: str, chapter_id: int) -> Optional[Path]:
        safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id)) or "default"
        path = AUDIO_DIR / safe_story_id / f"{int(chapter_id)}.mp3"
        return path if path.exists() else None

    def get_audio_metadata(self, story_id: str, chapter_id: int) -> Optional[dict]:
        """Lấy thông tin giọng đọc AI và metadata của file audio chương"""
        safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id)) or "default"
        meta_file = AUDIO_DIR / safe_story_id / f"{int(chapter_id)}.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Fallback cho các file audio cũ đã được tạo trước đó
        audio_file = AUDIO_DIR / safe_story_id / f"{int(chapter_id)}.mp3"
        if audio_file.exists():
            return {
                "voice": "Thái Sơn",
                "engine": "vieneu",
                "size_bytes": audio_file.stat().st_size
            }
        return None

