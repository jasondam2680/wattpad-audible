import os
import sys
import re
import unicodedata
from urllib.parse import quote
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

def make_content_disposition(filename: str) -> str:
    """Tạo header Content-Disposition chuẩn RFC 6266 / RFC 5987 hỗ trợ tiếng Việt không lỗi latin-1"""
    ascii_name = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    ascii_name = re.sub(r'[^\w\s\.-]', '_', ascii_name).strip()
    if not ascii_name:
        ascii_name = 'audiobook'
    encoded_name = quote(filename.encode('utf-8'))
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded_name}'

from .models import (
    StoryInfo, ChapterInfo, VoiceConfig, TranslationConfig,
    ConvertRequest, CustomStoryRequest, SampleVoiceRequest,
    TranslationPreviewRequest, TranslationPreviewResponse,
    LoginRequest, LoginResponse, UserProfile,
    UserLibraryStory, ReadingHistoryItem, ListeningHistoryItem
)
from .database import DatabaseManager
from .scraper import WattpadScraper
from .tts_engine import TTSEngine, AUDIO_DIR, SAMPLE_DIR
from .translation import TranslationService
from .tasks import TaskManager
from .auth import UserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wattpad AI Audiobook & Translation API",
    description="Chuyển đổi truyện Wattpad thành sách nói với dịch thuật văn học AI và biểu cảm thông minh",
    version="2.0.0"
)

# Kích hoạt CORS để frontend hoặc Android app kết nối thoải mái
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo các module dịch vụ & Database SQLite chuẩn hóa
db = DatabaseManager()
scraper = WattpadScraper()
tts = TTSEngine()
translation_service = TranslationService(db)
task_manager = TaskManager(tts, scraper, db, translation_service)
user_manager = UserManager(db)

# Thư mục frontend và static
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Đảm bảo các thư mục tồn tại
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
async def on_startup():
    """Khởi động hệ thống và tự động di trú dữ liệu legacy JSON sang SQLite"""
    logger.info("Đang kiểm tra và khởi tạo hệ thống cơ sở dữ liệu SQLite...")
    try:
        db.run_auto_migration()
    except Exception as e:
        logger.error(f"Lỗi trong quá trình khởi tạo hoặc auto-migration: {e}")

class ParseRequest(BaseModel):
    url: str

# ----------------- CÁC ENDPOINT API: XÁC THỰC & NGƯỜI DÙNG -----------------

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Đăng nhập thành viên chính thức (username: jason, password: 1987)"""
    user = user_manager.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không chính xác.")
    token = user_manager.create_session(user.username)
    return LoginResponse(
        success=True,
        token=token,
        user=user,
        message=f"Chào mừng {user.name} trở lại Wattpad AI Audiobook!"
    )


@app.get("/api/auth/me")
async def get_me(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Lấy thông tin tài khoản người dùng đang đăng nhập"""
    token = authorization or x_auth_token
    user = user_manager.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập đã hết hạn hoặc không hợp lệ.")
    return {"authenticated": True, "user": user}


@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Đăng xuất tài khoản khỏi hệ thống"""
    token = authorization or x_auth_token
    if token:
        if token.startswith("Bearer "):
            token = token[7:].strip()
        user_manager.logout(token)
    return {"success": True, "message": "Đã đăng xuất thành công."}


@app.get("/api/user/library")
async def get_user_library(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Lấy toàn bộ dữ liệu Thư viện truyện, Kho Sách nói, Lịch sử đọc và Lịch sử nghe theo người dùng"""
    token = authorization or x_auth_token
    user = user_manager.verify_token(token)

    if user:
        user_data = user_manager.get_user_data(user.username)
        library_stories = user_data.get("library_stories", [])
        read_history = user_data.get("read_history", [])
        listen_history = user_data.get("listen_history", [])
    else:
        # Chế độ Khách (Guest) - Đảm bảo dữ liệu riêng tư của thành viên không bị rò rỉ
        guest_data = user_manager.get_user_data("guest")
        library_stories = guest_data.get("library_stories", [])
        read_history = guest_data.get("read_history", [])
        listen_history = guest_data.get("listen_history", [])

    # Lấy toàn bộ sách nói đã có audio từ SQLite
    audiobooks = db.get_all_audiobooks()

    return {
        "authenticated": user is not None,
        "user": user,
        "stories": library_stories,
        "audiobooks": audiobooks,
        "read_history": read_history,
        "listen_history": listen_history
    }


