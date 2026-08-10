import importlib.util
import os
import unittest
from unittest.mock import patch, MagicMock

from app.core.model_registry import normalize_model_key, list_supported_models
from app.services.classifier_factory import create_classifier
from app.services.classifiers.otis_classifier import OtisClassifier, normalize_spam_prediction


HAS_TORCH_TRANSFORMERS = (
    importlib.util.find_spec("torch") is not None
    and importlib.util.find_spec("transformers") is not None
)


class TestOtisClassifierAndModelSwitching(unittest.TestCase):
    """
    Test suite covering OTIS model integration, normalization, and environment-based model switching.
    """

    def test_test1_default_model_is_linear_svc(self):
        """Test 1: Default model when environment variable is empty/missing must be linear_svc."""
        key = normalize_model_key(None)
        self.assertEqual(key, "linear_svc")

        key_empty = normalize_model_key("")
        self.assertEqual(key_empty, "linear_svc")

    def test_test2_linear_svc_model_selection(self):
        """Test 2: EMAIL_CLASSIFIER_MODEL=linear_svc selects LinearSVC / MlopsClassifier."""
        classifier = create_classifier("linear_svc")
        self.assertIn(classifier.provider_name.lower(), ("linear_svc", "mlops"))
        self.assertTrue(classifier.is_loaded)

        res = classifier.predict(subject="Project Update", body="Here is the status report.")
        self.assertIn("predicted_label", res)
        self.assertIn("predicted_score", res)

    def test_test6_invalid_model_raises_configuration_error(self):
        """Test 6: Invalid EMAIL_CLASSIFIER_MODEL=abc raises clear configuration error."""
        with self.assertRaises(ValueError) as ctx:
            create_classifier("abc")
        
        err_msg = str(ctx.exception)
        self.assertIn("Unsupported EMAIL_CLASSIFIER_MODEL: abc", err_msg)
        self.assertIn("linear_svc", err_msg)
        self.assertIn("otis", err_msg)

    def test_normalize_spam_prediction_isolation(self):
        """Verify OTIS label normalization isolates labels into spam and not_spam / safe."""
        import torch

        # Index 0 = safe, Index 1 = spam
        logits = torch.tensor([[0.1, 2.5]])  # Higher score for index 1 (spam)
        id2label = {0: "LABEL_0", 1: "LABEL_1"}

        norm = normalize_spam_prediction(logits, id2label=id2label)
        self.assertTrue(norm["is_spam"])
        self.assertEqual(norm["label"], "spam")
        self.assertEqual(norm["predicted_label"], "spam")
        self.assertGreater(norm["confidence"], 0.8)

        # Index 0 = safe, Index 1 = spam
        logits_safe = torch.tensor([[3.0, 0.2]])  # Higher score for index 0 (safe)
        norm_safe = normalize_spam_prediction(logits_safe, id2label=id2label)
        self.assertFalse(norm_safe["is_spam"])
        self.assertEqual(norm_safe["label"], "not_spam")
        self.assertEqual(norm_safe["predicted_label"], "safe")

    @unittest.skipUnless(HAS_TORCH_TRANSFORMERS, "Requires PyTorch and transformers")
    @patch("transformers.AutoTokenizer.from_pretrained")
    @patch("transformers.AutoModelForSequenceClassification.from_pretrained")
    def test_test3_test4_test5_otis_prediction_flow_mocked(self, mock_model_cls, mock_tok_cls):
        """
        Fast unit test for:
        Test 3 (OTIS model prediction flow),
        Test 4 (Empty subject), and
        Test 5 (Empty body).
        """
        import torch

        # Setup mock tokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[101, 102]])}
        mock_tok_cls.return_value = mock_tokenizer

        # Setup mock model output
        mock_model = MagicMock()
        mock_output = MagicMock()
        mock_output.logits = torch.tensor([[0.1, 3.5]])  # High spam probability
        mock_model.return_value = mock_output
        mock_model.config.id2label = {0: "safe", 1: "spam"}
        mock_model_cls.return_value = mock_model

        classifier = OtisClassifier()
        self.assertEqual(classifier.provider_name, "otis")
        self.assertTrue(classifier.is_loaded)

        # Test 3: Normal prediction flow
        res = classifier.predict(
            subject="Exclusive Offer! Win Free Gift Cards",
            body="Click the link below immediately to claim your free reward."
        )
        self.assertIn("predicted_label", res)
        self.assertEqual(res["predicted_label"], "spam")
        self.assertEqual(res["is_spam"], True)
        self.assertEqual(res["label"], "spam")
        self.assertEqual(res["model"], "otis")

        # Test 4: Empty subject
        res_no_subj = classifier.predict(
            subject="",
            body="Congratulations! You have been selected for a cash prize."
        )
        self.assertEqual(res_no_subj["model"], "otis")

        # Test 5: Empty body
        res_no_body = classifier.predict(
            subject="Urgent action required: update your password now",
            body=""
        )
        self.assertEqual(res_no_body["model"], "otis")


if __name__ == "__main__":
    unittest.main()
