from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_user
from app.repositories.email_repository import EmailRepository
from app.utils.main_utile import return_response

emails_router = APIRouter()

# Safe fields to expose to the frontend (no tokens, no raw body, no sensitive IDs)
_SAFE_FIELDS = {
    "id",
    "email_id",
    "message_id",
    "thread_id",
    "subject",
    "snippet",
    "sender",
    "receiver",
    "from",
    "to",
    "predicted_label",
    "predicted_score",
    "gmail_classification",
    "fetch_time",
    "classified_at",
    "received_at",
    "sent_at",
    "summary",
    "summary_created_at",
    "summary_model",
}


MAX_LIMIT = 100


def _extract_clean_email(*candidates: Any) -> str:
    for cand in candidates:
        if not cand or not isinstance(cand, str):
            continue
        cleaned = cand.strip()
        if ObjectId.is_valid(cleaned) or (len(cleaned) == 24 and all(c in "0123456789abcdefABCDEF" for c in cleaned)):
            continue
        if "@" in cleaned or "." in cleaned:
            return cleaned
        if cleaned and not cleaned.isalnum():
            return cleaned
    return ""


def _sanitize_email(doc: dict) -> dict:
    """
    Strips all sensitive/internal fields, returning only UI-safe fields.
    ObjectId values are converted to strings, and datetime objects are converted to ISO 8601 UTC strings.
    """
    result = {}
    for key in _SAFE_FIELDS:
        if key in doc:
            val = doc[key]
            # Convert ObjectId to string if needed
            if isinstance(val, ObjectId):
                val = str(val)
            elif isinstance(val, datetime):
                if val.tzinfo is None:
                    val = val.replace(tzinfo=timezone.utc)
                iso_str = val.isoformat()
                if (
                    not iso_str.endswith("Z")
                    and "+" not in iso_str
                    and "-" not in iso_str[10:]
                ):
                    iso_str += "Z"
                val = iso_str
            result[key] = val

    # Ensure doc ID is present as clean UI id / email_id without exposing internal _id
    if "_id" in doc:
        doc_id_str = str(doc["_id"])
        if "id" not in result:
            result["id"] = doc_id_str
        if "email_id" not in result:
            result["email_id"] = doc_id_str

    # Ensure sender and receiver are cleaned
    if not result.get("sender"):
        clean_sender = _extract_clean_email(doc.get("sender"), doc.get("from"), doc.get("sender_email"), doc.get("from_email"))
        if clean_sender:
            result["sender"] = clean_sender

    if not result.get("receiver"):
        clean_receiver = _extract_clean_email(doc.get("receiver"), doc.get("to"), doc.get("recipient"), doc.get("receiver_email"))
        if clean_receiver:
            result["receiver"] = clean_receiver

    # Guarantee gmail_classification is present even for legacy database records
    if "gmail_classification" not in result or result["gmail_classification"] is None:
        label_ids = doc.get("label_ids", [])
        is_spam = "SPAM" in label_ids
        result["gmail_classification"] = {
            "is_spam": is_spam,
            "status": "spam" if is_spam else "not_spam",
            "label_ids": label_ids,
        }

    return result



@emails_router.get("/emails", summary="Get classified emails for authenticated user")
async def get_user_emails(
    limit: int = Query(
        default=20,
        ge=1,
        le=MAX_LIMIT,
        description="Number of emails per page (max 100)",
    ),
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    label: str | None = Query(
        default=None, description="Filter by predicted label (e.g. 'spam', 'important')"
    ),
    search: str | None = Query(
        default=None,
        description="Search query string for subject, snippet, label, or sender",
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/emails
    Returns paginated, classified emails for the authenticated user.
    Only safe UI fields are returned — no raw bodies, tokens, or sensitive IDs.

    Query parameters:
    - limit: how many emails to return per page (1-100, default 20)
    - page: page number starting from 1 (default 1)
    - label: optional filter by predicted_label
    - search: optional search query string
    """
    user_id = str(current_user["_id"])
    skip = (page - 1) * limit

    repo_kwargs = {
        "user_id": user_id,
        "predicted_label": label or None,
        "limit": limit,
        "skip": skip,
    }
    count_kwargs = {
        "user_id": user_id,
        "predicted_label": label or None,
    }
    if search and search.strip():
        repo_kwargs["search"] = search.strip()
        count_kwargs["search"] = search.strip()

    repo = EmailRepository()
    raw_emails = repo.get_user_emails(**repo_kwargs)
    total_count = repo.count_user_emails(**count_kwargs)

    emails = [_sanitize_email(doc) for doc in raw_emails]

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails retrieved successfully",
        data={
            "emails": emails,
            "page": page,
            "limit": limit,
            "count": len(emails),
            "total_count": total_count,
            "total": total_count,
        },
    )


def get_email_repository() -> EmailRepository:
    return EmailRepository()


def get_email_summary_service(
    repo: EmailRepository = Depends(get_email_repository),
):
    from app.services.email_summary_service import EmailSummaryService

    return EmailSummaryService(repository=repo)


@emails_router.get(
    "/emails/{email_id}/summary",
    summary="Get or generate concise summary for an email",
    status_code=status.HTTP_200_OK,
)
async def get_email_summary(
    email_id: str,
    summary_service: Any = Depends(get_email_summary_service),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /emails/{email_id}/summary

    Retrieves or lazily generates a concise summary for an email document.
    - If a non-empty 'summary' field exists in MongoDB, returns it immediately without calling Gemini API.
    - If 'summary' does not exist, reads the email body, sends it to Gemini API using a professional prompt,
      stores the generated summary back into MongoDB in the same document, and returns it.
    """
    user_id = str(current_user["_id"])
    result = await summary_service.get_or_generate_summary(
        email_id=email_id, current_user_id=user_id
    )
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Email summary retrieved successfully",
        data=result,
    )

