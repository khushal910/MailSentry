import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.core.config import settings

# Module under test
from app.services.gmail_fetch_service import (
    _LAST_FETCH_AT,
    _LOCK_ACQUIRED_AT,
    _USER_LOCKS,
    FetchResult,
    GmailFetchService,
)

USER_ID = "user_abc123"
GOOGLE_ACCOUNT = {
    "google_email": "test@gmail.com",
    "google_connected": True,
    "refresh_token": "tok_xxx",
}


def run(coro):
    """Helper to run async coroutines in unittest."""
    return asyncio.run(coro)


def _make_service(
    token_ok=True,
    token_401=False,
    emails=None,
    classify_raises=False,
):
    """
    Builds a GmailFetchService with all dependencies mocked.

    - token_ok=True  → token manager returns a token string
    - token_401=True → token manager raises HTTP 401 (revoked)
    - emails         → list of raw email dicts returned by _fetch_from_gmail
    - classify_raises → model_service.classify_text raises an Exception
    """
    email_repo = MagicMock()
    email_repo.save_email.return_value = {"_id": "doc1"}

    google_repo = MagicMock()
    google_repo.disconnect_account.return_value = True

    token_manager = MagicMock()
    if token_401:
        token_manager.get_valid_access_token = AsyncMock(
            side_effect=HTTPException(status_code=401, detail="Token revoked")
        )
    elif token_ok:
        token_manager.get_valid_access_token = AsyncMock(return_value="access_tok_abc")
    else:
        token_manager.get_valid_access_token = AsyncMock(
            side_effect=HTTPException(status_code=500, detail="Server error")
        )

    model_service = MagicMock()
    if classify_raises:
        model_service.classify_text.side_effect = Exception("model crashed")
    else:
        model_service.classify_text.return_value = {
            "predicted_label": "spam",
            "predicted_score": 0.97,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }

    svc = GmailFetchService(
        email_repo=email_repo,
        google_repo=google_repo,
        token_manager=token_manager,
        model_service=model_service,
    )

    # Inject stub emails into _fetch_from_gmail
    raw = emails if emails is not None else []
    svc._fetch_from_gmail = AsyncMock(return_value=raw)

    return svc


class TestGmailFetchServiceRateLimit(unittest.TestCase):
    """Rate limiting enforced correctly."""

    def setUp(self):
        _LAST_FETCH_AT.clear()
        _USER_LOCKS.clear()
        _LOCK_ACQUIRED_AT.clear()
        self.patcher = patch.object(settings, "FETCH_RATE_LIMIT_SECONDS_APPLY", True)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_first_call_is_allowed(self):
        svc = _make_service()
        result = run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertIsInstance(result, FetchResult)

    def test_second_call_within_window_raises_429(self):
        # Simulate a fetch that just happened
        _LAST_FETCH_AT[USER_ID] = datetime.now(timezone.utc)
        svc = _make_service()
        with self.assertRaises(HTTPException) as ctx:
            run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("wait", ctx.exception.detail.lower())

    def test_call_after_window_is_allowed(self):
        # Simulate a fetch 6 minutes ago (outside 5 min window)
        _LAST_FETCH_AT[USER_ID] = datetime.now(timezone.utc) - timedelta(minutes=6)
        svc = _make_service()
        result = run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertIsInstance(result, FetchResult)


class TestGmailFetchServiceConcurrency(unittest.TestCase):
    """Concurrency lock prevents duplicate parallel fetches."""

    def setUp(self):
        _LAST_FETCH_AT.clear()
        _USER_LOCKS.clear()
        _LOCK_ACQUIRED_AT.clear()

    def test_concurrent_call_raises_429(self):
        """If a lock is already held and not expired, second call gets 429."""
        import asyncio as _asyncio

        lock = _asyncio.Lock()
        _USER_LOCKS[USER_ID] = lock

        async def _run():
            # Acquire the lock to simulate an in-flight fetch
            async with lock:
                _LOCK_ACQUIRED_AT[USER_ID] = datetime.now(timezone.utc)
                svc = _make_service()
                # This second call should see the lock held and raise 429
                with self.assertRaises(HTTPException) as ctx:
                    await svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT)
                self.assertEqual(ctx.exception.status_code, 429)

        _asyncio.run(_run())


