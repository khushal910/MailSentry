import unittest
from unittest.mock import MagicMock
from app.services.ml_preprocessing import MLPreprocessing
from app.services.ml_model_service import MLModelService


class TestBackendStandaloneML(unittest.TestCase):
    """
    Tests backend standalone ML preprocessing & classification pipeline.
    Ensures backend does not depend on ml-service package/imports at runtime.
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

    def test_classify_text_with_mock_pipeline_model(self):
        service = MLModelService()
        mock_model = MagicMock()
        mock_model.predict.return_value = ["spam"]
        mock_model.predict_proba.return_value = [[0.02, 0.98]]

        service.load_latest_model = MagicMock(return_value=mock_model)

        res = service.classify_text(
            subject="Claim free prize",
            body="Congratulations you won a gift card at http://prize.com/win?id=99"
        )

        self.assertEqual(res["predicted_label"], "spam")
        self.assertEqual(res["predicted_score"], 0.98)
        self.assertIn("classified_at", res)

    def test_classify_text_with_mock_preprocessor_and_model(self):
        service = MLModelService()

        mock_preprocessor = MagicMock()
        mock_preprocessor.transform.return_value = [[0.1, 0.5, 0.9]]

        mock_label_encoder = MagicMock()
        mock_label_encoder.inverse_transform.return_value = ["spam"]

        mock_model = MagicMock()
        mock_model.predict.return_value = [1]
        mock_model.predict_proba.return_value = [[0.05, 0.95]]

        service.load_latest_model = MagicMock(return_value=mock_model)
        service.load_preprocessor = MagicMock(return_value=mock_preprocessor)
        service.load_label_encoder = MagicMock(return_value=mock_label_encoder)

        res = service.classify_text(
            subject="Account update",
            body="Please update credentials at http://phish.net/login"
        )

        mock_preprocessor.transform.assert_called_once()
        mock_model.predict.assert_called_once_with([[0.1, 0.5, 0.9]])
        self.assertEqual(res["predicted_label"], "spam")
        self.assertEqual(res["predicted_score"], 0.95)


if __name__ == "__main__":
    unittest.main()
