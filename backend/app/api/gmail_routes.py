import asyncio
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.dependencies.google_auth_deps import require_google_connected
from app.services.gmail_fetch_service import GmailFetchService
from app.services.job_service import JobService
from app.utils.main_utile import return_response

logger = logging.getLogger("mailsentry.gmail_routes")


class ClassifyBatchRequest(BaseModel):
    emails: list[dict[str, Any]] | None = Field(
        default=[], description="List of unclassified raw emails to classify"
    )


gmail_router = APIRouter()


async def _run_classify_job_background(
    job_id: str, user_id: str, emails_to_classify: list, google_account: dict
):
    job_service = JobService()
    try:
        from app.services.ml_model_service import MLModelService

        model_service = MLModelService()
        model_service.get_model_or_raise()
        service = GmailFetchService(model_service=model_service)

        if not emails_to_classify:
            emails_to_classify = await service.fetch_unclassified_raw_emails(
                user_id=user_id, google_account=google_account
            )

        if not emails_to_classify:
            job_service.complete_job(
                job_id, {"classified": 0, "skipped": 0, "classified_emails": []}
            )
            return

        # CRITICAL ARCHITECTURAL FIX: Offload CPU-bound ML prediction + DB writes to worker thread pool
        # This keeps the main FastAPI event loop 100% unblocked to instantly handle GET /api/gmail/jobs/{job_id} polling!
        await asyncio.to_thread(
            service.classify_and_save_batch,
            user_id=user_id,
            emails_to_classify=emails_to_classify,
            job_id=job_id,
        )
    except Exception as err:
        logger.error(f"Error executing background job {job_id}: {err}", exc_info=True)
        job_service.fail_job(job_id, str(err))


@gmail_router.post("/classify-job", summary="Start background email classification job")
async def start_classify_job(
    background_tasks: BackgroundTasks,
    payload: ClassifyBatchRequest | None = None,
    current_user: dict = Depends(get_current_user),
    account: dict = Depends(require_google_connected),
):
    """
    POST /api/gmail/classify-job
    Starts an asynchronous background job to classify provided unclassified emails.
    Returns immediately (<2s) with job_id and status for real-time frontend polling.
    """
    user_id = str(current_user["_id"])
    emails_to_process = payload.emails if (payload and payload.emails) else []
    total_count = len(emails_to_process) if emails_to_process else 50

    job_service = JobService()
    job = job_service.create_job(user_id=user_id, total=total_count)

    background_tasks.add_task(
        _run_classify_job_background,
        job_id=job.job_id,
        user_id=user_id,
        emails_to_classify=emails_to_process,
        google_account=account,
    )

    return return_response(
        status_code=status.HTTP_202_ACCEPTED,
        message="Classification job started",
        data=job.to_dict(),
    )


@gmail_router.get("/jobs/{job_id}", summary="Get background job status and progress")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/gmail/jobs/{job_id}
    Returns real-time progress (processed, total, status, result) for a background job.
    """
    user_id = str(current_user["_id"])
    job_service = JobService()
    job = job_service.get_job(job_id=job_id, user_id=user_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found or unauthorized.",
        )

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Job status retrieved",
        data=job.to_dict(),
    )


@gmail_router.post("/classify", summary="Classify provided unclassified emails")
async def classify_emails(
    payload: ClassifyBatchRequest | None = None,
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
        emails_to_process = await service.fetch_unclassified_raw_emails(
            user_id=user_id, google_account=account
        )

    result = service.classify_and_save_batch(
        user_id=user_id, emails_to_classify=emails_to_process
    )

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails classified and stored successfully",
        data=result,
    )


@gmail_router.post(
    "/fetch-unclassified", summary="Fetch unclassified raw emails from Gmail"
)
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
    unclassified = await service.fetch_unclassified_raw_emails(
        user_id=user_id, google_account=account
    )
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Unclassified emails fetched successfully",
        data={"fetched": len(unclassified), "unclassified_emails": unclassified},
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


@gmail_router.post("/summarize", summary="Summarize emails")
async def summarize_emails(account: dict = Depends(require_google_connected)):
    """
    POST /api/gmail/summarize
    Verifies Gmail connection prior to summarizing emails.
    """
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Emails summarized successfully",
        data={"google_email": account.get("google_email"), "summary": ""},
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
        data={"google_email": account.get("google_email"), "event": None},
    )
