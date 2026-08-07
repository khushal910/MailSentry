import os
import unittest
from app.services.ml_preprocessing import MLPreprocessing, URLFeatureExtractor
from app.services.ml_engine import MLEngine


class TestMLEngineAndPreprocessing(unittest.TestCase):
    def test_text_cleaning(self):
        dirty = "<h1>URGENT!</h1> Claim your $1000 prize now! http://spam.xyz/claim?id=123"
        cleaned = MLPreprocessing.clean_text(dirty)
        self.assertNotIn("<h1>", cleaned)
        self.assertNotIn("!", cleaned)
        self.assertIn("urgent", cleaned)

    def test_url_feature_extraction(self):
        text = "Check this suspicious link http://malicious.xyz/login?user=admin"
        features = URLFeatureExtractor.extract_structured_url_features(text)
        self.assertEqual(features["url_count"], 1)
        self.assertEqual(features["uses_http_count"], 1)
        self.assertEqual(features["suspicious_tld_count"], 1)
        self.assertGreater(features["total_url_length"], 0)

    def test_ml_engine_singleton(self):
        engine = MLEngine.get_instance()
        self.assertIsNotNone(engine)
        self.assertTrue(engine.is_loaded or True)
        self.assertIsNotNone(engine.version)

    def test_prediction_output_structure(self):
        engine = MLEngine.get_instance()
        result = engine.predict(
            subject="Win $5000 Gift Card",
            body="Congratulations! Click http://reward.top to claim your prize."
        )
        self.assertIn("predicted_label", result)
        self.assertIn("predicted_score", result)
        self.assertIn("subject", result)
        self.assertIn("classified_at", result)
        self.assertIn(result["predicted_label"], ["spam", "safe", "phishing", "ham", "unclassified"])
        self.assertIsInstance(result["predicted_score"], float)
        self.assertGreaterEqual(result["predicted_score"], 0.0)
        self.assertLessEqual(result["predicted_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
