from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.dependencies.google_auth_deps import require_google_connected
from app.services.gmail_fetch_service import GmailFetchService
from app.utils.main_utile import return_response

gmail_router = APIRouter()


@gmail_router.post("/fetch", summary="Fetch and classify emails from Gmail")
async def fetch_emails(
    current_user: dict = Depends(get_current_user),
    account: dict = Depends(require_google_connected),
):
    """
    POST /api/gmail/fetch
    Fetches new emails from Gmail and classifies them using the ML model.

    Enforces:
    - Per-user concurrency lock (one fetch at a time)
    - Rate limit: once every FETCH_RATE_LIMIT_SECONDS (default 5 min)
    - Token auto-refresh; on revocation → disconnects account, returns 403
    - Partial-failure tolerance: one bad email never aborts the batch

    Returns:
        fetched    — number of emails retrieved from Gmail
        classified — number successfully classified and stored
        skipped    — number that failed classification (logged individually)
    """
    user_id = str(current_user["_id"])
    service = GmailFetchService()
    result = await service.run_fetch_pipeline(user_id=user_id, google_account=account)
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails fetched successfully",
        data=result.to_dict(),
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
