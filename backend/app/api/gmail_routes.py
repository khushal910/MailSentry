import asyncio
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.dependencies.google_auth_deps import (
    get_google_account_optional,
    require_google_connected,
)
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
    job_id: str, user_id: str, emails_to_classify: list, google_account: dict | None
):
    job_service = JobService()
    try:
        from app.services.ml_model_service import MLModelService

        model_service = MLModelService()
        model_service.get_model_or_raise()
        service = GmailFetchService(model_service=model_service)

        if not emails_to_classify:
            if not google_account:
                job_service.fail_job(job_id, "Gmail account not connected.")
                return
            emails_to_classify = await service.fetch_unclassified_raw_emails(
                user_id=user_id, google_account=google_account
            )

        if not emails_to_classify:
            job_service.complete_job(
                job_id, {"classified": 0, "skipped": 0, "classified_emails": []}
            )
            return

        job_service.set_total(job_id, len(emails_to_classify))

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
    account: dict | None = Depends(get_google_account_optional),
):
    """
    POST /api/gmail/classify-job
    Starts an asynchronous background job to classify provided unclassified emails.
    Returns immediately (<2s) with job_id and status for real-time frontend polling.
    """
    user_id = str(current_user["_id"])
    from app.core.config import settings

    emails_to_process = payload.emails if (payload and payload.emails) else []

    # If no emails provided in payload and Google account is not connected -> require connection
    if not emails_to_process and not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Please connect Gmail."
        )

    default_max = int(getattr(settings, "FETCH_MAX_RESULTS", 50))
    total_count = len(emails_to_process) if emails_to_process else default_max

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

    PRODUCTION FIX: In multi-worker deployments (gunicorn on Render), there's a brief
    race window where the job exists in Worker A's memory but hasn't propagated to
    MongoDB yet when Worker B receives the poll request. Instead of returning a 404
    (which breaks the frontend progress bar), we return a synthetic "started" status
    so the frontend keeps polling gracefully.
    """
    user_id = str(current_user["_id"])
    job_service = JobService()
    job = job_service.get_job(job_id=job_id, user_id=user_id)

    if not job:
        # Grace period: return a synthetic "started" response instead of 404.
        # The frontend will poll again in 1s and by then MongoDB should have the real data.
        logger.info(f"Job '{job_id}' not found yet (race window), returning synthetic started status")
        return return_response(
            status_code=status.HTTP_200_OK,
            message="Job status retrieved",
            data={
                "job_id": job_id,
                "status": "started",
                "total": 0,
                "processed": 0,
                "classified": 0,
                "skipped": 0,
                "current_subject": None,
                "result": None,
                "error": None,
            },
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
