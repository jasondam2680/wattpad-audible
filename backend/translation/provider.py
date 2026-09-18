"""
Translation Providers & Abstraction Layer
"""
import os
import time
import json
import random
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import aiohttp

from .models import (
    TranslationResult, TranslationError, TranslationProviderError,
    TranslationRateLimitError, TranslationTimeoutError, TranslationValidationError,
    BookTranslationContext
)
from .prompts import PromptBuilder, DEFAULT_PROMPT_VERSION

logger = logging.getLogger(__name__)

class TranslationProvider(ABC):
    @abstractmethod
    async def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "vi",
        context: Optional[BookTranslationContext] = None,
        previous_context: Optional[str] = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION
    ) -> TranslationResult:
        """Thực hiện dịch thuật đoạn văn bản"""
        pass

class MockTranslationProvider(TranslationProvider):
    """
    Mock Provider dùng cho Unit Testing và Development độc lập, không phụ thuộc vào Internet hay API Key.
    """
    def __init__(
        self,
        simulate_latency_ms: float = 0.0,
        fail_rate: float = 0.0,
        error_type: Optional[str] = None,
        should_fail: bool = False,
        fail_error_msg: str = "",
        custom_translations: Optional[Dict[str, str]] = None
    ):
        self.simulate_latency_ms = simulate_latency_ms
        self.fail_rate = fail_rate
        self.error_type = error_type
        self.should_fail = should_fail
        self.fail_error_msg = fail_error_msg
        self.custom_translations = custom_translations or {}
        self.call_count = 0

    async def translate(
        self,
        text: Optional[str] = None,
        source_language: str = "en",
        target_language: str = "vi",
        context: Optional[BookTranslationContext] = None,
        previous_context: Optional[str] = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
        messages: Optional[List[Dict[str, str]]] = None,
        source_text: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        self.call_count += 1
        start_time = time.time()

        if self.should_fail:
            err_msg = self.fail_error_msg or "Mock translation failure"
            if "rate limit" in err_msg.lower() or "429" in err_msg:
                raise TranslationRateLimitError(err_msg)
            elif "timeout" in err_msg.lower():
                raise TranslationTimeoutError(err_msg)
            raise TranslationError(err_msg)

        if self.error_type:
            if self.error_type == "rate_limit":
                raise TranslationRateLimitError("Rate limit exceeded (429)")
            elif self.error_type == "timeout":
                raise TranslationTimeoutError("Request timed out")
            elif self.error_type == "server_error":
                raise TranslationProviderError("Provider server error (500)")

        # Determine effective source text
        raw_input = source_text or text or ""
        if not raw_input and messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    raw_input = msg.get("content", "")
                    break

        if self.simulate_latency_ms > 0:
            await asyncio.sleep(self.simulate_latency_ms / 1000.0)

        # Check custom translations dictionary
        if raw_input in self.custom_translations:
            translated = self.custom_translations[raw_input]
            if messages and not context and not text:
                return translated
            return TranslationResult(
                translated_text=translated,
                source_language=source_language,
                target_language=target_language,
                provider="mock",
                model=model or "mock-v1",
                prompt_version=prompt_version,
                source_text_hash="",
                input_chars=len(raw_input),
                output_chars=len(translated),
                latency_ms=round((time.time() - start_time) * 1000.0, 2),
                cached=False
            )

        # Simple deterministic Vietnamese mock translation
        translated = raw_input
        word_replacements = {
            "Chapter": "Chương",
            "Once upon a time": "Ngày xửa ngày xưa",
            "The quick brown fox": "Chú cáo nâu nhanh nhẹn",
            "jumps over the lazy dog": "nhảy qua chú chó lười biếng",
            "Hello world": "Xin chào thế giới",
            "He said": "Anh ấy nói",
            "She smiled": "Cô ấy mỉm cười",
            "The end": "Hết"
        }
        for k, v in word_replacements.items():
            translated = translated.replace(k, v)

        if translated == raw_input and source_language == "en":
            translated = f"[Bản dịch tiếng Việt] {raw_input}"

        latency = (time.time() - start_time) * 1000.0

        if messages and not context and not text:
            return translated

        return TranslationResult(
            translated_text=translated,
            source_language=source_language,
            target_language=target_language,
            provider="mock",
            model=model or "mock-v1",
            prompt_version=prompt_version,
            source_text_hash="",
            input_chars=len(raw_input),
            output_chars=len(translated),
            latency_ms=round(latency, 2),
            cached=False
        )

class OpenAITranslationProvider(TranslationProvider):
    """
    OpenAI-compatible Translation Provider.
    Hỗ trợ OpenAI, OpenRouter, DeepSeek, Local vLLM/Ollama qua standard Chat Completion endpoint.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        api_base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.environ.get("TRANSLATION_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        effective_url = api_base_url or base_url or os.environ.get("TRANSLATION_BASE_URL") or "https://api.openai.com/v1"
        self.base_url = effective_url.rstrip('/')
        self.model = model or os.environ.get("TRANSLATION_MODEL") or "gpt-4o-mini"
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "vi",
        context: Optional[BookTranslationContext] = None,
        previous_context: Optional[str] = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION
    ) -> TranslationResult:
        if not self.api_key:
            raise TranslationProviderError("Chưa cấu hình API Key cho Translation Provider (TRANSLATION_API_KEY hoặc OPENAI_API_KEY).")

        full_prompt = PromptBuilder.build_prompt(
            source_text=text,
            source_language="English" if source_language == "en" else source_language,
            target_language="Vietnamese" if target_language == "vi" else target_language,
            context=context,
            previous_translation_context=previous_context,
            prompt_version=prompt_version
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.3,
            "top_p": 0.95
        }

        url = f"{self.base_url}/chat/completions"
        start_time = time.time()
        last_error = None
        attempt = 0

        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)

        while attempt <= self.max_retries:
            attempt += 1
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=payload) as resp:
                        status_code = resp.status
                        if status_code == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"].strip()
                            latency = (time.time() - start_time) * 1000.0

                            # Validation
                            clean_content = self._sanitize_and_validate_output(content)

                            usage = data.get("usage", {})
                            return TranslationResult(
                                translated_text=clean_content,
                                source_language=source_language,
                                target_language=target_language,
                                provider="openai",
                                model=self.model,
                                prompt_version=prompt_version,
                                source_text_hash="",
                                input_chars=len(text),
                                output_chars=len(clean_content),
                                latency_ms=round(latency, 2),
                                retry_count=attempt - 1,
                                metadata={
                                    "prompt_tokens": usage.get("prompt_tokens", 0),
                                    "completion_tokens": usage.get("completion_tokens", 0)
                                }
                            )
                        elif status_code == 429:
                            last_error = TranslationRateLimitError(f"OpenAI API rate limit exceeded (429)")
                        elif status_code in [500, 502, 503, 504]:
                            resp_text = await resp.text()
                            last_error = TranslationProviderError(f"OpenAI server error ({status_code}): {resp_text[:150]}")
                        elif status_code == 401:
                            raise TranslationProviderError("OpenAI API Key không hợp lệ hoặc đã hết hạn (401).")
                        else:
                            resp_text = await resp.text()
                            raise TranslationProviderError(f"OpenAI API error ({status_code}): {resp_text[:200]}")

            except asyncio.TimeoutError:
                last_error = TranslationTimeoutError(f"Hết thời gian chờ phản hồi ({self.timeout_seconds}s)")
            except aiohttp.ClientError as ce:
                last_error = TranslationProviderError(f"Lỗi mạng khi kết nối Translation Provider: {ce}")
            except (TranslationRateLimitError, TranslationTimeoutError, TranslationProviderError) as e:
                last_error = e

            # Exponential backoff with jitter
            if attempt <= self.max_retries:
                backoff_wait = (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
                logger.warning(f"Translation attempt {attempt} failed ({last_error}). Retrying in {backoff_wait:.2f}s...")
                await asyncio.sleep(backoff_wait)

        raise last_error or TranslationProviderError("Dịch thuật thất bại sau nhiều lần thử lại.")

    def _sanitize_and_validate_output(self, content: str) -> str:
        """Kiểm tra và làm sạch bản dịch loại bỏ meta comments"""
        if not content:
            raise TranslationValidationError("Bản dịch trả về nội dung rỗng.")

        # Xóa markdown code block nếu model trả về ```markdown ... ```
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if len(lines) > 2 and lines[-1].startswith("```"):
                cleaned = "\n".join(lines[1:-1]).strip()

        # Loại bỏ các tiền tố meta comment không mong muốn
        meta_prefixes = [
            "Bản dịch:",
            "Dưới đây là bản dịch:",
            "Dưới đây là bản dịch tiếng Việt:",
            "Here is the translation:",
            "Translation:"
        ]
        for prefix in meta_prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()

        return cleaned

def create_translation_provider(
    provider_name: str = "mock",
    api_key: Optional[str] = None,
    api_base_url: Optional[str] = None,
    model: str = "gpt-4o-mini",
    **kwargs
) -> TranslationProvider:
    """Factory khởi tạo Translation Provider"""
    p_name = (provider_name or "mock").strip().lower()
    if p_name == "openai":
        key = api_key or os.getenv("TRANSLATION_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        base_url = api_base_url or os.getenv("TRANSLATION_API_BASE_URL", "https://api.openai.com/v1")
        m = model or os.getenv("TRANSLATION_MODEL", "gpt-4o-mini")
        return OpenAITranslationProvider(api_key=key, api_base_url=base_url, model=m, **kwargs)
    return MockTranslationProvider(**kwargs)
