import os
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from app.core.config import Settings
from app.services.gmail_fetch_service import GmailFetchService, FetchResult


class TestModelSwitchingAndGmailLabelPreservation(unittest.TestCase):
    """
    Test suite for model switching configuration and Gmail label preservation.
    """

    def test_default_classifier_model_setting(self):
        """Test 1: Check default model is mlops when env var is omitted."""
        with patch.dict(os.environ, {}, clear=True):
            s = Settings()
            model_setting = getattr(s, "FALLBACK_CLASSIFICATION_MODEL", "mlops")
            self.assertEqual(model_setting, "mlops")

    def test_configured_classifier_model_setting(self):
        """Test 2 & 3: Environment variable switching for FALLBACK_CLASSIFICATION_MODEL between linear_svc and otis."""
        with patch.dict(os.environ, {"FALLBACK_CLASSIFICATION_MODEL": "linear_svc"}):
            s = Settings()
            self.assertEqual(s.FALLBACK_CLASSIFICATION_MODEL, "linear_svc")

        with patch.dict(os.environ, {"FALLBACK_CLASSIFICATION_MODEL": "otis"}):
            s = Settings()
            self.assertEqual(s.FALLBACK_CLASSIFICATION_MODEL, "otis")

    @patch("app.services.gmail_fetch_service.GmailTokenManager")
    def test_test7_gmail_label_preservation(self, mock_token_mgr_cls):
        """
        Test 7: Verify that Gmail label (gmail_classification / gmail_label) and AI prediction
        (predicted_label / ai_prediction) remain completely separate.
        """
        email_repo = MagicMock()
        email_repo.get_existing_message_ids.return_value = []

        google_repo = MagicMock()
        token_mgr = MagicMock()
        token_mgr.get_valid_access_token = AsyncMock(return_value="valid_token")

        model_service = MagicMock()
        # ML model predicts 'safe' (not spam)
        model_service.classify_text.return_value = {
            "predicted_label": "safe",
            "predicted_score": 0.95,
            "is_spam": False,
            "label": "not_spam",
            "confidence": 0.95,
            "model": "otis",
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }

        svc = GmailFetchService(
            email_repo=email_repo,
            google_repo=google_repo,
            token_manager=token_mgr,
            model_service=model_service,
        )

        # Raw email has Gmail label SPAM (Gmail classified it as spam)
        raw_email = {
            "message_id": "msg_123",
            "thread_id": "thread_123",
            "subject": "Offers",
            "body": "Special discount",
            "label_ids": ["SPAM", "UNREAD"],
            "gmail_classification": {"is_spam": True, "status": "spam"},
        }
        svc._fetch_from_gmail = AsyncMock(return_value=[raw_email])

        res = svc.classify_and_save_batch(user_id="user_1", emails_to_classify=[raw_email])

        self.assertEqual(res["classified"], 1)
        self.assertEqual(len(res["classified_emails"]), 1)

        saved_doc = res["classified_emails"][0]
        # AI prediction says safe / not_spam
        self.assertEqual(saved_doc["predicted_label"], "safe")
        self.assertEqual(saved_doc["predicted_score"], 0.95)

        # Gmail label says SPAM (preserved separately)
        self.assertIsNotNone(saved_doc["gmail_classification"])
        self.assertTrue(saved_doc["gmail_classification"]["is_spam"])
        self.assertEqual(saved_doc["gmail_classification"]["status"], "spam")

    @patch("app.services.ml_client.MLServiceClient.check_health", new_callable=AsyncMock)
    def test_production_model_endpoint_when_ml_service_offline(self, mock_check_health):
        """Verify get_production_model returns 200 OK with fallback metadata when ml-service is offline."""
        import asyncio
        mock_check_health.side_effect = Exception("Connection refused / microservice terminated")
        from app.api.model_routes import get_production_model

        res = asyncio.run(get_production_model())
        self.assertEqual(res.get("status_code"), 200)
        data = res.get("data", {})
        self.assertEqual(data.get("serving_status"), "Fallback Engine")
        self.assertEqual(data.get("provider"), "mlops")


if __name__ == "__main__":
    unittest.main()
