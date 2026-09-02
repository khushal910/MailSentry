"""
GmailFetchService
=================
Central service that owns the complete Gmail fetch-and-classify pipeline.

Pipeline steps (in order):
  1. Concurrency lock  — one fetch per user at a time (asyncio.Lock + TTL)
  2. Rate limit        — at most one fetch per FETCH_RATE_LIMIT_SECONDS (default 5 min)
  3. Token validation  — refresh access token; on 401/revoke → disconnect + raise 403
  4. Email fetch stub  — placeholder for real Gmail API call
  5. Classify & save   — partial-failure tolerant; one email error never aborts the batch
  6. Structured log    — one INFO summary per run
"""

import asyncio
import base64
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.email_repository import EmailRepository
from app.repositories.google_account_repository import GoogleAccountRepository
from app.services.gmail_token_manager import GmailTokenManager
from app.services.ml_model_service import MLModelService

logger = logging.getLogger("mailsentry.gmail_fetch")


def _extract_full_body(payload: dict[str, Any]) -> str:
    """
    Recursively extracts full body text (plain text or html fallback) from Gmail API payload.
    """
    if not payload:
        return ""

    def _decode_data(data_str: str) -> str:
        if not data_str:
            return ""
        try:
            padded = data_str + "=" * (-len(data_str) % 4)
            return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
        except Exception:
            return ""

    body_obj = payload.get("body", {})
    mime_type = payload.get("mimeType", "")

    if body_obj.get("data") and mime_type == "text/plain":
        return _decode_data(body_obj.get("data"))

    parts = payload.get("parts", [])
    for part in parts:
        part_mime = part.get("mimeType", "")
        if part_mime == "text/plain" and part.get("body", {}).get("data"):
            text = _decode_data(part["body"]["data"])
            if text.strip():
                return text
        elif part.get("parts"):
            res = _extract_full_body(part)
            if res.strip():
                return res

    if body_obj.get("data") and "text/html" in mime_type:
        raw_html = _decode_data(body_obj.get("data"))
        return re.sub(r"<.*?>", " ", raw_html)

    for part in parts:
        part_mime = part.get("mimeType", "")
        if "text/html" in part_mime and part.get("body", {}).get("data"):
            raw_html = _decode_data(part["body"]["data"])
            return re.sub(r"<.*?>", " ", raw_html)

    return ""

# ──────────────────────────────────────────────────────────────────────────────
# Process-level state (single-worker safe)
# ──────────────────────────────────────────────────────────────────────────────

# Per-user asyncio locks: {user_id: asyncio.Lock}
_USER_LOCKS: dict[str, asyncio.Lock] = {}

# Per-user lock acquisition timestamps for TTL expiry: {user_id: datetime}
_LOCK_ACQUIRED_AT: dict[str, datetime] = {}

# Per-user last successful fetch timestamp for rate limiting: {user_id: datetime}
_LAST_FETCH_AT: dict[str, datetime] = {}


def _get_user_lock(user_id: str) -> asyncio.Lock:
    """Returns (or creates) the asyncio.Lock for this user."""
    if user_id not in _USER_LOCKS:
        _USER_LOCKS[user_id] = asyncio.Lock()
    return _USER_LOCKS[user_id]


def _is_lock_expired(user_id: str) -> bool:
    """Returns True if the lock has been held longer than FETCH_LOCK_TTL_SECONDS."""
    acquired_at = _LOCK_ACQUIRED_AT.get(user_id)
    if not acquired_at:
        return False
    elapsed = (datetime.now(timezone.utc) - acquired_at).total_seconds()
    ttl = int(getattr(settings, "FETCH_LOCK_TTL_SECONDS", 60))
    return elapsed > ttl


def _is_rate_limited(user_id: str) -> bool:
    """Returns True if this user's last fetch was less than FETCH_RATE_LIMIT_SECONDS ago."""
    if not getattr(settings, "FETCH_RATE_LIMIT_SECONDS_APPLY", True):
        return False

    last = _LAST_FETCH_AT.get(user_id)
    if not last:
        return False
    elapsed = (datetime.now(timezone.utc) - last).total_seconds()
    window = int(getattr(settings, "FETCH_RATE_LIMIT_SECONDS", 300))
    return elapsed < window


