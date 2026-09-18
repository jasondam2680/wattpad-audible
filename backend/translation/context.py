"""
Book Translation Context Manager (Character Bible, Relationships, Style)
"""
from typing import Optional, Dict, Any, List
from backend.database import DatabaseManager
from .models import BookTranslationContext, CharacterItem, GlossaryEntry

class TranslationContextManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_context(self, story_id: str) -> BookTranslationContext:
        """Tải thông tin ngữ cảnh truyện và danh mục glossary từ DB"""
        ctx_data = self.db.get_translation_context(story_id)
        glossary_items = self.db.get_glossary(story_id)
        story = self.db.get_story(story_id)

        title = story.title if story else ""
        author = story.author if story else ""
        genre = ctx_data.get("genre", "") if ctx_data else ""
        
        characters = []
        relationships = {}
        style_notes = ""

        if ctx_data:
            cb = ctx_data.get("character_bible", {})
            for c_info in cb.get("characters", []):
                characters.append(CharacterItem(**c_info))
            relationships = ctx_data.get("relationship_map", {})
            style_notes = ctx_data.get("style_bible", {}).get("notes", "")

        glossary_list = [
            GlossaryEntry(
                source_term=g["source_term"],
                target_term=g["target_term"],
                notes=g.get("notes")
            )
            for g in glossary_items
        ]

        return BookTranslationContext(
            story_id=story_id,
            title=title,
            author=author,
            genre=genre,
            characters=characters,
            relationships=relationships,
            glossary=glossary_list,
            style_notes=style_notes
        )

    def update_context(
        self,
        story_id: str,
        genre: str = "",
        characters: Optional[List[Dict[str, Any]]] = None,
        relationships: Optional[Dict[str, str]] = None,
        style_notes: str = ""
    ):
        """Cập nhật ngữ cảnh cho truyện"""
        cb_dict = {"characters": characters or []}
        rel_dict = relationships or {}
        sb_dict = {"notes": style_notes}
        self.db.save_translation_context(
            story_id=story_id,
            genre=genre,
            character_bible=cb_dict,
            relationship_map=rel_dict,
            style_bible=sb_dict
        )

    def save_context(self, story_id: str, context: BookTranslationContext):
        """Lưu toàn bộ BookTranslationContext vào database"""
        chars_list = []
        for c in context.characters:
            if hasattr(c, "model_dump"):
                chars_list.append(c.model_dump())
            elif isinstance(c, dict):
                chars_list.append(c)
            else:
                chars_list.append(dict(c))

        cb_dict = {"characters": chars_list}
        rel_dict = context.relationships or {}
        style_notes = context.style_notes or getattr(context, 'tone_style', '')
        sb_dict = {"notes": style_notes}

        self.db.save_translation_context(
            story_id=story_id,
            genre=context.genre,
            character_bible=cb_dict,
            relationship_map=rel_dict,
            style_bible=sb_dict
        )
