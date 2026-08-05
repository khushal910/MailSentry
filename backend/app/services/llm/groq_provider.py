import asyncio
import logging
import os
import time
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import SYSTEM_SUMMARY_PROMPT

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """
    Groq LLM Provider implementation using Groq's high-performance Chat Completions API.
    Supports Llama 3.3 70B, Llama 3.1 8B, and other Groq models.
    """

    GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = (
            api_key
            or getattr(settings, "GROQ_API_KEY", "")
            or os.getenv("GROQ_API_KEY", "")
        )
        self._model_name = (
            model_name
            or getattr(settings, "GROQ_MODEL", "")
            or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        )
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_summary(self, email_body: str) -> str:
        """
        Sends email body to Groq API using Llama 3.3 / Llama 3.1 model.
        Logs model, generation time, token usage, and handles retries / timeouts cleanly.
        """
        if not email_body or not str(email_body).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email body is empty; cannot generate summary.",
            )

        clean_body = str(email_body).strip()

        if not self.api_key:
            logger.error("Groq API key is missing or not configured in environment variables.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Groq API key is not configured on the server. Please set GROQ_API_KEY.",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_SUMMARY_PROMPT},
                {"role": "user", "content": f"Email Body:\n{clean_body}"},
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        }

        max_attempts = 2
        last_exception: Exception | None = None
        start_time = time.perf_counter()

        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.GROQ_COMPLETIONS_URL,
                        headers=headers,
                        json=payload,
                    )

                duration = time.perf_counter() - start_time

                if response.status_code == 401 or response.status_code == 403:
                    logger.error(
                        f"[GroqProvider] Invalid API Key or Unauthorized (HTTP {response.status_code}): {response.text}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Invalid Groq API key configured on server.",
                    )

                if response.status_code != 200:
                    logger.warning(
                        f"[GroqProvider] Attempt {attempt}/{max_attempts} returned HTTP status {response.status_code}: {response.text}"
                    )
                    if attempt < max_attempts and response.status_code in (429, 500, 502, 503, 504):
                        await asyncio.sleep(1.0)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Groq API returned HTTP error status {response.status_code}.",
                    )

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    logger.warning(f"[GroqProvider] Empty choices returned from Groq API.")
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Groq API returned an empty completion response.",
                    )

                message = choices[0].get("message", {})
                summary_text = str(message.get("content", "")).strip()

                if not summary_text:
                    logger.warning(f"[GroqProvider] Groq API returned empty summary string.")
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Generated summary from Groq API was empty.",
                    )

                # Log performance metrics & token usage if present
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                logger.info(
                    f"[GroqProvider] Summary generated successfully. "
                    f"Provider: 'groq' | Model: '{self.model_name}' | "
                    f"Duration: {duration:.3f}s | Tokens: total={total_tokens} (prompt={prompt_tokens}, completion={completion_tokens})"
                )

                return summary_text

            except httpx.TimeoutException as exc:
                logger.warning(f"[GroqProvider] Attempt {attempt}/{max_attempts} request timeout: {exc!s}")
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(1.0)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Request to Groq API timed out.",
                ) from exc

            except httpx.RequestError as exc:
                logger.warning(f"[GroqProvider] Attempt {attempt}/{max_attempts} network error: {exc!s}")
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(1.0)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Network error communicating with Groq API: {exc!s}",
                ) from exc

            except HTTPException:
                raise

            except Exception as exc:
                logger.error(f"[GroqProvider] Attempt {attempt}/{max_attempts} unexpected error: {exc!s}")
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(0.5)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An unexpected error occurred during email summarization with Groq: {exc!s}",
                ) from exc

        if isinstance(last_exception, HTTPException):
            raise last_exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary from Groq API after retrying.",
        )