def _seconds_until_allowed(user_id: str) -> int:
    """Returns the number of seconds the user must wait before the next fetch."""
    if not getattr(settings, "FETCH_RATE_LIMIT_SECONDS_APPLY", True):
        return 0

    last = _LAST_FETCH_AT.get(user_id)
    if not last:
        return 0
    window = int(getattr(settings, "FETCH_RATE_LIMIT_SECONDS", 300))
    elapsed = (datetime.now(timezone.utc) - last).total_seconds()
    remaining = int(window - elapsed)
    return max(remaining, 0)


# ──────────────────────────────────────────────────────────────────────────────
# Fetch result type
# ──────────────────────────────────────────────────────────────────────────────


class FetchResult:
    def __init__(
        self,
        fetched: int = 0,
        classified: int = 0,
        skipped: int = 0,
        new_emails: list | None = None,
    ):
        self.fetched = fetched
        self.classified = classified
        self.skipped = skipped
        self.new_emails = new_emails or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "fetched": self.fetched,
            "classified": self.classified,
            "skipped": self.skipped,
            "new_emails": self.new_emails,
        }


# ──────────────────────────────────────────────────────────────────────────────
# GmailFetchService
# ──────────────────────────────────────────────────────────────────────────────


class GmailFetchService:
    """
    Orchestrates the full Gmail fetch-and-classify pipeline with:
    - Per-user concurrency lock
    - Per-user rate limiting
    - Token refresh / 401 handling with automatic disconnect
    - Partial-failure tolerant classification loop
    - Structured fetch summary logging
    """

    def __init__(
        self,
        email_repo: EmailRepository | None = None,
        google_repo: GoogleAccountRepository | None = None,
        token_manager: GmailTokenManager | None = None,
        model_service: MLModelService | None = None,
    ):
        self.email_repo = email_repo or EmailRepository()
        self.google_repo = google_repo or GoogleAccountRepository()
        self.token_manager = token_manager or GmailTokenManager(repo=self.google_repo)
        self.model_service = model_service or MLModelService()

    # ── public entry point ────────────────────────────────────────────────────

    async def run_fetch_pipeline(
        self, user_id: str, google_account: dict[str, Any]
    ) -> FetchResult:
        """
        Run the full pipeline. Raises HTTPException for terminal errors (rate limit,
        concurrency conflict, token revocation). Returns FetchResult on success.
        """
        self._check_rate_limit(user_id)
        return await self._run_with_lock(user_id, google_account)

    # ── rate limit ────────────────────────────────────────────────────────────

    def _check_rate_limit(self, user_id: str) -> None:
        if _is_rate_limited(user_id):
            wait = _seconds_until_allowed(user_id)
            logger.warning(
                f"[Fetch] user_id={user_id} rate-limited. "
                f"Next fetch allowed in {wait}s."
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait} seconds before refreshing again.",
            )

    # ── concurrency lock ──────────────────────────────────────────────────────

    async def _run_with_lock(
        self, user_id: str, google_account: dict[str, Any]
    ) -> FetchResult:
        lock = _get_user_lock(user_id)

        # If lock already held AND not expired → reject
        if lock.locked() and not _is_lock_expired(user_id):
            logger.warning(f"[Fetch] user_id={user_id} fetch already in progress.")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="A fetch is already in progress for your account. Please wait.",
            )

        async with lock:
            _LOCK_ACQUIRED_AT[user_id] = datetime.now(timezone.utc)
            try:
                result = await self._pipeline(user_id, google_account)
                # Record successful completion for rate-limiting
                _LAST_FETCH_AT[user_id] = datetime.now(timezone.utc)
                return result
            finally:
                _LOCK_ACQUIRED_AT.pop(user_id, None)

    # ── pipeline ──────────────────────────────────────────────────────────────

    async def _pipeline(
        self, user_id: str, google_account: dict[str, Any]
    ) -> FetchResult:
        google_email = google_account.get("google_email", "")

        # Step 1: Validate / refresh access token
        try:
            access_token = await self.token_manager.get_valid_access_token(google_email)
        except HTTPException as exc:
            if exc.status_code in (
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            ):
                # Token revoked or missing — mark account as disconnected
                self._disconnect_revoked_account(user_id, google_email)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Gmail access revoked. Please reconnect your account.",
                ) from exc
            raise

        # Step 2: Fetch unclassified emails from Gmail API
        raw_emails = await self._fetch_from_gmail(
            user_id=user_id,
            google_email=google_email,
            access_token=access_token,
        )

        result = FetchResult(fetched=len(raw_emails))

        if result.fetched == 0:
            logger.info(
                f"[Fetch] user_id={user_id} — no new emails found. "
                "fetched=0 classified=0 skipped=0"
            )
            return result

        # Step 3: Classify and save — partial-failure tolerant
        for raw in raw_emails:
            try:
                classified = self._classify_one(raw)
                gmail_cls = raw.get("gmail_classification")
                if not gmail_cls and "label_ids" in raw:
                    is_g_spam = "SPAM" in raw.get("label_ids", [])
                    gmail_cls = {
                        "is_spam": is_g_spam,
                        "status": "spam" if is_g_spam else "not_spam",
                    }

                email_doc = {
                    "user_id": user_id,
                    "message_id": raw["message_id"],
                    "thread_id": raw.get("thread_id"),
                    "subject": raw.get("subject", ""),
                    "snippet": raw.get("snippet", ""),
                    "predicted_label": classified["predicted_label"],
                    "predicted_score": classified["predicted_score"],
                    "gmail_classification": gmail_cls,
                    "fetch_time": datetime.now(timezone.utc),
                    "classified_at": datetime.fromisoformat(
                        classified["classified_at"]
                    ),
                    "received_at": raw.get("received_at") or raw.get("sent_at"),
                    "sent_at": raw.get("sent_at") or raw.get("received_at"),
                }
                self.email_repo.save_email(email_doc, check_access=False)
                result.classified += 1

                # Format for API response
                ui_doc = {
                    "message_id": raw["message_id"],
                    "thread_id": raw.get("thread_id"),
                    "subject": raw.get("subject", ""),
                    "snippet": raw.get("snippet", ""),
                    "predicted_label": classified["predicted_label"],
                    "predicted_score": classified["predicted_score"],
                    "gmail_classification": gmail_cls,
                    "fetch_time": email_doc["fetch_time"].isoformat(),
                    "classified_at": classified["classified_at"],
                    "received_at": raw.get("received_at") or raw.get("sent_at"),
                    "sent_at": raw.get("sent_at") or raw.get("received_at"),
                }
                result.new_emails.append(ui_doc)


            except Exception as err:
                result.skipped += 1
                logger.error(
                    f"[Fetch] user_id={user_id} message_id={raw.get('message_id')} "
                    f"skipped due to error: {err}",
                    exc_info=False,
                )

        logger.info(
            f"[Fetch] user_id={user_id} complete — "
            f"fetched={result.fetched} classified={result.classified} "
            f"skipped={result.skipped}"
        )
        return result

    async def fetch_unclassified_raw_emails(
        self, user_id: str, google_account: dict[str, Any]
    ) -> list:
        """
        Fetches up to 50 latest raw emails from Gmail whose message_id does NOT exist in MongoDB EmailPrediction.
        Does NOT run ML classification or save predictions to MongoDB yet.
        """
        google_email = google_account.get("google_email", "")
        access_token = await self.token_manager.get_valid_access_token(google_email)
        raw_emails = await self._fetch_from_gmail(
            user_id=user_id,
            google_email=google_email,
            access_token=access_token,
        )
        return raw_emails

    def classify_and_save_batch(
        self, user_id: str, emails_to_classify: list, job_id: str | None = None
    ) -> dict[str, Any]:
        """
        Classifies specified unclassified emails using ML model, saves records to MongoDB,
        updates progress on job_id if provided, and returns saved classified email documents.
        """
        from app.services.job_service import JobService

        job_service = JobService()

        classified_count = 0
        skipped_count = 0
        saved_records = []

        for raw in emails_to_classify:
            subject = raw.get("subject", "No subject")
            is_success = False
            try:
                classified = self._classify_one(raw)
                message_id = raw.get("message_id") or raw.get("gmail_message_id")
                if not message_id:
                    skipped_count += 1
                else:
                    now = datetime.now(timezone.utc)
                    class_at_str = classified.get("classified_at")
                    if isinstance(class_at_str, datetime):
                        classified_dt = class_at_str
                    elif isinstance(class_at_str, str) and class_at_str.strip():
                        try:
                            s = class_at_str.strip().replace("Z", "+00:00")
                            classified_dt = datetime.fromisoformat(s)
                        except Exception:
                            classified_dt = now
                    else:
                        classified_dt = now

                    gmail_cls = raw.get("gmail_classification")
                    if not gmail_cls and "label_ids" in raw:
                        is_g_spam = "SPAM" in raw.get("label_ids", [])
                        gmail_cls = {
                            "is_spam": is_g_spam,
                            "status": "spam" if is_g_spam else "not_spam",
                        }

                    email_doc = {
                        "user_id": user_id,
                        "message_id": message_id,
                        "gmail_message_id": message_id,
                        "thread_id": raw.get("thread_id"),
                        "subject": subject,
                        "snippet": raw.get("snippet", ""),
                        "sender": raw.get("sender")
                        or raw.get("from")
                        or raw.get("received_at"),
                        "predicted_label": classified.get("predicted_label", "ham"),
                        "prediction": classified.get("predicted_label", "ham"),
                        "predicted_score": classified.get("predicted_score", 0.85),
                        "confidence": classified.get("predicted_score", 0.85),
                        "gmail_classification": gmail_cls,
                        "fetch_time": now,
                        "classified_at": classified_dt,
                        "created_at": now,
                        "received_at": raw.get("received_at") or raw.get("sent_at"),
                        "sent_at": raw.get("sent_at") or raw.get("received_at"),
                    }
                    self.email_repo.save_email(email_doc, check_access=False)
                    classified_count += 1
                    is_success = True
                    saved_records.append(
                        {
                            "message_id": message_id,
                            "gmail_message_id": message_id,
                            "thread_id": raw.get("thread_id"),
                            "subject": subject,
                            "snippet": raw.get("snippet", ""),
                            "predicted_label": classified["predicted_label"],
                            "prediction": classified["predicted_label"],
                            "predicted_score": classified["predicted_score"],
                            "confidence": classified["predicted_score"],
                            "gmail_classification": gmail_cls,
                            "classified_at": classified["classified_at"],
                            "created_at": now.isoformat(),
                            "sent_at": raw.get("sent_at") or raw.get("received_at"),
                        }
                    )

            except Exception as err:
                skipped_count += 1
                logger.error(
                    f"[ClassifyBatch] user_id={user_id} error classifying email: {err}"
                )

            if job_id:
                job_service.update_progress(
                    job_id=job_id,
                    processed_increment=1,
                    classified_increment=1 if is_success else 0,
                    skipped_increment=1 if not is_success else 0,
                    current_subject=subject,
                )

        result = {
            "classified": classified_count,
            "skipped": skipped_count,
            "classified_emails": saved_records,
        }

        if job_id:
            job_service.complete_job(job_id, result)

        return result

    # ── helpers ───────────────────────────────────────────────────────────────

    def _disconnect_revoked_account(self, user_id: str, google_email: str) -> None:
        """Marks the Google account as disconnected when the token is revoked."""
        try:
            self.google_repo.disconnect_account(user_id)
            logger.warning(
                f"[Fetch] Google token revoked for user_id={user_id} "
                f"({google_email}). Account marked as disconnected."
            )
        except Exception as err:
            logger.error(
                f"[Fetch] Failed to disconnect revoked account "
                f"user_id={user_id}: {err}"
            )

    def _classify_one(self, raw_email: dict[str, Any]) -> dict[str, Any]:
        """
        Classifies a single raw email dict using the ML model service.
        Prioritizes full email body text over short snippet.
        """
        subject = raw_email.get("subject", "")
        body = raw_email.get("body") or raw_email.get("snippet", "")
        return self.model_service.classify_text(subject=subject, body=body)

    async def _fetch_from_gmail(
        self, user_id: str, google_email: str, access_token: str
    ) -> list:
        """
        Fetches unclassified messages from Gmail REST API v1 using access_token.
        Fetches up to FETCH_MAX_RESULTS messages per batch (capping maxResults per page to 500).
        Filters out messages that are already present in MongoDB.
        Uses concurrent batch fetching (asyncio.gather with Semaphore) for maximum performance.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        target_max_results = int(getattr(settings, "FETCH_MAX_RESULTS", 50))
        page_token = None
        candidate_msg_ids: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch up to target_max_results of the latest messages from Gmail (current dates first)
                while len(candidate_msg_ids) < target_max_results:
                    remaining = target_max_results - len(candidate_msg_ids)
                    page_size = min(remaining, 500)
                    url_list = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={page_size}"
                    if page_token:
                        url_list += f"&pageToken={page_token}"

                    resp = await client.get(url_list, headers=headers)
                    if resp.status_code != 200:
                        logger.warning(
                            f"[GmailAPI] List messages status {resp.status_code} for user_id={user_id}"
                        )
                        break

                    data = resp.json()
                    page_messages = data.get("messages", [])
                    if not page_messages:
                        break

                    for m in page_messages:
                        mid = m.get("id")
                        if mid and mid not in candidate_msg_ids:
                            candidate_msg_ids.append(mid)
                            if len(candidate_msg_ids) >= target_max_results:
                                break

                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break

                if not candidate_msg_ids:
                    return []

                # Filter out messages that already exist in MongoDB
                existing_ids = self.email_repo.get_existing_message_ids(
                    user_id, candidate_msg_ids
                )
                new_msg_ids = [m_id for m_id in candidate_msg_ids if m_id not in existing_ids]

                if not new_msg_ids:
                    return []

                # Concurrent batch fetching with Semaphore(10) to complete in ~1.2s instead of 20s
                semaphore = asyncio.Semaphore(10)

                async def _fetch_one_details(msg_id: str) -> dict[str, Any] | None:
                    async with semaphore:
                        try:
                            url_msg = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full"
                            msg_resp = await client.get(
                                url_msg, headers=headers, timeout=10.0
                            )
                            if msg_resp.status_code != 200:
                                return None

                            msg_data = msg_resp.json()
                            payload = msg_data.get("payload", {})
                            headers_list = payload.get("headers", [])

                            subject = "No Subject"
                            date_header = None
                            for h in headers_list:
                                h_name = h.get("name", "").lower()
                                if h_name == "subject":
                                    subject = h.get("value", "No Subject")
                                elif h_name == "date":
                                    date_header = h.get("value")

                            internal_date_ms = msg_data.get("internalDate")
                            sent_at = None
                            if internal_date_ms:
                                try:
                                    dt = datetime.fromtimestamp(
                                        int(internal_date_ms) / 1000.0, tz=timezone.utc
                                    )
                                    sent_at = dt.isoformat()
                                except Exception:
                                    pass

                            if not sent_at and date_header:
                                sent_at = date_header

                            snippet = msg_data.get("snippet", "")
                            full_body = _extract_full_body(payload) or snippet
                            thread_id = msg_data.get("threadId")
                            label_ids = msg_data.get("labelIds", [])
                            is_gmail_spam = "SPAM" in label_ids if isinstance(label_ids, list) else False
                            gmail_classification = {
                                "is_spam": is_gmail_spam,
                                "status": "spam" if is_gmail_spam else "not_spam",
                                "label_ids": label_ids,
                            }

                            return {
                                "message_id": msg_id,
                                "thread_id": thread_id,
                                "subject": subject,
                                "snippet": snippet,
                                "body": full_body,
                                "received_at": sent_at,
                                "sent_at": sent_at,
                                "label_ids": label_ids,
                                "gmail_classification": gmail_classification,
                            }

                        except Exception as fetch_err:
                            logger.warning(
                                f"[GmailAPI] Error fetching msg_id={msg_id}: {fetch_err}"
                            )
                            return None

                tasks = [_fetch_one_details(msg_id) for msg_id in new_msg_ids]
                fetched_results = await asyncio.gather(*tasks)
                new_raw_emails = [res for res in fetched_results if res is not None]

                # Ensure newest emails are always first
                new_raw_emails.sort(
                    key=lambda x: str(x.get("sent_at") or x.get("received_at") or ""),
                    reverse=True,
                )

                return new_raw_emails
        except Exception as err:
            logger.error(
                f"[GmailAPI] Error querying Gmail API for user_id={user_id}: {err}"
            )
            return []

    def _classify_one(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Classifies a single raw email dict using model_service or PredictionEngine singleton."""
        subject = raw.get("subject", "")
        body = raw.get("body") or raw.get("snippet", "")

        if hasattr(self, "model_service") and self.model_service is not None:
            if hasattr(self.model_service, "classify_text"):
                return self.model_service.classify_text(subject, body)
            if hasattr(self.model_service, "predict"):
                return self.model_service.predict(subject=subject, body=body)

        from app.services.prediction_engine import PredictionEngine

        engine = PredictionEngine()
        return engine.predict(subject=subject, body=body)
