import asyncio
import unittest
from unittest.mock import patch, MagicMock
from app.services.ml_client import MLServiceClient


class TestMLServiceClientIntegration(unittest.TestCase):
    def setUp(self):
        self.client = MLServiceClient(base_url="http://localhost:9000", timeout=5)

    @patch("httpx.Client.post")
    def test_predict_sync_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "subject": "Test Subject",
            "predicted_label": "spam",
            "predicted_score": 0.88,
            "classified_at": "2026-08-07T00:00:00Z"
        }
        mock_post.return_value = mock_response

        res = self.client.predict_sync(subject="Test Subject", body="Test Body")
        self.assertEqual(res["predicted_label"], "spam")
        self.assertEqual(res["predicted_score"], 0.88)

    @patch("httpx.AsyncClient.get")
    def test_health_check_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "service": "MailSentry ML Service",
            "version": "1.0.0"
        }
        mock_get.return_value = mock_response

        health = asyncio.run(self.client.check_health())
        self.assertEqual(health["status"], "healthy")

    @patch("httpx.Client.post")
    def test_predict_sync_retry_on_failure(self, mock_post):
        mock_post.side_effect = Exception("Connection error")
        try:
            self.client.predict_sync(subject="Urgent", body="Call now")
        except Exception:
            pass
        self.assertEqual(mock_post.call_count, 3)


if __name__ == "__main__":
    unittest.main()
