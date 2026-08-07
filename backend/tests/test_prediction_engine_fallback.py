import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.prediction_engine import PredictionEngine


class TestPredictionEngineFallback(unittest.TestCase):
    """
    Unit and integration tests for PredictionEngine fallback behavior when
    the primary ML Microservice HTTP endpoint is unreachable or timing out.
    """

    def setUp(self):
        self.engine = PredictionEngine()

    @patch("app.services.ml_client.MLServiceClient.predict_sync")
    def test_primary_http_success(self, mock_predict_sync):
        """Tests that PredictionEngine uses HTTP client when microservice is online."""
        mock_predict_sync.return_value = {
            "subject": "Weekly Update",
            "predicted_label": "safe",
            "predicted_score": 0.9250,
            "classified_at": "2026-08-07T00:00:00Z",
            "version": "v1.0.0",
        }

        res = self.engine.predict(subject="Weekly Update", body="Here is the project status.")
        self.assertEqual(res["predicted_label"], "safe")
        self.assertEqual(res["predicted_score"], 0.9250)

    @patch("app.services.ml_client.MLServiceClient.predict_sync")
    def test_unreachable_http_falls_back_and_never_returns_flat_50(self, mock_predict_sync):
        """
        Tests that when MLServiceClient raises an exception (unreachable),
        PredictionEngine falls back seamlessly and NEVER returns a static 0.50 score.
        """
        mock_predict_sync.side_effect = Exception("Connection refused to port 9000")

        # Test normal safe email
        safe_res = self.engine.predict(
            subject="Team sync meeting",
            body="Hi everyone, let us meet tomorrow at 10 AM to discuss Q3 targets.",
        )
        self.assertIn("predicted_label", safe_res)
        self.assertIn("predicted_score", safe_res)
        self.assertNotEqual(safe_res["predicted_score"], 0.50)
        self.assertGreater(safe_res["predicted_score"], 0.60)

        # Test spam email
        spam_res = self.engine.predict(
            subject="URGENT LOTTERY WINNER",
            body="CLAIM YOUR FREE PRIZE BITCOIN CASH NOW CLICK LINK",
        )
        self.assertEqual(spam_res["predicted_label"], "spam")
        self.assertNotEqual(spam_res["predicted_score"], 0.50)
        self.assertGreater(spam_res["predicted_score"], 0.85)

    def test_dynamic_heuristic_score_calculation(self):
        """Tests that Backup 2 (Dynamic Heuristic) calculates variable confidence scores."""
        res_short = self.engine.predict(subject="Hi", body="Quick question")
        res_long = self.engine.predict(
            subject="Detailed Quarterly Financial Report and Analysis",
            body="Dear team, Attached is the complete breakdown of our quarterly revenues, expenditure, and growth metrics. Regards.",
        )

        # Long email with greeting should have higher confidence score than short email
        self.assertNotEqual(res_short["predicted_score"], 0.50)
        self.assertNotEqual(res_long["predicted_score"], 0.50)
        self.assertGreaterEqual(res_long["predicted_score"], res_short["predicted_score"])


if __name__ == "__main__":
    unittest.main()