@app.post("/api/user/library/story")
async def add_story_to_library(story_item: UserLibraryStory, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Thêm hoặc cập nhật truyện vào thư viện cá nhân của người dùng"""
    token = authorization or x_auth_token
    user = user_manager.verify_token(token)
    uname = user.username if user else "guest"
    updated_lib = user_manager.add_library_story(uname, story_item)
    return {"success": True, "stories": updated_lib}


@app.delete("/api/user/library/story/{story_id}")
async def remove_story_from_library(story_id: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Xóa truyện khỏi thư viện người dùng"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    token = authorization or x_auth_token
    user = user_manager.verify_token(token)
    uname = user.username if user else "guest"
    updated_lib = user_manager.remove_library_story(uname, safe_story_id)
    return {"success": True, "stories": updated_lib}


@app.post("/api/user/history/read")
async def save_read_history(item: ReadingHistoryItem, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Ghi nhận lịch sử đọc chương truyện theo người dùng"""
    token = authorization or x_auth_token
    user = user_manager.verify_token(token)
    uname = user.username if user else "guest"
    hist = user_manager.record_reading_history(uname, item)
    return {"success": True, "read_history": hist}


@app.post("/api/user/history/listen")
async def save_listen_history(item: ListeningHistoryItem, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Ghi nhận lịch sử nghe sách nói (vị trí giây, thời lượng) theo người dùng"""
    token = authorization or x_auth_token
    user = user_manager.verify_token(token)
    uname = user.username if user else "guest"
    hist = user_manager.record_listening_history(uname, item)
    return {"success": True, "listen_history": hist}


@app.delete("/api/user/history/{history_type}")
async def clear_user_history(history_type: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Xóa lịch sử đọc ('read') hoặc nghe ('listen')"""
    token = authorization or x_auth_token
    user = user_manager.verify_token(token)
    uname = user.username if user else "guest"
    user_manager.clear_history(uname, history_type)
    return {"success": True, "message": f"Đã xóa lịch sử {history_type} thành công."}


# ----------------- CÁC ENDPOINT API: TRUYỆN & SÁCH NÓI -----------------

@app.get("/api/system/status")
async def get_system_status():
    """Kiểm tra tài nguyên phần cứng, số nhân CPU, chế độ lượng tử hóa int8 và mức độ chạy song song"""
    cpu_cores = os.cpu_count() or 1
    default_prec = "int8" if sys.platform != "darwin" else "fp32"
    precision = os.environ.get("VIENEU_PRECISION", default_prec).lower()
    threads = int(os.environ.get("VIENEU_THREADS", str(cpu_cores)))
    vieneu_ready = (tts._vieneu is not None)
    edge_concurrency = int(os.environ.get("EDGE_TTS_CONCURRENCY", "4"))
    vieneu_concurrency = int(os.environ.get("VIENEU_CONCURRENCY", str(max(1, cpu_cores // 2))))

    return {
        "status": "online",
        "platform": sys.platform,
        "is_codespaces": bool(os.environ.get("CODESPACES")),
        "cpu_cores": cpu_cores,
        "vieneu": {
            "is_model_loaded": vieneu_ready,
            "precision": precision,
            "threads": threads,
            "parallel_chapters": vieneu_concurrency
        },
        "edge_tts": {
            "parallel_chapters": edge_concurrency
        },
        "active_tasks": [
            {
                "task_id": t.task_id,
                "story_id": t.story_id,
                "status": t.status,
                "completed_chapters": t.completed_chapters,
                "total_chapters": t.total_chapters,
                "percent": t.current_chapter_percent
            }
            for t in task_manager.tasks.values() if t.status in ["processing", "queued", "paused"]
        ]
    }

@app.get("/api/voices")
async def get_voices():
    """Lấy danh sách giọng đọc AI và các bộ preset biểu cảm / cảm xúc"""
    return tts.get_presets_and_voices()


@app.post("/api/story/parse")
async def parse_story(req: ParseRequest):
    """Phân tích đường link Wattpad và trả về danh sách chương, ảnh bìa, tác giả, tự động nhận diện ngôn ngữ"""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Vui lòng nhập đường link hoặc ID truyện Wattpad.")

    story = scraper.get_story_info(url)
    if not story:
        raise HTTPException(
            status_code=404,
            detail="Không thể lấy thông tin truyện từ Wattpad. Vui lòng kiểm tra lại đường link hoặc thử dùng tính năng Nhập văn bản thủ công."
        )

    # Tự động nhận diện ngôn ngữ của truyện từ mô tả / tiêu đề / metadata
    det_res = translation_service.detect_language(
        f"{story.title}\n{story.description}",
        metadata_lang=str(story.language or "")
    )
    story.detected_language = det_res.source_language
    story.language_confidence = det_res.confidence

    # Kiểm tra xem các chương đã từng được chuyển đổi hoặc dịch trước đó chưa
    existing_story = task_manager.load_story(story.id)
    cached_part_map = {p.id: p for p in existing_story.parts} if existing_story else {}

    for p in story.parts:
        audio_path = tts.get_audio_path(story.id, p.id)
        if audio_path:
            p.is_converted = True
            p.audio_url = f"/api/audio/{story.id}/{p.id}"
            p.audio_size_bytes = audio_path.stat().st_size
            meta = tts.get_audio_metadata(story.id, p.id)
            cached_p = cached_part_map.get(p.id)
            p.audio_voice = (meta.get("voice") if meta else None) or (cached_p.audio_voice if cached_p else None) or "Thái Sơn"
            p.audio_engine = (meta.get("engine") if meta else None) or (cached_p.audio_engine if cached_p else None) or "vieneu"

        # Kiểm tra bản dịch đã có trong database
        trans = db.get_chapter_translation(story.id, p.id)
        if trans:
            p.is_translated = True
            p.detected_language = trans.source_language
        else:
            p.detected_language = story.detected_language

    task_manager.save_story(story)
    return story


@app.post("/api/story/custom")
async def create_custom_story(req: CustomStoryRequest):
    """Tạo truyện từ nội dung văn bản tự nhập (Tính năng dự phòng khi Wattpad chặn IP)"""
    import uuid
    story_id = f"custom_{str(uuid.uuid4())[:8]}"
    chapters_list = req.chapters if req.chapters else []
    if not chapters_list and req.text:
        chapters_list = [{"title": "Chương 1", "content": req.text}]

    parts = []
    combined_sample = ""
    for idx, chap in enumerate(chapters_list):
        cid = 1000 + idx
        content = chap.get("content", "")
        if idx == 0:
            combined_sample = content[:500]
        parts.append(ChapterInfo(
            id=cid,
            title=chap.get("title", f"Chương {idx+1}"),
            url="",
            length=len(content)
        ))

    det_res = translation_service.detect_language(
        combined_sample or req.title,
        metadata_lang=req.language
    )

    story = StoryInfo(
        id=story_id,
        title=req.title,
        author=req.author,
        cover=req.cover or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80",
        description=req.description or "Truyện được nhập trực tiếp bởi người dùng.",
        url="",
        language=det_res.source_language,
        detected_language=det_res.source_language,
        language_confidence=det_res.confidence,
        numParts=len(parts),
        parts=parts
    )

    # Lưu story vào SQLite
    task_manager.save_story(story)
    
    # Lưu nội dung text từng chương vào file text tạm
    custom_text_dir = Path(__file__).parent / "data" / "custom_texts" / story_id
    custom_text_dir.mkdir(parents=True, exist_ok=True)
    for idx, chap in enumerate(chapters_list):
        cid = 1000 + idx
        with open(custom_text_dir / f"{cid}.txt", "w", encoding="utf-8") as f:
            f.write(chap.get("content", ""))

    return story


@app.get("/api/story/{story_id}")
async def get_story(story_id: str):
    """Lấy thông tin truyện đã lưu trong cơ sở dữ liệu"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    if not safe_story_id:
        raise HTTPException(status_code=400, detail="Mã truyện không hợp lệ.")

    story = task_manager.load_story(safe_story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện trong hệ thống.")

    for p in story.parts:
        audio_path = tts.get_audio_path(story.id, p.id)
        if audio_path:
            p.is_converted = True
            p.audio_url = f"/api/audio/{story.id}/{p.id}"
            p.audio_size_bytes = audio_path.stat().st_size
            if not p.audio_voice:
                meta = tts.get_audio_metadata(story.id, p.id)
                p.audio_voice = (meta.get("voice") if meta else None) or "Thái Sơn"
                p.audio_engine = (meta.get("engine") if meta else None) or "vieneu"
        
        trans = db.get_chapter_translation(story.id, p.id)
        if trans:
            p.is_translated = True
            p.detected_language = trans.source_language
    return story


@app.get("/api/story/{story_id}/chapter/{chapter_id}")
async def get_chapter_content(story_id: str, chapter_id: int):
    """Lấy nội dung văn bản của một chương kèm metadata song ngữ và điều hướng"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    if not safe_story_id:
        raise HTTPException(status_code=400, detail="Mã truyện không hợp lệ.")

    safe_chapter_id = int(chapter_id)
    story = task_manager.load_story(safe_story_id)
    story_title = story.title if story else ""
    story_cover = story.cover if story else ""
    chapter_title = f"Chương {safe_chapter_id}"
    is_converted = False
    audio_url = None
    audio_voice = None
    prev_chapter_id = None
    next_chapter_id = None
    all_parts = []

    if story:
        for idx, p in enumerate(story.parts):
            all_parts.append({"id": p.id, "title": p.title})
            if p.id == safe_chapter_id:
                chapter_title = p.title
                if p.audio_voice:
                    audio_voice = p.audio_voice
                if idx > 0:
                    prev_chapter_id = story.parts[idx - 1].id
                if idx < len(story.parts) - 1:
                    next_chapter_id = story.parts[idx + 1].id

    audio_path = tts.get_audio_path(safe_story_id, safe_chapter_id)
    if audio_path:
        is_converted = True
        audio_url = f"/api/audio/{safe_story_id}/{safe_chapter_id}"
        if not audio_voice:
            meta = tts.get_audio_metadata(safe_story_id, safe_chapter_id)
            audio_voice = (meta.get("voice") if meta else None) or "Thái Sơn"

    # Kiểm tra custom text trước
    custom_file = Path(__file__).parent / "data" / "custom_texts" / safe_story_id / f"{safe_chapter_id}.txt"
    if custom_file.exists():
        with open(custom_file, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raw_text = scraper.get_chapter_text(safe_chapter_id)

    # Kiểm tra bản dịch đã có trong DB
    trans = db.get_chapter_translation(safe_story_id, safe_chapter_id)
    translated_text = trans.translated_text if trans else None

    # Nhận diện ngôn ngữ
    det = translation_service.detect_language(
        raw_text,
        metadata_lang=story.detected_language if story else None
    )
    detected_lang = trans.source_language if trans else det.source_language

    return {
        "story_id": safe_story_id,
        "story_title": story_title,
        "story_cover": story_cover,
        "chapter_id": safe_chapter_id,
        "chapter_title": chapter_title,
        "is_converted": is_converted,
        "audio_url": audio_url,
        "audio_voice": audio_voice,
        "prev_chapter_id": prev_chapter_id,
        "next_chapter_id": next_chapter_id,
        "parts": all_parts,
        "text": translated_text if translated_text else raw_text,
        "original_text": raw_text,
        "translated_text": translated_text,
        "detected_language": detected_lang,
        "is_translated": bool(trans),
        "translation_info": {
            "provider": trans.provider,
            "model": trans.model,
            "prompt_version": trans.prompt_version,
            "latency_ms": trans.latency_ms
        } if trans else None
    }


# ----------------- CÁC ENDPOINT API: DỊCH THUẬT & NGÔN NGỮ -----------------

@app.get("/api/languages")
async def get_supported_languages():
    """Lấy danh sách các ngôn ngữ được hỗ trợ và các tùy chọn dịch"""
    return {
        "languages": [
            {"code": "auto", "name": "Tự động nhận diện (Auto Detect)"},
            {"code": "en", "name": "Tiếng Anh (English)"},
            {"code": "vi", "name": "Tiếng Việt (Vietnamese)"}
        ],
        "source_languages": [
            {"code": "auto", "name": "Tự động nhận diện (Auto Detect)"},
            {"code": "en", "name": "Tiếng Anh (English)"},
            {"code": "vi", "name": "Tiếng Việt (Vietnamese)"}
        ],
        "target_languages": [
            {"code": "vi", "name": "Tiếng Việt (Vietnamese - Sách nói chuẩn)"}
        ],
        "models": [
            {"id": "gpt-4o-mini", "name": "OpenAI GPT-4o-mini (Mặc định)"},
            {"id": "mock", "name": "Mock Provider (Testing)"}
        ],
        "prompt_versions": [
            {"id": "literary_vi_v1", "name": "Bản dịch Văn học V1 (Tối ưu Sách nói / 22 Điều khoản)", "is_default": True}
        ]
    }


@app.post("/api/translation/preview", response_model=TranslationPreviewResponse)
async def preview_translation(req: TranslationPreviewRequest):
    """Dịch thử một đoạn văn mẫu trước khi bắt đầu tạo sách nói"""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Vui lòng nhập đoạn văn bản cần dịch thử.")

    try:
        res = await translation_service.translate_text(
            text=req.text,
            source_language=req.source_language or "auto",
            target_language=req.target_language or "vi",
            story_id=req.story_id,
            chapter_id=req.chapter_id,
            prompt_version=req.prompt_version or "literary_vi_v1"
        )
        return TranslationPreviewResponse(
            success=True,
            source_language=res.source_language,
            target_language=res.target_language,
            original_text=req.text,
            translated_text=res.translated_text,
            cached=res.cached,
            provider=res.provider,
            model=res.model,
            prompt_version=res.prompt_version,
            latency_ms=res.latency_ms
        )
    except Exception as e:
        logger.exception(f"Lỗi khi dịch thử: {e}")
        return TranslationPreviewResponse(
            success=False,
            source_language=req.source_language or "unknown",
            target_language=req.target_language or "vi",
            original_text=req.text,
            translated_text="",
            cached=False,
            provider="error",
            model="none",
            prompt_version=req.prompt_version or "literary_vi_v1",
            error=str(e)
        )


@app.get("/api/story/{story_id}/chapter/{chapter_id}/translation")
async def get_chapter_translation_record(story_id: str, chapter_id: int):
    """Lấy chi tiết bản ghi dịch thuật của một chương"""
    safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    safe_cid = int(chapter_id)
    trans = db.get_chapter_translation(safe_sid, safe_cid)
    if not trans:
        raise HTTPException(status_code=404, detail="Chương này chưa có bản dịch trong hệ thống.")
    return trans


@app.get("/api/story/{story_id}/glossary")
async def get_story_glossary(story_id: str):
    """Lấy danh sách thuật ngữ chuyên biệt của truyện"""
    safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    return {"glossary": db.get_glossary(safe_sid)}


class GlossaryItemRequest(BaseModel):
    source_term: str
    target_term: str
    notes: Optional[str] = ""

@app.post("/api/story/{story_id}/glossary")
async def add_story_glossary_term(story_id: str, item: GlossaryItemRequest):
    """Thêm hoặc cập nhật thuật ngữ dịch cho truyện"""
    safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    updated = db.add_glossary_item(safe_sid, item.source_term, item.target_term, item.notes or "")
    return {"success": True, "glossary": updated}


@app.delete("/api/story/{story_id}/glossary/{source_term}")
async def delete_story_glossary_term(story_id: str, source_term: str):
    """Xóa thuật ngữ khỏi glossary của truyện"""
    safe_sid = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    updated = db.delete_glossary_item(safe_sid, source_term)
    return {"success": True, "glossary": updated}


# ----------------- CÁC ENDPOINT API: TTS & TIẾN TRÌNH CHUYỂN ĐỔI -----------------

@app.post("/api/tts/sample")
async def generate_voice_sample(req: SampleVoiceRequest):
    """Tạo file âm thanh ngắn nghe thử giọng đọc và biểu cảm"""
    try:
        sample_url = await tts.generate_sample(req.text or "Xin chào các bạn độc giả.", req.voice_config)
        return {"sample_url": sample_url}
    except Exception as e:
        logger.exception(f"Lỗi tạo audio mẫu: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo giọng đọc thử: {str(e)}")


@app.post("/api/tts/convert")
async def start_conversion(req: ConvertRequest):
    """Bắt đầu hoặc tiếp tục tiến trình chuyển đổi các chương đã chọn thành sách nói"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(req.story_id))
    if not safe_story_id:
        raise HTTPException(status_code=400, detail="Mã truyện không hợp lệ.")

    story = task_manager.load_story(safe_story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Truyện chưa được phân tích hoặc không tồn tại.")

    if not req.chapter_ids:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất một chương để chuyển đổi.")

    task_id = await task_manager.start_conversion_task(
        story_id=safe_story_id,
        chapter_ids=req.chapter_ids,
        voice_config=req.voice_config,
        translation_config=req.translation_config,
        device_id=req.device_id,
        user_id=req.user_id
    )
    task = task_manager.get_task(task_id)
    is_resumed = getattr(task, "resumed", False) if task else False
    msg = "Tiếp tục phiên chuyển đổi trước đó cho đến khi hoàn thành." if is_resumed else "Tiến trình chuyển đổi đã bắt đầu thành công."

    return {
        "task_id": task_id,
        "resumed": is_resumed,
        "status": task.status if task else "processing",
        "current_phase": getattr(task, "current_phase", "queued") if task else "queued",
        "message": msg
    }


@app.get("/api/tts/active-task")
async def get_active_task(
    device_id: str = Query(..., description="Mã thiết bị đầu cuối"),
    story_id: Optional[str] = Query(None, description="Mã truyện (tùy chọn)")
):
    """Lấy phiên chuyển đổi đang chạy hoặc dang dở của thiết bị để tiếp tục tự động"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id)) if story_id else None
    task = task_manager.get_active_task_for_device(device_id, safe_story_id)
    if not task:
        return {"has_active_task": False, "task": None}
    return {"has_active_task": True, "task": task}


@app.get("/api/tts/task/{task_id}")
async def get_task_status(task_id: str):
    """Xem tiến trình chuyển đổi của tác vụ"""
    safe_task_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(task_id))
    task = task_manager.get_task(safe_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy tác vụ.")
    return task


@app.post("/api/tts/task/{task_id}/pause")
async def pause_task(task_id: str):
    """Tạm dừng tác vụ đang chuyển đổi"""
    safe_task_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(task_id))
    success = task_manager.pause_task(safe_task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể tạm dừng tác vụ (chỉ áp dụng khi đang xử lý).")
    return {"status": "paused", "message": f"Tác vụ {safe_task_id} đã được tạm dừng."}


@app.post("/api/tts/task/{task_id}/resume")
async def resume_task(task_id: str):
    """Tiếp tục tác vụ đã tạm dừng"""
    safe_task_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(task_id))
    success = task_manager.resume_task(safe_task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể tiếp tục tác vụ (chỉ áp dụng khi đang tạm dừng).")
    return {"status": "processing", "message": f"Tác vụ {safe_task_id} đã tiếp tục chạy."}


@app.post("/api/tts/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Hủy bỏ tác vụ chuyển đổi"""
    safe_task_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(task_id))
    success = task_manager.cancel_task(safe_task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể hủy tác vụ này.")
    return {"status": "cancelled", "message": f"Tác vụ {safe_task_id} đã bị hủy bỏ."}


@app.get("/api/audio/sample/{filename}")
async def get_sample_audio(filename: str):
    """Lấy file âm thanh mẫu (ngăn chặn Path Traversal)"""
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', str(filename))
    file_path = SAMPLE_DIR / safe_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Mẫu âm thanh không tồn tại.")
    return FileResponse(str(file_path), media_type="audio/mpeg")


@app.get("/api/audio/{story_id}/download-all")
async def download_all_zip(story_id: str):
    """Tải toàn bộ các chương đã chuyển đổi dưới dạng file ZIP"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    if not safe_story_id:
        raise HTTPException(status_code=400, detail="Mã truyện không hợp lệ.")

    zip_path = task_manager.create_story_zip(safe_story_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=404, detail="Chưa có chương nào được chuyển đổi thành audio để tải về.")
        
    story = task_manager.load_story(safe_story_id)
    story_title = story.title if story else safe_story_id
    clean_title = re.sub(r'[/\\:*?"<>|]', '_', story_title).strip()
    download_name = f"{clean_title or safe_story_id} - Sách nói AI.zip"

    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        headers={"Content-Disposition": make_content_disposition(download_name)}
    )


@app.get("/api/audio/{story_id}/{chapter_id}")
async def stream_audio(story_id: str, chapter_id: int):
    """Phát trực tuyến (Stream) file âm thanh MP3 của chương truyện"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    safe_chapter_id = int(chapter_id)

    audio_path = tts.get_audio_path(safe_story_id, safe_chapter_id)
    if not audio_path or not audio_path.exists():
        raise HTTPException(status_code=404, detail="File âm thanh của chương này chưa được tạo.")
    return FileResponse(
        str(audio_path),
        media_type="audio/mpeg",
        filename=f"{safe_chapter_id}.mp3"
    )


@app.get("/api/audio/{story_id}/{chapter_id}/download")
async def download_audio(story_id: str, chapter_id: int):
    """Tải file MP3 của chương truyện về máy"""
    safe_story_id = re.sub(r'[^a-zA-Z0-9_-]', '', str(story_id))
    safe_chapter_id = int(chapter_id)

    audio_path = tts.get_audio_path(safe_story_id, safe_chapter_id)
    if not audio_path or not audio_path.exists():
        raise HTTPException(status_code=404, detail="File âm thanh không tồn tại.")

    story = task_manager.load_story(safe_story_id)
    chapter_title = f"Chương_{safe_chapter_id}"
    if story:
        part = next((p for p in story.parts if p.id == safe_chapter_id), None)
        if part and part.title:
            chapter_title = part.title

    clean_chapter_title = re.sub(r'[/\\:*?"<>|]', '_', chapter_title).strip()
    download_name = f"{clean_chapter_title or f'Chuong_{safe_chapter_id}'}.mp3"

    return FileResponse(
        str(audio_path),
        media_type="audio/mpeg",
        headers={"Content-Disposition": make_content_disposition(download_name)}
    )


# ----------------- TÍCH HỢP PWA & GIAO DIỆN WEB -----------------

@app.get("/manifest.json")
async def get_manifest():
    manifest_file = FRONTEND_DIR / "manifest.json"
    if manifest_file.exists():
        return FileResponse(str(manifest_file), media_type="application/json")
    raise HTTPException(status_code=404, detail="Manifest not found")


@app.get("/sw.js")
async def get_service_worker():
    sw_file = FRONTEND_DIR / "sw.js"
    if sw_file.exists():
        return FileResponse(str(sw_file), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Service worker not found")


# Gắn thư mục static cho assets (css, js, icons)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Wattpad AI Audiobook API is running. Giao diện frontend đang được chuẩn bị."}


@app.get("/reader")
@app.get("/reader.html")
async def serve_reader():
    reader_file = FRONTEND_DIR / "reader.html"
    if reader_file.exists():
        return FileResponse(str(reader_file))
    raise HTTPException(status_code=404, detail="Giao diện đọc truyện chưa sẵn sàng.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
