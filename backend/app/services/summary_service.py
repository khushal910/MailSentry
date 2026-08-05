import asyncio
import logging
import os
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class SummaryService:
    """
    Reusable Gemini AI Service for Email Summarization.
    Encapsulates Gemini API key retrieval, prompt formatting, error handling,
    and automatic retry logic.
    """

    PROMPT_TEMPLATE = (
        "You are an intelligent email assistant.\n\n"
        "Summarize this email.\n\n"
        "Include:\n\n"
        "- Purpose\n"
        "- Important dates\n"
        "- Required actions\n"
        "- Deadlines\n"
        "- Tone\n\n"
        "Return the summary in under 100 words.\n\n"
        "Email Body:\n{email_body}"
    )

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout: float = 30.0,
    ):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                getattr(settings, "GEMINI_API_KEY", "")
                or getattr(settings, "GEMINI_API", "")
                or os.getenv("GEMINI_API_KEY", "")
                or os.getenv("GEMINI_API", "")
                or os.getenv("GOOGLE_API_KEY", "")
            )
        self.model_name = (
            model_name
            or getattr(settings, "GEMINI_MODEL", "")
            or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        )
        self.timeout = timeout


    async def generate_summary(self, email_body: str) -> str:
        """
        Generates a concise email summary using Google Gemini API.

        Sends ONLY the email body formatted with a structured prompt.
        Handles timeouts, empty responses, API errors, and retries once if necessary.
        Returns only the summary string.
        """
        if not email_body or not str(email_body).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email body is empty; cannot generate summary.",
            )

        clean_body = str(email_body).strip()

        if not self.api_key:
            logger.error(
                "Gemini API key is missing or not configured in environment variables."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API key is not configured on the server.",
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        prompt = self.PROMPT_TEMPLATE.format(email_body=clean_body)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 300,
            },
        }

        max_attempts = 2
        last_exception: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)

                if response.status_code != 200:
                    logger.warning(
                        f"[Attempt {attempt}/{max_attempts}] Gemini API returned HTTP status {response.status_code}: {response.text}"
                    )
                    if attempt < max_attempts and response.status_code in (
                        429,
                        500,
                        502,
                        503,
                        504,
                    ):
                        await asyncio.sleep(1.0)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Gemini API returned error status {response.status_code}.",
                    )

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.warning(
                        f"[Attempt {attempt}/{max_attempts}] Empty candidate list from Gemini API."
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Gemini API returned an empty response candidate set.",
                    )

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    logger.warning(
                        f"[Attempt {attempt}/{max_attempts}] Malformed content parts from Gemini API."
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Malformed response format received from Gemini API.",
                    )

                summary_text = parts[0]["text"].strip()
                if not summary_text:
                    logger.warning(
                        f"[Attempt {attempt}/{max_attempts}] Gemini API returned empty summary string."
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5)
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Generated summary from Gemini API was empty.",
                    )

                return summary_text

            except httpx.TimeoutException as exc:
                logger.warning(
                    f"[Attempt {attempt}/{max_attempts}] Timeout while calling Gemini API: {exc!s}"
                )
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(1.0)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Request to Gemini API timed out.",
                ) from exc

            except httpx.RequestError as exc:
                logger.warning(
                    f"[Attempt {attempt}/{max_attempts}] Network error calling Gemini API: {exc!s}"
                )
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
                logger.error(
                    f"[Attempt {attempt}/{max_attempts}] Unexpected error calling Gemini API: {exc!s}"
                )
                last_exception = exc
                if attempt < max_attempts:
                    await asyncio.sleep(0.5)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An unexpected error occurred during email summarization: {exc!s}",
                ) from exc

        if isinstance(last_exception, HTTPException):
            raise last_exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary from Gemini API after retrying.",
        )
