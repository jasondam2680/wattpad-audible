import os
import re
import json
import time
import sqlite3
import hashlib
import secrets
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from .models import (
    StoryInfo, ChapterInfo, TaskProgress,
    UserProfile, UserLibraryStory, ReadingHistoryItem, ListeningHistoryItem
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "database.sqlite"
AUDIO_DIR = DATA_DIR / "audio"

import hmac

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Băm mật khẩu bằng PBKDF2-HMAC-SHA256 với Salt ngẫu nhiên 16 bytes"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100_000
    ).hex()
    return hashed, salt

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Xác minh tính đúng đắn của mật khẩu với stored hash"""
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, stored_hash)


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
        """Context manager quản lý kết nối SQLite thread-safe với WAL mode"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.exception(f"Lỗi database transaction: {e}")
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Khởi tạo schema bảng và chỉ mục nếu chưa tồn tại"""
        with self.get_connection() as conn:
            conn.executescript("""
            -- 1. Bảng người dùng (Users)
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Thành viên',
                avatar TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );

            -- 2. Bảng truyện (Stories)
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                cover TEXT NOT NULL,
                description TEXT DEFAULT '',
                url TEXT DEFAULT '',
                language TEXT DEFAULT 'vi',
                num_parts INTEGER DEFAULT 0,
                is_custom INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            -- 3. Bảng chương truyện (Chapters)
            CREATE TABLE IF NOT EXISTS chapters (
                composite_id TEXT PRIMARY KEY,
                story_id TEXT NOT NULL,
                chapter_id INTEGER NOT NULL,
                chapter_index INTEGER DEFAULT 0,
                title TEXT NOT NULL,
                url TEXT DEFAULT '',
                length INTEGER DEFAULT 0,
                create_date TEXT,
                is_converted INTEGER DEFAULT 0,
                audio_url TEXT,
                audio_duration REAL DEFAULT 0.0,
                audio_size_bytes INTEGER DEFAULT 0,
                audio_voice TEXT,
                audio_engine TEXT,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
            );

            -- 4. Bảng thư viện người dùng (User Library)
            CREATE TABLE IF NOT EXISTS user_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                story_id TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                cover TEXT NOT NULL,
                num_parts INTEGER DEFAULT 0,
                url TEXT DEFAULT '',
                is_custom INTEGER DEFAULT 0,
                added_at REAL NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
                UNIQUE(username, story_id)
            );

            -- 5. Bảng lịch sử đọc (Read History)
            CREATE TABLE IF NOT EXISTS read_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                story_id TEXT NOT NULL,
                story_title TEXT,
                story_cover TEXT,
                chapter_id INTEGER NOT NULL,
                chapter_title TEXT NOT NULL,
                progress_percent INTEGER DEFAULT 0,
                timestamp REAL NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            );

            -- 6. Bảng lịch sử nghe (Listen History)
            CREATE TABLE IF NOT EXISTS listen_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                story_id TEXT NOT NULL,
                story_title TEXT,
                story_cover TEXT,
                chapter_id INTEGER NOT NULL,
                chapter_title TEXT NOT NULL,
                current_time REAL DEFAULT 0.0,
                duration REAL DEFAULT 0.0,
                timestamp REAL NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            );

            -- 7. Bảng tác vụ chuyển đổi (Tasks)
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                story_id TEXT NOT NULL,
                user_id TEXT,
                device_id TEXT,
                total_chapters INTEGER DEFAULT 0,
                completed_chapters INTEGER DEFAULT 0,
                current_chapter_title TEXT DEFAULT '',
                current_chapter_percent INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                can_pause INTEGER DEFAULT 1,
                error TEXT,
                resumed INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            -- Chỉ mục tối ưu truy vấn
            CREATE INDEX IF NOT EXISTS idx_chapters_story_id ON chapters(story_id);
            CREATE INDEX IF NOT EXISTS idx_user_library_user ON user_library(username);
            CREATE INDEX IF NOT EXISTS idx_read_hist_user ON read_history(username, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_listen_hist_user ON listen_history(username, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_tasks_device ON tasks(device_id, story_id);
            """)
        logger.info("Cơ sở dữ liệu SQLite đã được khởi tạo thành công tại: %s", self.db_path)

    # ----------------- TỰ ĐỘNG DI TRÚ TỪ DỮ LIỆU JSON CŨ -----------------

    def run_auto_migration(self):
        """
        Quét và di trú dữ liệu hiện có từ các file JSON trong backend/data/ vào SQLite.
        Chỉ thực hiện một lần khi dữ liệu chưa được nạp.
        """
        logger.info("Bắt đầu kiểm tra và tự động di trú dữ liệu legacy JSON sang SQLite...")
        now = time.time()

        # 1. Di trú User mặc định (jason / 1987) và file jason.json nếu có
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE username = 'jason'")
            if cur.fetchone()[0] == 0:
                user_json_file = DATA_DIR / "users" / "jason.json"
                name = "Jason"
                role = "Thành viên chính thức"
                avatar = "J"
                lib_stories = []
                read_hist = []
                listen_hist = []

                if user_json_file.exists():
                    try:
                        with open(user_json_file, "r", encoding="utf-8") as f:
                            udata = json.load(f)
                            name = udata.get("name", name)
                            role = udata.get("role", role)
                            avatar = udata.get("avatar", avatar)
                            lib_stories = udata.get("library_stories", [])
                            read_hist = udata.get("read_history", [])
                            listen_hist = udata.get("listen_history", [])
                    except Exception as e:
                        logger.warning(f"Lỗi đọc jason.json: {e}")

                pwd_hash, salt = hash_password("1987")
                cur.execute("""
                    INSERT INTO users (username, password_hash, salt, name, role, avatar, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("jason", pwd_hash, salt, name, role, avatar, now))

                # Di trú thư viện truyện của jason
                for s in lib_stories:
                    sid = str(s.get("id"))
                    cur.execute("""
                        INSERT OR IGNORE INTO user_library (username, story_id, title, author, cover, num_parts, url, is_custom, added_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "jason", sid, s.get("title", "Truyện"), s.get("author", "Tác giả"),
                        s.get("cover", ""), s.get("numParts", 0), s.get("url", ""),
                        1 if s.get("is_custom") else 0, s.get("added_at", now)
                    ))

                # Di trú lịch sử đọc
                for rh in read_hist:
                    cur.execute("""
                        INSERT INTO read_history (username, story_id, story_title, story_cover, chapter_id, chapter_title, progress_percent, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "jason", str(rh.get("story_id")), rh.get("story_title"), rh.get("story_cover"),
                        rh.get("chapter_id", 0), rh.get("chapter_title", ""),
                        rh.get("progress_percent", 0), rh.get("timestamp", now)
                    ))

                # Di trú lịch sử nghe
                for lh in listen_hist:
                    cur.execute("""
                        INSERT INTO listen_history (username, story_id, story_title, story_cover, chapter_id, chapter_title, current_time, duration, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "jason", str(lh.get("story_id")), lh.get("story_title"), lh.get("story_cover"),
                        lh.get("chapter_id", 0), lh.get("chapter_title", ""),
                        lh.get("current_time", 0.0), lh.get("duration", 0.0),
                        lh.get("timestamp", now)
                    ))
                logger.info("Đã di trú tài khoản thành viên 'jason' cùng thư viện và lịch sử.")

        # 2. Di trú danh sách truyện từ stories/*.json
        stories_dir = DATA_DIR / "stories"
        if stories_dir.exists():
            with self.get_connection() as conn:
                cur = conn.cursor()
                for sfile in stories_dir.glob("*.json"):
                    try:
                        with open(sfile, "r", encoding="utf-8") as f:
                            sdata = json.load(f)
                            sid = str(sdata.get("id"))
                            cur.execute("SELECT id FROM stories WHERE id = ?", (sid,))
                            if cur.fetchone():
                                continue

                            is_custom = 1 if sid.startswith("custom_") else 0
                            cur.execute("""
                                INSERT OR REPLACE INTO stories (id, title, author, cover, description, url, language, num_parts, is_custom, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                sid, sdata.get("title", ""), sdata.get("author", ""),
                                sdata.get("cover", ""), sdata.get("description", ""),
                                sdata.get("url", ""), str(sdata.get("language", "vi")),
                                sdata.get("numParts", 0), is_custom, now, now
                            ))

                            parts = sdata.get("parts", [])
                            for idx, p in enumerate(parts):
                                cid = p.get("id")
                                comp_id = f"{sid}_{cid}"
                                # Kiểm tra file audio thực tế
                                audio_path = AUDIO_DIR / sid / f"{cid}.mp3"
                                is_conv = 1 if (audio_path.exists() and audio_path.stat().st_size > 1000) else (1 if p.get("is_converted") else 0)
                                a_url = f"/api/audio/{sid}/{cid}" if is_conv else None
                                a_size = audio_path.stat().st_size if (is_conv and audio_path.exists()) else (p.get("audio_size_bytes") or 0)
                                a_dur = p.get("audio_duration") or 0.0

                                # Đọc sidecar metadata nếu có
                                meta_path = AUDIO_DIR / sid / f"{cid}.json"
                                a_voice = p.get("audio_voice")
                                a_eng = p.get("audio_engine")
                                if meta_path.exists():
                                    try:
                                        with open(meta_path, "r", encoding="utf-8") as mf:
                                            mdata = json.load(mf)
                                            a_voice = mdata.get("voice", a_voice)
                                            a_eng = mdata.get("engine", a_eng)
                                            a_dur = mdata.get("duration", a_dur)
                                    except Exception:
                                        pass

                                cur.execute("""
                                    INSERT OR REPLACE INTO chapters (
                                        composite_id, story_id, chapter_id, chapter_index,
                                        title, url, length, create_date, is_converted,
                                        audio_url, audio_duration, audio_size_bytes, audio_voice, audio_engine
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    comp_id, sid, cid, idx,
                                    p.get("title", f"Chương {cid}"), p.get("url", ""),
                                    p.get("length", 0), p.get("createDate"),
                                    is_conv, a_url, a_dur, a_size,
                                    a_voice or ("Thái Sơn" if is_conv else None),
                                    a_eng or ("vieneu" if is_conv else None)
                                ))
                    except Exception as se:
                        logger.warning(f"Lỗi di trú file truyện {sfile}: {se}")

        # 3. Di trú các tasks cũ từ tasks/*.json
        tasks_dir = DATA_DIR / "tasks"
        if tasks_dir.exists():
            with self.get_connection() as conn:
                cur = conn.cursor()
                for tfile in tasks_dir.glob("*.json"):
                    try:
                        with open(tfile, "r", encoding="utf-8") as f:
                            tdata = json.load(f)
                            tid = tdata.get("task_id")
                            cur.execute("SELECT task_id FROM tasks WHERE task_id = ?", (tid,))
                            if cur.fetchone():
                                continue

                            cur.execute("""
                                INSERT OR REPLACE INTO tasks (
                                    task_id, story_id, user_id, device_id, total_chapters,
                                    completed_chapters, current_chapter_title, current_chapter_percent,
                                    status, can_pause, error, resumed, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                tid, tdata.get("story_id", ""), tdata.get("user_id"),
                                tdata.get("device_id"), tdata.get("total_chapters", 0),
                                tdata.get("completed_chapters", 0), tdata.get("current_chapter_title", ""),
                                tdata.get("current_chapter_percent", 0), tdata.get("status", "completed"),
                                1 if tdata.get("can_pause", True) else 0, tdata.get("error"),
                                1 if tdata.get("resumed", False) else 0, now, now
                            ))
                    except Exception as te:
                        logger.warning(f"Lỗi di trú file task {tfile}: {te}")

        logger.info("Hoàn tất di trú dữ liệu legacy JSON sang SQLite an toàn!")

    # ----------------- REPOSITORY: TRUYỆN & CHƯƠNG -----------------

    def save_story(self, story: StoryInfo):
        """Lưu hoặc cập nhật toàn bộ thông tin truyện và danh sách chương vào DB"""
        now = time.time()
        sid = str(story.id)
        is_custom = 1 if sid.startswith("custom_") else 0

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO stories (id, title, author, cover, description, url, language, num_parts, is_custom, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM stories WHERE id = ?), ?), ?)
            """, (
                sid, story.title, story.author, story.cover, story.description,
                story.url, str(story.language or "vi"), story.numParts, is_custom,
                sid, now, now
            ))

            for idx, p in enumerate(story.parts):
                comp_id = f"{sid}_{p.id}"
                cur.execute("""
                    INSERT OR REPLACE INTO chapters (
                        composite_id, story_id, chapter_id, chapter_index,
                        title, url, length, create_date, is_converted,
                        audio_url, audio_duration, audio_size_bytes, audio_voice, audio_engine
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    comp_id, sid, p.id, idx,
                    p.title, p.url, p.length or 0, p.createDate,
                    1 if p.is_converted else 0, p.audio_url,
                    p.audio_duration or 0.0, p.audio_size_bytes or 0,
                    p.audio_voice, p.audio_engine
                ))

    def get_story(self, story_id: str) -> Optional[StoryInfo]:
        """Tải thông tin truyện và toàn bộ danh sách chương từ DB"""
        sid = str(story_id)
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM stories WHERE id = ?", (sid,))
            srow = cur.fetchone()
            if not srow:
                return None

            cur.execute("SELECT * FROM chapters WHERE story_id = ? ORDER BY chapter_index ASC", (sid,))
            crows = cur.fetchall()
            parts: List[ChapterInfo] = []
            for c in crows:
                parts.append(ChapterInfo(
                    id=c["chapter_id"],
                    title=c["title"],
                    url=c["url"] or "",
                    length=c["length"] or 0,
                    createDate=c["create_date"],
                    is_converted=bool(c["is_converted"]),
                    audio_url=c["audio_url"],
                    audio_duration=c["audio_duration"],
                    audio_size_bytes=c["audio_size_bytes"],
                    audio_voice=c["audio_voice"],
                    audio_engine=c["audio_engine"]
                ))

            return StoryInfo(
                id=srow["id"],
                title=srow["title"],
                author=srow["author"],
                cover=srow["cover"],
                description=srow["description"] or "",
                url=srow["url"] or "",
                language=srow["language"] or "vi",
                numParts=srow["num_parts"] or len(parts),
                parts=parts
            )

    def update_chapter_audio(
        self,
        story_id: str,
        chapter_id: int,
        duration: float,
        size_bytes: int,
        voice: Optional[str] = None,
        engine: Optional[str] = None
    ):
        """Cập nhật trạng thái chuyển đổi sách nói của một chương"""
        sid = str(story_id)
        comp_id = f"{sid}_{chapter_id}"
        audio_url = f"/api/audio/{sid}/{chapter_id}"
        now = time.time()

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE chapters
                SET is_converted = 1,
                    audio_url = ?,
                    audio_duration = ?,
                    audio_size_bytes = ?,
                    audio_voice = COALESCE(?, audio_voice),
                    audio_engine = COALESCE(?, audio_engine)
                WHERE composite_id = ?
            """, (audio_url, duration, size_bytes, voice, engine, comp_id))

            cur.execute("UPDATE stories SET updated_at = ? WHERE id = ?", (now, sid))

    def get_all_audiobooks(self) -> List[Dict[str, Any]]:
        """Lấy danh sách toàn bộ các truyện đã có ít nhất một chương audio hoàn thiện"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.id, s.title, s.author, s.cover, s.num_parts, s.url,
                       COUNT(c.composite_id) as converted_count,
                       MIN(c.chapter_id) as first_audio_chapter_id
                FROM stories s
                JOIN chapters c ON s.id = c.story_id
                WHERE c.is_converted = 1
                GROUP BY s.id
                ORDER BY s.updated_at DESC
            """)
            rows = cur.fetchall()
            results = []
            for r in rows:
                sid = r["id"]
                # Lấy danh sách chi tiết các chương audio
                cur.execute("""
                    SELECT chapter_id as id, title, audio_duration as duration
                    FROM chapters
                    WHERE story_id = ? AND is_converted = 1
                    ORDER BY chapter_index ASC
                """, (sid,))
                chap_rows = cur.fetchall()
                results.append({
                    "id": sid,
                    "title": r["title"],
                    "author": r["author"],
                    "cover": r["cover"],
                    "numParts": r["num_parts"],
                    "converted_count": r["converted_count"],
                    "first_audio_chapter_id": r["first_audio_chapter_id"],
                    "url": r["url"] or "",
                    "audio_chapters": [dict(cr) for cr in chap_rows]
                })
            return results

    # ----------------- REPOSITORY: NGƯỜI DÙNG & XÁC THỰC -----------------

    def create_user(self, username: str, password: str, name: str, role: str = "Thành viên", avatar: str = "") -> bool:
        """Tạo người dùng mới với mật khẩu được băm an toàn"""
        uname = username.strip().lower()
        pwd_hash, salt = hash_password(password)
        now = time.time()
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (username, password_hash, salt, name, role, avatar, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (uname, pwd_hash, salt, name, role, avatar or uname[:1].upper(), now))
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username: str, password: str) -> Optional[UserProfile]:
        """Xác thực tài khoản và mật khẩu người dùng"""
        uname = username.strip().lower()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (uname,))
            row = cur.fetchone()
            if not row:
                return None

            if verify_password(password, row["salt"], row["password_hash"]):
                return UserProfile(
                    username=row["username"],
                    name=row["name"],
                    role=row["role"],
                    avatar=row["avatar"]
                )
        return None

    def get_user_profile(self, username: str) -> Optional[UserProfile]:
        uname = username.strip().lower()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (uname,))
            row = cur.fetchone()
            if row:
                return UserProfile(
                    username=row["username"],
                    name=row["name"],
                    role=row["role"],
                    avatar=row["avatar"]
                )
        return None

    # ----------------- REPOSITORY: THƯ VIỆN & LỊCH SỬ -----------------

    def get_user_library(self, username: str) -> List[Dict[str, Any]]:
        uname = username.strip().lower()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT story_id as id, title, author, cover, num_parts as numParts, url, is_custom, added_at
                FROM user_library
                WHERE username = ?
                ORDER BY added_at DESC
            """, (uname,))
            return [dict(r) for r in cur.fetchall()]

    def add_user_library_story(self, username: str, story: UserLibraryStory) -> List[Dict[str, Any]]:
        uname = username.strip().lower()
        now = time.time()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO user_library (username, story_id, title, author, cover, num_parts, url, is_custom, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uname, str(story.id), story.title, story.author, story.cover,
                story.numParts, story.url or "", 1 if story.is_custom else 0, story.added_at or now
            ))
        return self.get_user_library(uname)

    def remove_user_library_story(self, username: str, story_id: str) -> List[Dict[str, Any]]:
        uname = username.strip().lower()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM user_library WHERE username = ? AND story_id = ?", (uname, str(story_id)))
        return self.get_user_library(uname)

    def record_reading_history(self, username: str, item: ReadingHistoryItem) -> List[Dict[str, Any]]:
        uname = username.strip().lower()
        now = time.time()
        with self.get_connection() as conn:
            cur = conn.cursor()
            # Xóa bản ghi cũ cùng chương để đưa bản ghi mới lên đầu
            cur.execute("""
                DELETE FROM read_history
                WHERE username = ? AND story_id = ? AND chapter_id = ?
            """, (uname, str(item.story_id), item.chapter_id))

            cur.execute("""
                INSERT INTO read_history (username, story_id, story_title, story_cover, chapter_id, chapter_title, progress_percent, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uname, str(item.story_id), item.story_title, item.story_cover,
                item.chapter_id, item.chapter_title, item.progress_percent or 0, item.timestamp or now
            ))

            # Giữ tối đa 50 bản ghi gần nhất
            cur.execute("""
                DELETE FROM read_history
                WHERE id NOT IN (
                    SELECT id FROM read_history WHERE username = ? ORDER BY timestamp DESC LIMIT 50
                ) AND username = ?
            """, (uname, uname))

        return self.get_reading_history(uname)

    def get_reading_history(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        uname = username.strip().lower()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT story_id, story_title, story_cover, chapter_id, chapter_title, progress_percent, timestamp
                FROM read_history
                WHERE username = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (uname, limit))
            return [dict(r) for r in cur.fetchall()]

    def record_listening_history(self, username: str, item: ListeningHistoryItem) -> List[Dict[str, Any]]:
        uname = username.strip().lower()
        now = time.time()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM listen_history
                WHERE username = ? AND story_id = ? AND chapter_id = ?
            """, (uname, str(item.story_id), item.chapter_id))

            cur.execute("""
                INSERT INTO listen_history (username, story_id, story_title, story_cover, chapter_id, chapter_title, current_time, duration, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uname, str(item.story_id), item.story_title, item.story_cover,
                item.chapter_id, item.chapter_title, item.current_time or 0.0, item.duration or 0.0,
                item.timestamp or now
            ))

            cur.execute("""
                DELETE FROM listen_history
                WHERE id NOT IN (
                    SELECT id FROM listen_history WHERE username = ? ORDER BY timestamp DESC LIMIT 50
                ) AND username = ?
            """, (uname, uname))

        return self.get_listening_history(uname)

    def get_listening_history(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        uname = username.strip().lower()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT story_id, story_title, story_cover, chapter_id, chapter_title, current_time, duration, timestamp
                FROM listen_history
                WHERE username = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (uname, limit))
            return [dict(r) for r in cur.fetchall()]

    def clear_history(self, username: str, history_type: str):
        uname = username.strip().lower()
        with self.get_connection() as conn:
            cur = conn.cursor()
            if history_type in ["read", "all"]:
                cur.execute("DELETE FROM read_history WHERE username = ?", (uname,))
            if history_type in ["listen", "all"]:
                cur.execute("DELETE FROM listen_history WHERE username = ?", (uname,))

    # ----------------- REPOSITORY: TÁC VỤ (TASKS) -----------------

    def save_task(self, task: TaskProgress):
        now = time.time()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO tasks (
                    task_id, story_id, user_id, device_id, total_chapters,
                    completed_chapters, current_chapter_title, current_chapter_percent,
                    status, can_pause, error, resumed, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM tasks WHERE task_id = ?), ?), ?)
            """, (
                task.task_id, task.story_id, task.user_id, task.device_id,
                task.total_chapters, task.completed_chapters, task.current_chapter_title,
                task.current_chapter_percent, task.status, 1 if task.can_pause else 0,
                task.error, 1 if getattr(task, "resumed", False) else 0,
                task.task_id, now, now
            ))

    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cur.fetchone()
            if not row:
                return None
            return TaskProgress(
                task_id=row["task_id"],
                story_id=row["story_id"],
                total_chapters=row["total_chapters"],
                completed_chapters=row["completed_chapters"],
                current_chapter_title=row["current_chapter_title"] or "",
                current_chapter_percent=row["current_chapter_percent"] or 0,
                status=row["status"],
                can_pause=bool(row["can_pause"]),
                error=row["error"],
                device_id=row["device_id"],
                user_id=row["user_id"],
                resumed=bool(row["resumed"])
            )

    def get_active_task_for_device(self, device_id: str, story_id: Optional[str] = None) -> Optional[TaskProgress]:
        if not device_id:
            return None
        with self.get_connection() as conn:
            cur = conn.cursor()
            if story_id:
                cur.execute("""
                    SELECT * FROM tasks
                    WHERE device_id = ? AND story_id = ? AND status IN ('processing', 'queued', 'paused')
                    ORDER BY updated_at DESC LIMIT 1
                """, (device_id, story_id))
            else:
                cur.execute("""
                    SELECT * FROM tasks
                    WHERE device_id = ? AND status IN ('processing', 'queued', 'paused')
                    ORDER BY updated_at DESC LIMIT 1
                """, (device_id,))

            row = cur.fetchone()
            if not row:
                return None
            return TaskProgress(
                task_id=row["task_id"],
                story_id=row["story_id"],
                total_chapters=row["total_chapters"],
                completed_chapters=row["completed_chapters"],
                current_chapter_title=row["current_chapter_title"] or "",
                current_chapter_percent=row["current_chapter_percent"] or 0,
                status=row["status"],
                can_pause=bool(row["can_pause"]),
                error=row["error"],
                device_id=row["device_id"],
                user_id=row["user_id"],
                resumed=bool(row["resumed"])
            )

    def update_task_status(self, task_id: str, status: str, error: Optional[str] = None):
        now = time.time()
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE tasks
                SET status = ?, error = COALESCE(?, error), updated_at = ?
                WHERE task_id = ?
            """, (status, error, now, task_id))
