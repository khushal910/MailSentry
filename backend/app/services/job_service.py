import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("mailsentry.job_service")


class ClassificationJob:
    """
    Represents an asynchronous email classification job with real-time progress tracking.
    """

    def __init__(self, job_id: str, user_id: str, total: int):
        self.job_id = job_id
        self.user_id = user_id
        self.status = "started"  # started, running, completed, failed
        self.total = total
        self.processed = 0
        self.classified_count = 0
        self.skipped_count = 0
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "classified": self.classified_count,
            "skipped": self.skipped_count,
            "result": self.result,
            "error": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class JobService:
    """
    Singleton service for creating, updating, retrieving, and auto-expiring background classification jobs.
    """

    _instance = None
    _jobs: Dict[str, ClassificationJob] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobService, cls).__new__(cls)
        return cls._instance

    def create_job(self, user_id: str, total: int) -> ClassificationJob:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = ClassificationJob(job_id=job_id, user_id=user_id, total=total)
        self._jobs[job_id] = job
        self._cleanup_old_jobs()
        return job

    def get_job(self, job_id: str, user_id: Optional[str] = None) -> Optional[ClassificationJob]:
        job = self._jobs.get(job_id)
        if job and user_id and job.user_id != user_id:
            return None
        return job

    def update_progress(
        self,
        job_id: str,
        processed_increment: int,
        classified_increment: int = 0,
        skipped_increment: int = 0,
    ) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "running"
            job.processed = min(job.total, job.processed + processed_increment)
            job.classified_count += classified_increment
            job.skipped_count += skipped_increment
            job.updated_at = datetime.now(timezone.utc)

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "completed"
            job.processed = job.total
            job.result = result
            job.updated_at = datetime.now(timezone.utc)

    def fail_job(self, job_id: str, error_message: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "failed"
            job.error_message = error_message
            job.updated_at = datetime.now(timezone.utc)

    def _cleanup_old_jobs(self) -> None:
        now = datetime.now(timezone.utc)
        expired_ids = [
            jid for jid, j in self._jobs.items()
            if (now - j.created_at).total_seconds() > 3600
        ]
        for jid in expired_ids:
            self._jobs.pop(jid, None)