class TestGmailFetchServiceTokenExpiry(unittest.TestCase):
    """401 from token manager disconnects the account and raises 403."""

    def setUp(self):
        _LAST_FETCH_AT.clear()
        _USER_LOCKS.clear()
        _LOCK_ACQUIRED_AT.clear()

    def test_token_401_raises_403_and_disconnects(self):
        svc = _make_service(token_401=True)
        with self.assertRaises(HTTPException) as ctx:
            run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("reconnect", ctx.exception.detail.lower())
        # Verify disconnect was called
        svc.google_repo.disconnect_account.assert_called_once_with(USER_ID)

    def test_non_401_http_error_is_re_raised(self):
        """HTTP errors that aren't 401/404 should propagate unchanged."""
        svc = _make_service(token_ok=False)
        with self.assertRaises(HTTPException) as ctx:
            run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(ctx.exception.status_code, 500)
        svc.google_repo.disconnect_account.assert_not_called()


class TestGmailFetchServiceZeroEmails(unittest.TestCase):
    """Zero emails fetched returns {fetched:0, classified:0, skipped:0}."""

    def setUp(self):
        _LAST_FETCH_AT.clear()
        _USER_LOCKS.clear()
        _LOCK_ACQUIRED_AT.clear()

    def test_zero_emails_returns_empty_result(self):
        svc = _make_service(emails=[])
        result = run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(result.fetched, 0)
        self.assertEqual(result.classified, 0)
        self.assertEqual(result.skipped, 0)
        svc.email_repo.save_email.assert_not_called()

    def test_zero_emails_to_dict(self):
        svc = _make_service(emails=[])
        result = run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(
            result.to_dict(),
            {"fetched": 0, "classified": 0, "skipped": 0, "new_emails": []},
        )


class TestGmailFetchServicePartialFailure(unittest.TestCase):
    """One failing email doesn't abort the batch — counted as skipped."""

    def setUp(self):
        _LAST_FETCH_AT.clear()
        _USER_LOCKS.clear()
        _LOCK_ACQUIRED_AT.clear()

    def test_all_succeed(self):
        emails = [
            {"message_id": "m1", "subject": "Hello", "snippet": "body1"},
            {"message_id": "m2", "subject": "World", "snippet": "body2"},
        ]
        svc = _make_service(emails=emails)
        result = run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(result.fetched, 2)
        self.assertEqual(result.classified, 2)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(svc.email_repo.save_email.call_count, 2)

    def test_one_classify_fails_is_skipped(self):
        emails = [
            {"message_id": "m1", "subject": "Good email", "snippet": "ok"},
            {"message_id": "m2", "subject": "Bad email", "snippet": "crash"},
        ]
        svc = _make_service(emails=emails)
        # Make classify_text raise only for m2
        call_count = {"n": 0}

        def classify_side_effect(subject, body):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise Exception("model crashed on this email")
            return {
                "predicted_label": "spam",
                "predicted_score": 0.9,
                "classified_at": datetime.now(timezone.utc).isoformat(),
            }

        svc.model_service.classify_text.side_effect = classify_side_effect

        result = run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(result.fetched, 2)
        self.assertEqual(result.classified, 1)
        self.assertEqual(result.skipped, 1)
        # Only the first email was saved
        self.assertEqual(svc.email_repo.save_email.call_count, 1)

    def test_all_classify_fail_skipped_count_equals_fetched(self):
        emails = [
            {"message_id": "m1", "subject": "A", "snippet": "a"},
            {"message_id": "m2", "subject": "B", "snippet": "b"},
        ]
        svc = _make_service(emails=emails, classify_raises=True)
        result = run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(result.fetched, 2)
        self.assertEqual(result.classified, 0)
        self.assertEqual(result.skipped, 2)
        svc.email_repo.save_email.assert_not_called()


