import unittest
import os
import shutil
import tempfile
from fastapi.testclient import TestClient

from backend.main import app
from backend.scraper import is_valid_wattpad_url

class TestSecurityAndAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_ssrf_url_validation(self):
        # Valid Wattpad URLs
        self.assertTrue(is_valid_wattpad_url("https://www.wattpad.com/story/151007312-sample-story"))
        self.assertTrue(is_valid_wattpad_url("https://wattpad.com/151007312-sample-chapter"))
        self.assertTrue(is_valid_wattpad_url("http://www.wattpad.com/story/9999"))

        # Malicious / SSRF URLs that MUST be blocked
        self.assertFalse(is_valid_wattpad_url("http://127.0.0.1:8000/secret"))
        self.assertFalse(is_valid_wattpad_url("http://localhost:8080/admin"))
        self.assertFalse(is_valid_wattpad_url("http://169.254.169.254/latest/meta-data/"))
        self.assertFalse(is_valid_wattpad_url("file:///etc/passwd"))
        self.assertFalse(is_valid_wattpad_url("https://attacker.com/story/151007312"))
        self.assertFalse(is_valid_wattpad_url("https://wattpad.com.evil.com/story/123"))
        self.assertFalse(is_valid_wattpad_url("javascript:alert(1)"))

    def test_api_languages_endpoint(self):
        res = self.client.get("/api/languages")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("languages", data)
        self.assertIn("models", data)
        self.assertIn("prompt_versions", data)
        
        lang_codes = [l["code"] for l in data["languages"]]
        self.assertIn("vi", lang_codes)
        self.assertIn("en", lang_codes)
        self.assertIn("auto", lang_codes)

    def test_api_translation_preview(self):
        req = {
            "text": "The ancient bell tolled three times in the foggy evening.",
            "source_language": "auto",
            "target_language": "vi"
        }
        res = self.client.post("/api/translation/preview", json=req)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("translated_text", data)
        self.assertIn("latency_ms", data)
        self.assertEqual(data["source_language"], "en")
        self.assertEqual(data["target_language"], "vi")

    def test_api_custom_story_creation(self):
        req = {
            "title": "Custom Test Novel",
            "author": "Author X",
            "description": "Short description for custom story test",
            "text": "Chương 1: Bình minh trên thảo nguyên xanh ngát. Những tia nắng đầu tiên xuyên qua từng tán lá."
        }
        res = self.client.post("/api/story/custom", json=req)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "Custom Test Novel")
        self.assertEqual(len(data["parts"]), 1)
        self.assertEqual(data["language"], "vi")

    def test_api_glossary_management(self):
        # Create a story first
        story_res = self.client.post("/api/story/custom", json={
            "title": "Glossary Test Novel",
            "author": "Author G",
            "description": "Desc",
            "text": "Sample text for testing glossary"
        })
        story_id = story_res.json()["id"]

        # Add glossary term
        add_res = self.client.post(f"/api/story/{story_id}/glossary", json={
            "source_term": "Aegis Shield",
            "target_term": "Khiên Thánh Thần",
            "notes": "Vũ khí phòng thủ tối thượng"
        })
        self.assertEqual(add_res.status_code, 200)
        
        # Retrieve glossary
        get_res = self.client.get(f"/api/story/{story_id}/glossary")
        self.assertEqual(get_res.status_code, 200)
        glossary_items = get_res.json().get("glossary", [])
        self.assertTrue(len(glossary_items) >= 1)
        self.assertEqual(glossary_items[0]["source_term"], "Aegis Shield")
        self.assertEqual(glossary_items[0]["target_term"], "Khiên Thánh Thần")

    def test_auth_login_and_token(self):
        login_res = self.client.post("/api/auth/login", json={
            "username": "jason",
            "password": "1987"
        })
        self.assertEqual(login_res.status_code, 200)
        auth_data = login_res.json()
        self.assertIn("token", auth_data)
        self.assertEqual(auth_data["user"]["username"], "jason")

        # Use token to call protected endpoint
        headers = {"Authorization": f"Bearer {auth_data['token']}"}
        me_res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["user"]["username"], "jason")

if __name__ == "__main__":
    unittest.main()
