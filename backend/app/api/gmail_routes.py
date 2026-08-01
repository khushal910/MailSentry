from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.dependencies.google_auth_deps import require_google_connected
from app.services.gmail_fetch_service import GmailFetchService
from app.utils.main_utile import return_response

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ClassifyBatchRequest(BaseModel):
    emails: Optional[List[Dict[str, Any]]] = Field(default=[], description="List of unclassified raw emails to classify")

gmail_router = APIRouter()


@gmail_router.post("/fetch-unclassified", summary="Fetch unclassified raw emails from Gmail")
async def fetch_unclassified_emails(
    current_user: dict = Depends(get_current_user),
    account: dict = Depends(require_google_connected),
):
    """
    POST /api/gmail/fetch-unclassified
    Fetches up to 50 latest raw emails from Gmail that do NOT exist in MongoDB EmailPrediction.
    Does NOT classify or save predictions to MongoDB yet.
    """
    user_id = str(current_user["_id"])
    service = GmailFetchService()
    unclassified = await service.fetch_unclassified_raw_emails(user_id=user_id, google_account=account)
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Unclassified emails fetched successfully",
        data={
            "fetched": len(unclassified),
            "unclassified_emails": unclassified
        }
    )


@gmail_router.post("/fetch", summary="Fetch and classify emails from Gmail")
async def fetch_emails(
    current_user: dict = Depends(get_current_user),
    account: dict = Depends(require_google_connected),
):
    """
    POST /api/gmail/fetch
    Fetches new emails from Gmail and classifies them using the ML model.
    """
    user_id = str(current_user["_id"])
    service = GmailFetchService()
    result = await service.run_fetch_pipeline(user_id=user_id, google_account=account)
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails fetched successfully",
        data=result.to_dict(),
    )


@gmail_router.post("/classify", summary="Classify provided unclassified emails")
async def classify_emails(
    payload: Optional[ClassifyBatchRequest] = None,
    current_user: dict = Depends(get_current_user),
    account: dict = Depends(require_google_connected),
):
    """
    POST /api/gmail/classify
    Runs ML model classification on provided unclassified emails (or pending Gmail queue),
    saves prediction records to MongoDB with full metadata, and returns classified results.
    """
    from app.services.ml_model_service import MLModelService
    model_service = MLModelService()
    model_service.get_model_or_raise()

    user_id = str(current_user["_id"])
    service = GmailFetchService(model_service=model_service)

    emails_to_process = payload.emails if (payload and payload.emails) else []

    if not emails_to_process:
        # Fallback: fetch unclassified emails from Gmail directly
        emails_to_process = await service.fetch_unclassified_raw_emails(user_id=user_id, google_account=account)

    result = service.classify_and_save_batch(user_id=user_id, emails_to_classify=emails_to_process)

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails classified and stored successfully",
        data=result
    )


@gmail_router.post("/summarize", summary="Summarize emails")
async def summarize_emails(account: dict = Depends(require_google_connected)):
    """
    POST /api/gmail/summarize
    Verifies Gmail connection prior to summarizing emails.
    """
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails summarized successfully",
        data={"google_email": account.get("google_email"), "summary": ""}
    )


@gmail_router.post("/schedule-meeting", summary="Schedule meeting from email")
async def schedule_meeting(account: dict = Depends(require_google_connected)):
    """
    POST /api/gmail/schedule-meeting
    Verifies Gmail connection prior to scheduling a meeting.
    """
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Meeting scheduled successfully",
        data={"google_email": account.get("google_email"), "event": None}
    )