class TestGmailFetchServicePrivacy(unittest.TestCase):
    """Emails are always saved with the authenticated user's user_id."""

    def setUp(self):
        _LAST_FETCH_AT.clear()
        _USER_LOCKS.clear()
        _LOCK_ACQUIRED_AT.clear()

    def test_save_called_with_correct_user_id(self):
        emails = [{"message_id": "msg_x", "subject": "Test", "snippet": "snip"}]
        svc = _make_service(emails=emails)
        run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        call_args = svc.email_repo.save_email.call_args
        saved_doc = call_args[0][0]  # positional first arg
        self.assertEqual(saved_doc["user_id"], USER_ID)
        self.assertEqual(saved_doc["message_id"], "msg_x")


class TestFetchResultToDict(unittest.TestCase):
    """FetchResult serialises correctly."""

    def test_to_dict(self):
        r = FetchResult(fetched=5, classified=4, skipped=1)
        self.assertEqual(
            r.to_dict(), {"fetched": 5, "classified": 4, "skipped": 1, "new_emails": []}
        )

    def test_defaults(self):
        r = FetchResult()
        self.assertEqual(
            r.to_dict(), {"fetched": 0, "classified": 0, "skipped": 0, "new_emails": []}
        )


class TestJobServiceSetTotal(unittest.TestCase):
    """JobService set_total updates total dynamically and complete_job sets processed=total."""

    def test_set_total_and_complete_job(self):
        from app.services.job_service import JobService

        js = JobService()
        job = js.create_job(user_id="user_test", total=50)
        self.assertEqual(job.total, 50)

        js.set_total(job.job_id, 5)
        self.assertEqual(job.total, 5)

        js.update_progress(job.job_id, processed_increment=2)
        self.assertEqual(job.processed, 2)

        js.complete_job(job.job_id, {"status": "ok"})
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.processed, 5)


class TestFetchFromGmailPagination(unittest.TestCase):
    """Verifies that _fetch_from_gmail caps page size to 500 and paginates using pageToken when FETCH_MAX_RESULTS > 500."""

    def setUp(self):
        self.patcher = patch.object(settings, "FETCH_MAX_RESULTS", 1000)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_fetch_paginates_and_caps_500(self):
        svc = GmailFetchService()
        svc.email_repo = MagicMock()
        svc.email_repo.get_existing_message_ids.return_value = set()

        # Mock httpx AsyncClient response to simulate 2 pages of 500 messages
        mock_resp_1 = MagicMock()
        mock_resp_1.status_code = 200
        mock_resp_1.json.return_value = {
            "messages": [{"id": f"m_{i}"} for i in range(500)],
            "nextPageToken": "token_page_2",
        }

        mock_resp_2 = MagicMock()
        mock_resp_2.status_code = 200
        mock_resp_2.json.return_value = {
            "messages": [{"id": f"m_{i}"} for i in range(500, 1000)],
        }

        mock_msg_resp = MagicMock()
        mock_msg_resp.status_code = 200
        mock_msg_resp.json.return_value = {
            "id": "m_0",
            "snippet": "hello",
            "payload": {"headers": [{"name": "Subject", "value": "Test"}]},
        }

        async def mock_get(url, **kwargs):
            if "pageToken=token_page_2" in url:
                return mock_resp_2
            elif "messages?" in url:
                return mock_resp_1
            return mock_msg_resp

        with patch("httpx.AsyncClient.get", side_effect=mock_get):
            raw = run(
                svc._fetch_from_gmail(
                    user_id="user_123",
                    google_email="test@gmail.com",
                    access_token="tok",
                )
            )

        self.assertEqual(len(raw), 1000)


class TestGmailFetchServiceTokenError400(unittest.TestCase):
    """HTTP 400 from token manager also disconnects account."""

    def test_token_400_disconnects_account(self):
        svc = _make_service(token_ok=False)
        svc.token_manager.get_valid_access_token = AsyncMock(
            side_effect=HTTPException(status_code=400, detail="invalid_grant")
        )
        with self.assertRaises(HTTPException) as ctx:
            run(svc.run_fetch_pipeline(USER_ID, GOOGLE_ACCOUNT))
        self.assertEqual(ctx.exception.status_code, 403)
        svc.google_repo.disconnect_account.assert_called_once_with(USER_ID)


if __name__ == "__main__":
    unittest.main()
