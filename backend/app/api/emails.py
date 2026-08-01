from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, List
from bson import ObjectId

from app.dependencies.auth import get_current_user
from app.repositories.email_repository import EmailRepository
from app.utils.main_utile import return_response

emails_router = APIRouter()

# Safe fields to expose to the frontend (no tokens, no raw body, no sensitive IDs)
_SAFE_FIELDS = {
    "message_id",
    "thread_id",
    "subject",
    "snippet",
    "predicted_label",
    "predicted_score",
    "fetch_time",
    "classified_at",
    "received_at",
    "sent_at",
}


MAX_LIMIT = 100


def _sanitize_email(doc: dict) -> dict:
    """
    Strips all sensitive/internal fields, returning only UI-safe fields.
    ObjectId values are converted to strings.
    """
    result = {}
    for key in _SAFE_FIELDS:
        if key in doc:
            val = doc[key]
            # Convert ObjectId to string if needed
            if isinstance(val, ObjectId):
                val = str(val)
            result[key] = val
    return result


@emails_router.get("/emails", summary="Get classified emails for authenticated user")
async def get_user_emails(
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT, description="Number of emails per page (max 100)"),
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    label: Optional[str] = Query(default=None, description="Filter by predicted label (e.g. 'spam', 'important')"),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/emails
    Returns paginated, classified emails for the authenticated user.
    Only safe UI fields are returned — no raw bodies, tokens, or sensitive IDs.

    Query parameters:
    - limit: how many emails to return per page (1-100, default 20)
    - page: page number starting from 1 (default 1)
    - label: optional filter by predicted_label
    """
    user_id = str(current_user["_id"])
    skip = (page - 1) * limit

    repo = EmailRepository()
    raw_emails = repo.get_user_emails(
        user_id=user_id,
        predicted_label=label or None,
        limit=limit,
        skip=skip
    )

    emails = [_sanitize_email(doc) for doc in raw_emails]

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails retrieved successfully",
        data={
            "emails": emails,
            "page": page,
            "limit": limit,
            "count": len(emails)
        }
    )
