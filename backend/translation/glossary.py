"""
Glossary Manager for Story-Specific Terminology Consistency
"""
from typing import List, Dict, Any, Optional
from backend.database import DatabaseManager

class GlossaryManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_terms(self, story_id: str) -> List[Dict[str, Any]]:
        """Lấy danh sách thuật ngữ của tác phẩm"""
        return self.db.get_glossary(story_id)

    def get_glossary(self, story_id: str) -> List[Dict[str, Any]]:
        """Alias cho get_terms"""
        return self.get_terms(story_id)

    def add_term(self, story_id: str, source_term: str, target_term: str, notes: str = "") -> List[Dict[str, Any]]:
        """Thêm hoặc cập nhật thuật ngữ"""
        return self.db.add_glossary_item(story_id, source_term, target_term, notes)

    def remove_term(self, story_id: str, source_term: str) -> List[Dict[str, Any]]:
        """Xóa thuật ngữ"""
        return self.db.delete_glossary_item(story_id, source_term)

    def delete_term(self, story_id: str, source_term: str) -> List[Dict[str, Any]]:
        """Alias cho remove_term"""
        return self.remove_term(story_id, source_term)

# Module alias for consistency across codebase
TranslationGlossaryManager = GlossaryManager
