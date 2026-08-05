import asyncio
import logging
import os
import time
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import SYSTEM_SUMMARY_PROMPT, format_summary_prompt

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM Provider implementation using Gemini generateContent REST API.
    Supports Gemini 2.5 Flash, Gemini 1.5 Flash, and other Gemini models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = (
            api_key
            or getattr(settings, "GEMINI_API_KEY", "")
            or getattr(settings, "GEMINI_API", "")
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GEMINI_API", "")
            or os.getenv("GOOGLE_API_KEY", "")
        )
        self._model_name = (
            model_name
            or getattr(settings, "GEMINI_MODEL", "")
            or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        )
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_summary(self, email_body: str) -> str:
        """
        Sends email body to Google Gemini API.
        Logs model, generation duration, token usage, and handles retries / timeouts cleanly.
        """
        if not email_body or not str(email_body).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email body is empty; cannot generate summary.",
            )

        clean_body = str(email_body).strip()

        if not self.api_key:
            logger.error("Gemini API key is missing or not configured in environment variables.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API key is not configured on the server. Please set GEMINI_API_KEY.",
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        prompt = format_summary_prompt(clean_body)

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 300,
            },
        }

        max_attempts = 2
        last_exception: Exception | None = None
        start_time = time.perf_counter()

        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)

                duration = time.perf_counter() - start_time

                if response.status_code == 400 or response.status_code == 403:
                    logger.error(
                        f"[GeminiProvider] Invalid API Key or Unauthorized (HTTP {response.status_code}): {response.text}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Invalid Gemini API key configured on server.",
                    )

                if response.status_code != 200:
                    logger.warning(
                        f"[GeminiProvider] Attempt {attempt}/{max_attempts} returned HTTP status {response.status_code}: {response.text}"
                    )
                    if attempt < max_attempts and response.status_code in (429, 500, 502, 503, 504):
                        await asyncio.sleep(1.0)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Gemini API returned error status {response.status_code}.",
                    )

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.warning(f"[GeminiProvider] Empty candidate set from Gemini API.")
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Gemini API returned an empty response candidate set.",
                    )

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    logger.warning(f"[GeminiProvider] Malformed content parts from Gemini API.")
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Malformed response format received from Gemini API.",
                    )

                summary_text = parts[0]["text"].strip()
                if not summary_text:
                    logger.warning(f"[GeminiProvider] Gemini API returned empty summary string.")
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Generated summary from Gemini API was empty.",
                    )

                # Token usage metadata if provided
                usage_metadata = data.get("usageMetadata", {})
                total_tokens = usage_metadata.get("totalTokenCount", 0)
                prompt_tokens = usage_metadata.get("promptTokenCount", 0)
                candidates_tokens = usage_metadata.get("candidatesTokenCount", 0)

                logger.info(
                    f"[GeminiProvider] Summary generated successfully. "
                    f"Provider: 'gemini' | Model: '{self.model_name}' | "
                    f"Duration: {duration:.3f}s | Tokens: total={total_tokens} (prompt={prompt_tokens}, candidate={candidates_tokens})"
                )

                return summary_text

            except httpx.TimeoutException as exc:
                logger.warning(f"[GeminiProvider] Attempt {attempt}/{max_attempts} request timeout: {exc!s}")
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(1.0)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Request to Gemini API timed out.",
                ) from exc

            except httpx.RequestError as exc:
                logger.warning(f"[GeminiProvider] Attempt {attempt}/{max_attempts} network error: {exc!s}")
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(1.0)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Network error communicating with Gemini API: {exc!s}",
                ) from exc

            except HTTPException:
                raise

            except Exception as exc:
                logger.error(f"[GeminiProvider] Attempt {attempt}/{max_attempts} unexpected error: {exc!s}")
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(0.5)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An unexpected error occurred during email summarization with Gemini: {exc!s}",
                ) from exc

        if isinstance(last_exception, HTTPException):
            raise last_exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary from Gemini API after retrying.",
        )
