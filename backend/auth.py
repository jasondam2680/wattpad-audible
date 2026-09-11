import os
import time
import uuid
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from .models import (
    UserProfile, UserLibraryStory, ReadingHistoryItem, ListeningHistoryItem
)
from .database import DatabaseManager

logger = logging.getLogger(__name__)

# Khóa bí mật nội bộ dùng ký token phiên
SECRET_KEY = os.environ.get("WATTPAD_SECRET_KEY", "wattpad-ai-audiobook-v18-secret-2026")

class UserManager:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db if db is not None else DatabaseManager()
        self.active_sessions: Dict[str, str] = {} # token -> username

    def authenticate(self, username: str, password: str) -> Optional[UserProfile]:
        """Kiểm tra thông tin đăng nhập thành viên qua database với mật khẩu đã hash an toàn"""
        return self.db.verify_user(username, password)

    def create_session(self, username: str) -> str:
        """Tạo token phiên làm việc bảo mật (HMAC-SHA256)"""
        uname = username.strip().lower()
        token_payload = f"{uname}:{int(time.time())}:{uuid.uuid4().hex[:12]}"
        sig = hmac.new(SECRET_KEY.encode(), token_payload.encode(), hashlib.sha256).hexdigest()[:16]
        token = f"wp_{token_payload}_{sig}"
        self.active_sessions[token] = uname
        return token

    def verify_token(self, token: Optional[str]) -> Optional[UserProfile]:
        """Xác thực token phiên gửi từ frontend/Android và kiểm tra hồ sơ user trong DB"""
        if not token:
            return None
        
        token = token.strip()
        if token.startswith("Bearer "):
            token = token[7:].strip()

        # 1. Kiểm tra trong cache active_sessions
        if token in self.active_sessions:
            uname = self.active_sessions[token]
            user = self.db.get_user_profile(uname)
            if user:
                return user

        # 2. Kiểm tra định dạng token hợp lệ theo HMAC signature
        try:
            parts = token.split("_")
            if len(parts) == 3 and parts[0] == "wp":
                payload = parts[1]
                sig = parts[2]
                expected_sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
                if hmac.compare_digest(sig, expected_sig):
                    uname = payload.split(":")[0]
                    user = self.db.get_user_profile(uname)
                    if user:
                        self.active_sessions[token] = uname
                        return user
        except Exception as e:
            logger.warning(f"Token không hợp lệ: {e}")

        return None

    def logout(self, token: str):
        if token in self.active_sessions:
            del self.active_sessions[token]

    # ----------------- QUẢN LÝ THƯ VIỆN & LỊCH SỬ -----------------

    def get_user_data(self, username: str) -> Dict[str, Any]:
        """Lấy toàn bộ thông tin tài khoản, thư viện truyện và lịch sử từ SQLite"""
        uname = username.strip().lower()
        profile = self.db.get_user_profile(uname)
        lib_stories = self.db.get_user_library(uname)
        read_hist = self.db.get_reading_history(uname)
        listen_hist = self.db.get_listening_history(uname)

        return {
            "username": uname,
            "name": profile.name if profile else uname.capitalize(),
            "role": profile.role if profile else "Thành viên",
            "avatar": profile.avatar if profile else uname[:1].upper(),
            "library_stories": lib_stories,
            "read_history": read_hist,
            "listen_history": listen_hist
        }

    def add_library_story(self, username: str, story: UserLibraryStory) -> List[Dict[str, Any]]:
        """Thêm truyện vào thư viện người dùng trong SQLite"""
        return self.db.add_user_library_story(username, story)

    def remove_library_story(self, username: str, story_id: str) -> List[Dict[str, Any]]:
        """Xóa truyện khỏi thư viện người dùng trong SQLite"""
        return self.db.remove_user_library_story(username, story_id)

    def record_reading_history(self, username: str, item: ReadingHistoryItem) -> List[Dict[str, Any]]:
        """Lưu lịch sử đọc truyện của người dùng vào SQLite"""
        return self.db.record_reading_history(username, item)

    def record_listening_history(self, username: str, item: ListeningHistoryItem) -> List[Dict[str, Any]]:
        """Lưu lịch sử nghe sách nói vào SQLite"""
        return self.db.record_listening_history(username, item)

    def clear_history(self, username: str, history_type: str):
        """Xóa lịch sử đọc hoặc nghe"""
        self.db.clear_history(username, history_type)
