import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.email_repository import EmailRepository
from app.services.summary_service import SummaryService

logger = logging.getLogger(__name__)


class EmailSummaryService:
    """
    Business logic layer for Lazy Email Summarization using Google Gemini API.
    Follows clean architecture and dependency injection.
    """

    def __init__(
        self,
        repository: EmailRepository | None = None,
        summary_service: SummaryService | None = None,
    ):
        self.repository = repository if repository is not None else EmailRepository()
        self.summary_service = (
            summary_service if summary_service is not None else SummaryService()
        )

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
                "summary_created_at": email_doc.get("summary_created_at"),
                "summary_model": email_doc.get("summary_model"),
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

        # Step 4: Call Gemini API asynchronously using SummaryService
        generated_summary = await self._call_gemini_api(body_text)
        summary_model = getattr(self.summary_service, "model_name", "gemini-2.5-flash")
        summary_created_at = datetime.now(timezone.utc)

        # Step 5: Store generated summary, summary_created_at, and summary_model back into MongoDB inside the same email document
        updated = self.repository.update_summary(
            email_id=clean_id,
            summary=generated_summary,
            summary_model=summary_model,
            summary_created_at=summary_created_at,
        )
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
            "summary_created_at": summary_created_at.isoformat(),
            "summary_model": summary_model,
            "cached": False,
        }

    async def _call_gemini_api(self, body_text: str) -> str:
        """
        Delegates Gemini API call to the reusable SummaryService.
        """
        return await self.summary_service.generate_summary(body_text)

