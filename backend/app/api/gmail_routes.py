from fastapi import APIRouter, Depends, status
from app.dependencies.google_auth_deps import require_google_connected
from app.utils.main_utile import return_response

gmail_router = APIRouter()


@gmail_router.post("/fetch", summary="Fetch emails from Gmail")
async def fetch_emails(account: dict = Depends(require_google_connected)):
    """
    POST /api/gmail/fetch
    Verifies Gmail connection prior to fetching emails.
    """
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails fetched successfully",
        data={"google_email": account.get("google_email"), "emails": []}
    )


@gmail_router.post("/classify", summary="Classify emails")
async def classify_emails(account: dict = Depends(require_google_connected)):
    """
    POST /api/gmail/classify
    Verifies Gmail connection prior to classifying emails.
    Verifies ML model availability; returns 500 error if model file is missing or corrupted.
    """
    from app.services.ml_model_service import MLModelService
    model_service = MLModelService()
    # Raises HTTPException(500, detail="ML classification model is not available") if missing/corrupted
    model = model_service.get_model_or_raise()

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails classified successfully",
        data={"google_email": account.get("google_email"), "classifications": []}
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
