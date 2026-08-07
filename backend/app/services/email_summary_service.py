import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.email_repository import EmailRepository
from app.services.summary_service import SummaryService

logger = logging.getLogger(__name__)

# In-memory per-email locks to prevent duplicate concurrent Gemini API calls
_EMAIL_LOCKS: dict[str, asyncio.Lock] = {}
_LOCKS_GUARD = asyncio.Lock()


async def _get_email_lock(email_id: str) -> asyncio.Lock:
    async with _LOCKS_GUARD:
        if email_id not in _EMAIL_LOCKS:
            _EMAIL_LOCKS[email_id] = asyncio.Lock()
        return _EMAIL_LOCKS[email_id]


class EmailSummaryService:
    """
    Business logic layer for Lazy Email Summarization using Google Gemini API.
    Follows clean architecture, double-checked concurrency locking, and dependency injection.
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

    def _extract_clean_email(self, *candidates: Any) -> str:
        for cand in candidates:
            if not cand or not isinstance(cand, str):
                continue
            cleaned = cand.strip()
            # Filter out raw MongoDB ObjectIds or 24-character hex IDs
            if ObjectId.is_valid(cleaned) or (len(cleaned) == 24 and all(c in "0123456789abcdefABCDEF" for c in cleaned)):
                continue
            if "@" in cleaned or "." in cleaned:
                return cleaned
            if cleaned and not cleaned.isalnum():
                return cleaned
        return ""

    def _format_summary_response(
        self,
        email_doc: dict[str, Any],
        summary_text: str,
        is_cached: bool,
        summary_created_at: str | None = None,
        summary_model: str | None = None,
    ) -> dict[str, Any]:
        doc_id = str(email_doc.get("_id", ""))
        created_at_val = (
            summary_created_at
            or email_doc.get("summary_created_at")
            or datetime.now(timezone.utc).isoformat()
        )
        if isinstance(created_at_val, datetime):
            created_at_val = created_at_val.isoformat()

        model_val = (
            summary_model
            or email_doc.get("summary_model")
            or getattr(self.summary_service, "model_name", "gemini-2.5-flash")
        )

        sender_val = self._extract_clean_email(
            email_doc.get("sender"),
            email_doc.get("from"),
            email_doc.get("sender_email"),
            email_doc.get("from_email"),
        )

        receiver_val = self._extract_clean_email(
            email_doc.get("receiver"),
            email_doc.get("to"),
            email_doc.get("recipient"),
            email_doc.get("receiver_email"),
            email_doc.get("user_email"),
        )

        return {
            "email_id": doc_id,
            "subject": email_doc.get("subject", ""),
            "sender": sender_val or "Unknown Sender",
            "receiver": receiver_val or "Authenticated User",
            "predicted_label": email_doc.get("predicted_label") or email_doc.get("prediction", "ham"),
            "predicted_score": email_doc.get("predicted_score"),
            "sent_at": email_doc.get("sent_at") or email_doc.get("received_at") or email_doc.get("classified_at"),
            "body": email_doc.get("body") or email_doc.get("snippet") or "",
            "summary": summary_text.strip(),
            "summary_created_at": created_at_val,
            "summary_model": model_val,
            "cached": is_cached,
            "message_id": email_doc.get("message_id"),
            "thread_id": email_doc.get("thread_id"),
        }

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
        4. Double-Checked Lock: Prevents duplicate API calls if 2 requests arrive concurrently.
        5. Generates summary via Gemini, stores in MongoDB, and returns summary.
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

        # Security check: if current_user_id provided, verify email ownership
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
            return self._format_summary_response(email_doc, existing_summary.strip(), is_cached=True)

        # Step 3: Concurrency protection (Double-Checked Locking)
        # Prevents duplicate Gemini API calls if two requests arrive simultaneously
        lock = await _get_email_lock(clean_id)
        async with lock:
            # Re-query DB after lock acquisition to check if another concurrent request already generated it
            rechecked_doc = self.repository.find_by_id(clean_id) or email_doc
            rechecked_summary = rechecked_doc.get("summary")
            if (
                rechecked_summary is not None
                and isinstance(rechecked_summary, str)
                and rechecked_summary.strip()
            ):
                logger.info(
                    f"Summary for email_id='{clean_id}' was generated by concurrent request. "
                    f"Returning cached summary without calling Gemini API."
                )
                return self._format_summary_response(rechecked_doc, rechecked_summary.strip(), is_cached=True)

            # Step 4: Extract email body for summarization
            body = (
                rechecked_doc.get("body")
                or rechecked_doc.get("snippet")
                or rechecked_doc.get("content")
                or rechecked_doc.get("text_body")
                or rechecked_doc.get("subject")
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

            # Step 5: Call configured LLM API asynchronously using SummaryService
            generated_summary = await self._call_gemini_api(body_text)
            summary_model = getattr(self.summary_service, "model_name", "llama-3.3-70b-versatile")
            summary_created_at = datetime.now(timezone.utc)

            # Step 6: Store generated summary, summary_created_at, and summary_model in MongoDB
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
                f"Successfully generated and stored new summary for email_id='{clean_id}' via LLM provider '{self.summary_service.provider_name}'."
            )

            return self._format_summary_response(
                rechecked_doc,
                generated_summary,
                is_cached=False,
                summary_created_at=summary_created_at.isoformat(),
                summary_model=summary_model,
            )

    async def _call_gemini_api(self, body_text: str) -> str:
        """
        Delegates LLM API call to the reusable SummaryService.
        """
        return await self.summary_service.generate_summary(body_text)

    # Alias for modern LLM provider naming
    _call_llm_api = _call_gemini_api

