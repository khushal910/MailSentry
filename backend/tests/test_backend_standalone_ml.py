import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ml_model_service import MLModelService
from app.services.ml_preprocessing import MLPreprocessing


class TestBackendStandaloneML(unittest.TestCase):
    """
    Tests backend standalone ML preprocessing & classification pipeline.
    Ensures backend delegates prediction to MLServiceClient over HTTP microservice API.
    """

    def test_clean_text(self):
        raw_html = "<h1>URGENT: Win $1000!</h1> <p>Click <a href='http://spam.com'>here</a> now.</p>"
        cleaned = MLPreprocessing.clean_text(raw_html)
        self.assertNotIn("<h1>", cleaned)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("</h1>", cleaned)
        self.assertIn("urgent win 1000 click here now", cleaned)

    def test_extract_url_features(self):
        text = "Check out https://secure-verify.bank.com/login?user=123 for details"
        featured = MLPreprocessing.extract_url_features(text)
        self.assertIn("https", featured)
        self.assertIn("bank", featured)
        self.assertIn("has_query", featured)

    def test_preprocess_email_text(self):
        subject = "<b>Special Offer</b>"
        body = "Visit http://discount.shop/claim today!"
        result = MLPreprocessing.preprocess_email_text(subject, body)
        self.assertNotIn("<b>", result)
        self.assertIn("special offer", result)
        self.assertIn("discount", result)

    @patch("app.services.ml_client.MLServiceClient.predict_sync")
    def test_classify_text_delegates_to_ml_client(self, mock_predict):
        mock_predict.return_value = {
            "subject": "Claim free prize",
            "predicted_label": "spam",
            "predicted_score": 0.98,
            "classified_at": "2026-08-07T00:00:00Z",
        }
        service = MLModelService()
        res = service.classify_text(
            subject="Claim free prize",
            body="Congratulations you won a gift card at http://prize.com/win?id=99",
        )

        mock_predict.assert_called_once_with(
            subject="Claim free prize",
            body="Congratulations you won a gift card at http://prize.com/win?id=99",
        )
        self.assertEqual(res["predicted_label"], "spam")
        self.assertEqual(res["predicted_score"], 0.98)


if __name__ == "__main__":
    unittest.main()
