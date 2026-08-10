import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("mailsentry.job_service")


def _get_jobs_collection():
    try:
        from app.db.mongodb import get_database

        db = get_database()
        if db is not None:
            coll = db["classification_jobs"]
            try:
                coll.create_index("job_id", unique=True, name="uniq_job_id")
                coll.create_index("created_at", expireAfterSeconds=3600, name="ttl_created_at")
            except Exception:
                pass
            return coll
    except Exception:
        pass
    return None


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
        self.current_subject: str | None = None
        self.result: dict[str, Any] | None = None
        self.error_message: str | None = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClassificationJob":
        job = cls(
            job_id=data.get("job_id", ""),
            user_id=data.get("user_id", ""),
            total=data.get("total", 1),
        )
        job.status = data.get("status", "started")
        job.processed = data.get("processed", 0)
        job.classified_count = data.get("classified", 0)
        job.skipped_count = data.get("skipped", 0)
        job.current_subject = data.get("current_subject")
        job.result = data.get("result")
        job.error_message = data.get("error")

        ca = data.get("created_at")
        if isinstance(ca, datetime):
            job.created_at = ca
        elif isinstance(ca, str) and ca.strip():
            try:
                job.created_at = datetime.fromisoformat(ca.replace("Z", "+00:00"))
            except Exception:
                pass

        ua = data.get("updated_at")
        if isinstance(ua, datetime):
            job.updated_at = ua
        elif isinstance(ua, str) and ua.strip():
            try:
                job.updated_at = datetime.fromisoformat(ua.replace("Z", "+00:00"))
            except Exception:
                pass

        return job

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "classified": self.classified_count,
            "skipped": self.skipped_count,
            "current_subject": self.current_subject,
            "result": self.result,
            "error": self.error_message,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else str(self.updated_at),
        }


class JobService:
    """
    Singleton service for creating, updating, retrieving, and auto-expiring background classification jobs.
    Persists jobs to MongoDB classification_jobs collection for multi-worker process compatibility.
    """

    _instance = None
    _jobs: dict[str, ClassificationJob] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _sync_to_db(self, job: ClassificationJob) -> None:
        try:
            coll = _get_jobs_collection()
            if coll is not None:
                coll.update_one(
                    {"job_id": job.job_id},
                    {"$set": job.to_dict()},
                    upsert=True,
                )
        except Exception as err:
            logger.warning(f"Failed to sync job {job.job_id} to MongoDB: {err}")

    def create_job(self, user_id: str, total: int) -> ClassificationJob:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = ClassificationJob(job_id=job_id, user_id=user_id, total=total)
        self._jobs[job_id] = job
        self._sync_to_db(job)
        self._cleanup_old_jobs()
        return job

    def get_job(
        self, job_id: str, user_id: str | None = None
    ) -> ClassificationJob | None:
        job = self._jobs.get(job_id)
        if not job:
            try:
                coll = _get_jobs_collection()
                if coll is not None:
                    doc = coll.find_one({"job_id": job_id})
                    if doc:
                        job = ClassificationJob.from_dict(doc)
                        self._jobs[job_id] = job
            except Exception as err:
                logger.warning(f"Failed to query job {job_id} from MongoDB: {err}")

        if job and user_id and job.user_id != user_id:
            return None
        return job

    def set_total(self, job_id: str, total: int) -> None:
        job = self.get_job(job_id)
        if job:
            job.total = max(1, total)
            if job.processed > job.total:
                job.processed = job.total
            job.updated_at = datetime.now(timezone.utc)
            self._jobs[job_id] = job
            self._sync_to_db(job)

    def update_progress(
        self,
        job_id: str,
        processed_increment: int,
        classified_increment: int = 0,
        skipped_increment: int = 0,
        current_subject: str | None = None,
    ) -> None:
        job = self.get_job(job_id)
        if job:
            job.status = "running"
            job.processed = min(job.total, job.processed + processed_increment)
            job.classified_count += classified_increment
            job.skipped_count += skipped_increment
            if current_subject:
                job.current_subject = current_subject
            job.updated_at = datetime.now(timezone.utc)
            self._jobs[job_id] = job
            self._sync_to_db(job)

    def complete_job(self, job_id: str, result: dict[str, Any]) -> None:
        job = self.get_job(job_id)
        if job:
            job.status = "completed"
            job.processed = job.total
            job.result = result
            job.updated_at = datetime.now(timezone.utc)
            self._jobs[job_id] = job
            self._sync_to_db(job)

    def fail_job(self, job_id: str, error_message: str) -> None:
        job = self.get_job(job_id)
        if job:
            job.status = "failed"
            job.error_message = error_message
            job.updated_at = datetime.now(timezone.utc)
            self._jobs[job_id] = job
            self._sync_to_db(job)

    def _cleanup_old_jobs(self) -> None:
        now = datetime.now(timezone.utc)
        expired_ids = [
            jid
            for jid, j in self._jobs.items()
            if isinstance(j.created_at, datetime) and (now - j.created_at).total_seconds() > 3600
        ]
        for jid in expired_ids:
            self._jobs.pop(jid, None)

