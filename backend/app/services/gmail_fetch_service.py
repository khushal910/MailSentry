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
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.email_repository import EmailRepository
from app.repositories.google_account_repository import GoogleAccountRepository
from app.services.gmail_token_manager import GmailTokenManager
from app.services.ml_model_service import MLModelService

logger = logging.getLogger("mailsentry.gmail_fetch")

# ──────────────────────────────────────────────────────────────────────────────
# Process-level state (single-worker safe)
# ──────────────────────────────────────────────────────────────────────────────

# Per-user asyncio locks: {user_id: asyncio.Lock}
_USER_LOCKS: Dict[str, asyncio.Lock] = {}

# Per-user lock acquisition timestamps for TTL expiry: {user_id: datetime}
_LOCK_ACQUIRED_AT: Dict[str, datetime] = {}

# Per-user last successful fetch timestamp for rate limiting: {user_id: datetime}
_LAST_FETCH_AT: Dict[str, datetime] = {}


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
    def __init__(self, fetched: int = 0, classified: int = 0, skipped: int = 0):
        self.fetched = fetched
        self.classified = classified
        self.skipped = skipped

    def to_dict(self) -> Dict[str, int]:
        return {
            "fetched": self.fetched,
            "classified": self.classified,
            "skipped": self.skipped,
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
        email_repo: Optional[EmailRepository] = None,
        google_repo: Optional[GoogleAccountRepository] = None,
        token_manager: Optional[GmailTokenManager] = None,
        model_service: Optional[MLModelService] = None,
    ):
        self.email_repo = email_repo or EmailRepository()
        self.google_repo = google_repo or GoogleAccountRepository()
        self.token_manager = token_manager or GmailTokenManager(repo=self.google_repo)
        self.model_service = model_service or MLModelService()

    # ── public entry point ────────────────────────────────────────────────────

    async def run_fetch_pipeline(
        self, user_id: str, google_account: Dict[str, Any]
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
        self, user_id: str, google_account: Dict[str, Any]
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
        self, user_id: str, google_account: Dict[str, Any]
    ) -> FetchResult:
        google_email = google_account.get("google_email", "")

        # Step 1: Validate / refresh access token
        try:
            access_token = await self.token_manager.get_valid_access_token(google_email)
        except HTTPException as exc:
            if exc.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_404_NOT_FOUND,
            ):
                # Token revoked or missing — mark account as disconnected
                self._disconnect_revoked_account(user_id, google_email)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Gmail access revoked. Please reconnect your account.",
                ) from exc
            raise

        # Step 2: Fetch emails from Gmail (stub — replace with real API call)
        raw_emails = self._fetch_from_gmail(
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
                email_doc = {
                    "user_id": user_id,
                    "message_id": raw["message_id"],
                    "thread_id": raw.get("thread_id"),
                    "subject": raw.get("subject", ""),
                    "snippet": raw.get("snippet", ""),
                    "predicted_label": classified["predicted_label"],
                    "predicted_score": classified["predicted_score"],
                    "fetch_time": datetime.now(timezone.utc),
                    "classified_at": datetime.fromisoformat(
                        classified["classified_at"]
                    ),
                }
                self.email_repo.save_email(email_doc, check_access=False)
                result.classified += 1
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

    def _classify_one(self, raw_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies a single raw email dict using the ML model service.
        Raises on any model error so the caller can count it as skipped.
        """
        subject = raw_email.get("subject", "")
        snippet = raw_email.get("snippet", "") or raw_email.get("body", "")
        return self.model_service.classify_text(subject=subject, body=snippet)

    @staticmethod
    def _fetch_from_gmail(
        user_id: str, google_email: str, access_token: str
    ) -> list:
        """
        Stub: Returns mock email data.
        ─────────────────────────────────────────────────────────────────────
        REPLACE THIS METHOD with the real Gmail API call, e.g.:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials

            creds = Credentials(token=access_token)
            service = build("gmail", "v1", credentials=creds)
            results = service.users().messages().list(
                userId="me", labelIds=["INBOX"], maxResults=50
            ).execute()
            messages = results.get("messages", [])
            ...
        ─────────────────────────────────────────────────────────────────────
        """
        logger.debug(
            f"[Fetch] _fetch_from_gmail stub called for "
            f"user_id={user_id} email={google_email}"
        )
        # Return an empty list until real API is integrated
        return []
