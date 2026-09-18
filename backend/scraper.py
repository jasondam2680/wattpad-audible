import re
import json
import logging
from typing import Optional, Dict, Any, List
import requests
from bs4 import BeautifulSoup
from .models import StoryInfo, ChapterInfo

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
}

from urllib.parse import urlparse

class WattpadScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    @staticmethod
    def is_valid_wattpad_url(url: str) -> bool:
        """Kiểm tra URL an toàn, chỉ chấp nhận domain chính thức của Wattpad (Chống SSRF)"""
        try:
            parsed = urlparse(url.strip())
            if parsed.scheme not in ["http", "https"]:
                return False
            hostname = parsed.hostname or ""
            # Chấp nhận wattpad.com và các subdomain của wattpad.com
            if hostname == "wattpad.com" or hostname.endswith(".wattpad.com"):
                return True
            return False
        except Exception:
            return False

    def extract_story_id(self, url_or_id: str) -> Optional[str]:
        """Trích xuất Story ID hoặc Part ID từ đường link Wattpad"""
        url_or_id = url_or_id.strip()
        
        # Nếu nhập trực tiếp số ID
        if url_or_id.isdigit():
            return url_or_id
            
        # Dạng https://www.wattpad.com/story/12345678-ten-truyen
        story_match = re.search(r'/story/(\d+)', url_or_id)
        if story_match:
            return story_match.group(1)
            
        # Dạng https://www.wattpad.com/12345678-ten-chuong
        part_match = re.search(r'wattpad\.com/(\d+)', url_or_id)
        if part_match:
            return part_match.group(1)
            
        return None

    def get_story_info(self, url_or_id: str) -> Optional[StoryInfo]:
        """Lấy thông tin truyện, bìa và danh sách toàn bộ các chương"""
        url_or_id = url_or_id.strip()
        
        # Xác định URL mục tiêu
        if url_or_id.startswith('http://') or url_or_id.startswith('https://'):
            if not self.is_valid_wattpad_url(url_or_id):
                logger.warning(f"[Security Warning] URL không thuộc domain Wattpad hợp lệ: {url_or_id}")
                return None
            target_url = url_or_id
        else:
            clean_id = re.sub(r'[^0-9]', '', url_or_id)
            if not clean_id:
                return None
            target_url = f"https://www.wattpad.com/story/{clean_id}"

        try:
            resp = self.session.get(target_url, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch Wattpad page: {resp.status_code}")
                return None

            html = resp.text
            
            # 1. Trích xuất qua Remix context (Chuẩn nhất và đầy đủ nhất trên Wattpad hiện đại)
            remix_match = re.search(r'window\.__remixContext\s*=\s*(\{.*?\});', html, re.DOTALL)
            if remix_match:
                try:
                    remix_data = json.loads(remix_match.group(1))
                    loader_data = remix_data.get('state', {}).get('loaderData', {})
                    
                    for route_key, route_val in loader_data.items():
                        if isinstance(route_val, dict) and 'story' in route_val:
                            s = route_val['story']
                            return self._build_story_info_from_remix(s, target_url)
                except Exception as e:
                    logger.warning(f"Error parsing remixContext: {e}")

            # 2. Fallback: Parse trực tiếp HTML qua BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.find('h1')
            title_text = title.get_text(strip=True) if title else "Không rõ tiêu đề"
            
            # Tìm tác giả
            author_tag = soup.find('a', href=re.compile(r'/user/'))
            author_text = author_tag.get_text(strip=True) if author_tag else "Wattpad Author"
            
            # Tìm ảnh bìa
            cover_img = soup.find('img', alt=re.compile('Cover', re.I)) or soup.find('img', src=re.compile('cover'))
            cover_url = cover_img['src'] if cover_img and cover_img.get('src') else "https://www.wattpad.com/img/cover-placeholder.png"
            
            # Tìm tóm tắt
            desc_tag = soup.find('h2', class_=re.compile('description')) or soup.find('div', class_=re.compile('description'))
            desc_text = desc_tag.get_text(strip=True) if desc_tag else ""
            
            # Tìm danh sách chương
            parts: List[ChapterInfo] = []
            part_links = soup.find_all('a', href=re.compile(r'^/\d+-.+'))
            seen_ids = set()
            for pl in part_links:
                href = pl.get('href', '')
                pid_match = re.match(r'^/(\d+)-', href)
                if pid_match:
                    pid = int(pid_match.group(1))
                    if pid not in seen_ids:
                        seen_ids.add(pid)
                        parts.append(ChapterInfo(
                            id=pid,
                            title=pl.get_text(strip=True) or f"Chương {len(parts) + 1}",
                            url=f"https://www.wattpad.com{href}"
                        ))
                        
            story_id = self.extract_story_id(target_url) or "unknown"
            
            return StoryInfo(
                id=str(story_id),
                title=title_text,
                author=author_text,
                cover=cover_url,
                description=desc_text,
                url=target_url,
                numParts=len(parts),
                parts=parts
            )

        except Exception as e:
            logger.exception(f"Lỗi khi cào thông tin truyện từ Wattpad: {e}")
            return None

    def _build_story_info_from_remix(self, story_dict: Dict[str, Any], original_url: str) -> StoryInfo:
        parts_list: List[ChapterInfo] = []
        for p in story_dict.get('parts', []):
            parts_list.append(ChapterInfo(
                id=p.get('id'),
                title=p.get('title') or f"Chương {p.get('id')}",
                url=p.get('url') or f"https://www.wattpad.com/{p.get('id')}",
                length=p.get('length', 0),
                createDate=p.get('createDate')
            ))

        author_name = "Ẩn danh"
        if isinstance(story_dict.get('author'), dict):
            author_name = story_dict['author'].get('name') or author_name
        elif isinstance(story_dict.get('user'), dict):
            author_name = story_dict['user'].get('name') or author_name

        lang = story_dict.get('language')
        if isinstance(lang, dict):
            lang_str = str(lang.get('name', 'vi'))
        else:
            lang_str = str(lang) if lang is not None else 'vi'

        return StoryInfo(
            id=str(story_dict.get('id')),
            title=story_dict.get('title', 'Truyện không có tiêu đề'),
            author=author_name,
            cover=story_dict.get('cover', 'https://www.wattpad.com/img/cover-placeholder.png'),
            description=story_dict.get('description', ''),
            url=original_url,
            language=lang_str,
            numParts=len(parts_list),
            parts=parts_list
        )

    def get_chapter_text(self, part_id: int) -> str:
        """
        Lấy nội dung toàn văn của một chương truyện.
        Tự động duyệt qua các trang (pagination) nếu chương dài nhiều trang.
        """
        paragraphs: List[str] = []
        page = 1
        max_pages = 20 # Ngăn lặp vô hạn
        
        while page <= max_pages:
            api_url = f"https://www.wattpad.com/apiv2/?m=storytext&id={part_id}&page={page}"
            try:
                resp = self.session.get(api_url, timeout=12)
                if resp.status_code != 200:
                    break
                    
                content = resp.text.strip()
                if not content or len(content) < 10:
                    break
                    
                soup = BeautifulSoup(content, 'html.parser')
                page_paras = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
                
                if not page_paras:
                    # Thử lấy toàn bộ text nếu không có thẻ p
                    raw_text = soup.get_text(strip=True)
                    if raw_text:
                        paragraphs.append(raw_text)
                    break
                    
                paragraphs.extend(page_paras)
                page += 1
            except Exception as e:
                logger.error(f"Lỗi khi lấy trang {page} của chương {part_id}: {e}")
                break

        # Nếu apiv2 không lấy được nội dung, thử fallback cào trực tiếp trang chương
        if not paragraphs:
            paragraphs = self._fallback_fetch_chapter_page(part_id)

        clean_text = "\n\n".join(paragraphs)
        return clean_text

    def _fallback_fetch_chapter_page(self, part_id: int) -> List[str]:
        try:
            page_url = f"https://www.wattpad.com/{part_id}"
            resp = self.session.get(page_url, timeout=12)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, 'html.parser')
            paras = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
            return paras
        except Exception as e:
            logger.error(f"Fallback fetch failed for part {part_id}: {e}")
            return []

# Module level helper for SSRF protection
is_valid_wattpad_url = WattpadScraper.is_valid_wattpad_url
