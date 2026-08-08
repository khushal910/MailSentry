import importlib.util
import unittest
from app.services.classifier_factory import create_classifier
from app.services.ml_engine import MLEngine
from app.core.config import settings

HAS_TORCH_PEFT = (
    importlib.util.find_spec("torch") is not None
    and importlib.util.find_spec("peft") is not None
    and importlib.util.find_spec("transformers") is not None
)


class TestClassifierProviders(unittest.TestCase):
    def test_invalid_classification_model_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            create_classifier("invalid_provider_name")
        self.assertIn("Unsupported", str(ctx.exception))


    def test_mlops_classifier_provider(self):
        classifier = create_classifier("mlops")
        self.assertEqual(classifier.provider_name, "mlops")
        self.assertTrue(classifier.is_loaded)

        result = classifier.predict(
            subject="Congratulations! You won $1,000,000!",
            body="Click here to claim your prize."
        )
        self.assertIn("predicted_label", result)
        self.assertIn("predicted_score", result)
        self.assertIn("probabilities", result)
        self.assertEqual(result["model"], "mlops")

    @unittest.skipUnless(HAS_TORCH_PEFT, "Requires PyTorch, transformers, and peft")
    def test_roberta_classifier_provider(self):
        active_model = (settings.EMAIL_CLASSIFIER_MODEL or "").lower()
        run_all = os.getenv("RUN_TRANSFORMER_TESTS", "false").lower() in ("true", "1")
        if active_model != "roberta" and not run_all:
            self.skipTest(f"Skipping RoBERTa test as active model is '{active_model}' (Set EMAIL_CLASSIFIER_MODEL=roberta to run)")

        try:
            classifier = create_classifier("roberta")
        except Exception as e:
            self.skipTest(f"Skipping RoBERTa download test if network or model download unavailable: {e}")



        self.assertEqual(classifier.provider_name, "roberta")
        self.assertTrue(classifier.is_loaded)
        self.assertIn(classifier.device_name, ["cpu", "cuda"])

        # Test spam sample
        spam_result = classifier.predict(
            subject="Congratulations! You won $1,000,000!",
            body="Click here to claim your prize."
        )
        self.assertIn("predicted_label", spam_result)
        self.assertIn("predicted_score", spam_result)
        self.assertIn("probabilities", spam_result)
        self.assertEqual(spam_result["model"], "roberta")

        # Test safe/ham sample
        safe_result = classifier.predict(
            subject="Meeting tomorrow at 10 AM",
            body="Please join the project meeting tomorrow at 10 AM."
        )
        self.assertIn("predicted_label", safe_result)
        self.assertIn("predicted_score", safe_result)
        self.assertEqual(safe_result["model"], "roberta")

    def test_ml_engine_switching(self):
        engine_mlops = MLEngine.get_instance(model_type="mlops", force_reload=True)
        res_mlops = engine_mlops.predict(subject="Test Email", body="Hello team")
        self.assertEqual(res_mlops["model"], "mlops")


if __name__ == "__main__":
    unittest.main()
