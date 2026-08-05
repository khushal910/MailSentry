import logging
from typing import Any

import httpx
from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.email_repository import EmailRepository

logger = logging.getLogger(__name__)


class EmailSummaryService:
    """
    Business logic layer for Lazy Email Summarization using Google Gemini API.
    Follows clean architecture and dependency injection.
    """

    def __init__(self, repository: EmailRepository | None = None):
        self.repository = repository if repository is not None else EmailRepository()

    async def get_or_generate_summary(
        self, email_id: str, current_user_id: str | None = None
    ) -> dict[str, Any]:
        """
        Retrieves or generates a lazy summary for an email document in MongoDB.

        Lifecycle Rules:
        1. Validates email_id format (must be valid ObjectId or non-empty string).
        2. Retrieves the email document from MongoDB repository.
        3. If 'summary' field exists and is not empty:
           - Returns it immediately (NEVER calls Gemini API).
        4. If 'summary' field does NOT exist or is empty:
           - Reads the email body (or snippet/content/subject).
           - Sends ONLY the email body to Gemini API with a professional prompt.
           - Generates a concise summary.
           - Persists the generated summary back into MongoDB in the same document.
           - Returns the summary with cached=False flag.
        """
        if not email_id or not str(email_id).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email ID format.",
            )

        clean_id = str(email_id).strip()

        # Step 1: Query database for the email document
        email_doc = self.repository.find_by_id(clean_id)
        if not email_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email with ID '{clean_id}' was not found.",
            )

        # Optional security check: if current_user_id provided, verify email ownership
        if current_user_id:
            doc_user_id = str(email_doc.get("user_id", "")).strip()
            if doc_user_id and doc_user_id != str(current_user_id).strip():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Email with ID '{clean_id}' was not found.",
                )

        # Step 2: Check if a field named 'summary' already exists and is non-empty
        existing_summary = email_doc.get("summary")
        if (
            existing_summary is not None
            and isinstance(existing_summary, str)
            and existing_summary.strip()
        ):
            logger.info(
                f"Summary for email_id='{clean_id}' found in database cache. "
                f"Returning cached summary without calling Gemini API."
            )
            return {
                "email_id": str(email_doc["_id"]),
                "summary": existing_summary.strip(),
                "cached": True,
            }

        # Step 3: Extract email body for summarization
        body = (
            email_doc.get("body")
            or email_doc.get("snippet")
            or email_doc.get("content")
            or email_doc.get("text_body")
            or email_doc.get("subject")
            or ""
        )

        if isinstance(body, str):
            body_text = body.strip()
        else:
            body_text = str(body).strip()

        if not body_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email body is empty; cannot generate summary.",
            )

        # Step 4: Call Gemini API asynchronously using professional prompt
        generated_summary = await self._call_gemini_api(body_text)

        # Step 5: Store generated summary back into MongoDB inside the same email document
        updated = self.repository.update_summary(clean_id, generated_summary)
        if not updated:
            logger.warning(
                f"Failed to update summary in database for email_id='{clean_id}', "
                f"returning generated summary directly."
            )

        logger.info(
            f"Successfully generated and stored new summary for email_id='{clean_id}' via Gemini API."
        )

        return {
            "email_id": str(email_doc["_id"]),
            "summary": generated_summary,
            "cached": False,
        }

    async def _call_gemini_api(self, body_text: str) -> str:
        """
        Calls Google Gemini API asynchronously via HTTP POST request.
        Constructs a concise, professional summarization prompt.
        """
        api_key = getattr(settings, "GEMINI_API_KEY", "") or getattr(
            settings, "GEMINI_API", ""
        )
        if not api_key:
            logger.error("Gemini API key is not configured in environment settings.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API key is not configured on the server.",
            )

        model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        prompt = (
            "You are a professional executive email assistant. Summarize the following email body concisely "
            "in 2 to 3 clear sentences, highlighting key details, main topic, and any required action items.\n\n"
            f"Email Body:\n{body_text}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 300,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)

            if response.status_code != 200:
                logger.error(
                    f"Gemini API returned HTTP status {response.status_code}: {response.text}"
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Gemini API returned error status {response.status_code}.",
                )

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Gemini API returned an empty response candidate set.",
                )

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Malformed response format received from Gemini API.",
                )

            summary_text = parts[0]["text"].strip()
            if not summary_text:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Generated summary from Gemini API was empty.",
                )

            return summary_text

        except httpx.TimeoutException:
            logger.error("Timeout occurred while calling Gemini API.")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request to Gemini API timed out.",
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error while communicating with Gemini API: {exc!s}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Network error communicating with Gemini API: {exc!s}",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred during email summarization: {e!s}",
            )
