import importlib.util
import unittest
from app.core.model_registry import (
    MODEL_REGISTRY,
    get_model_config,
    list_supported_models,
    normalize_model_key,
)
from app.services.classifier_factory import create_classifier

HAS_DEBERTA_DEPS = (
    importlib.util.find_spec("torch") is not None
    and importlib.util.find_spec("transformers") is not None
    and importlib.util.find_spec("sentencepiece") is not None
)


class TestDebertaClassifierIntegration(unittest.TestCase):
    def test_model_registry_resolution(self):
        self.assertEqual(normalize_model_key("deberta"), "deberta-v3-base")
        self.assertEqual(normalize_model_key("deberta-v3-base"), "deberta-v3-base")
        self.assertEqual(normalize_model_key("microsoft/deberta-v3-base"), "deberta-v3-base")
        self.assertEqual(normalize_model_key("roberta"), "roberta")
        self.assertEqual(normalize_model_key("mlops"), "mlops")

        config = get_model_config("deberta-v3-base")
        self.assertIsNotNone(config)
        self.assertEqual(config["base_model"], "microsoft/deberta-v3-base")
        self.assertIn("query_proj", config["target_modules"])

        supported = list_supported_models()
        self.assertIn("deberta-v3-base", supported)
        self.assertIn("roberta", supported)
        self.assertIn("mlops", supported)

    def test_invalid_model_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            create_classifier("unknown_model_xyz")
        self.assertIn("Unsupported EMAIL_CLASSIFIER_MODEL", str(ctx.exception))
        self.assertIn("deberta-v3-base", str(ctx.exception))

    @unittest.skipUnless(HAS_DEBERTA_DEPS, "Requires PyTorch, Transformers, and SentencePiece")
    def test_deberta_classifier_prediction(self):
        active_model = (settings.EMAIL_CLASSIFIER_MODEL or "").lower()
        run_all = os.getenv("RUN_TRANSFORMER_TESTS", "false").lower() in ("true", "1")
        if active_model not in ("deberta", "deberta-v3-base") and not run_all:
            self.skipTest(f"Skipping DeBERTa prediction test as active model is '{active_model}' (Set EMAIL_CLASSIFIER_MODEL=deberta-v3-base to run)")

        try:
            classifier = create_classifier("deberta-v3-base")
        except Exception as e:
            self.skipTest(f"Skipping DeBERTa network/download test: {e}")


        self.assertEqual(classifier.provider_name, "deberta-v3-base")
        self.assertTrue(classifier.is_loaded)

        res = classifier.predict(
            subject="Urgent action required: Update account info",
            body="Click here immediately to restore access.",
        )
        self.assertIn("predicted_label", res)
        self.assertIn("predicted_score", res)
        self.assertIn("probabilities", res)
        self.assertIn(res["predicted_label"], ["spam", "safe"])
        self.assertEqual(res["model"], "deberta-v3-base")


if __name__ == "__main__":
    unittest.main()
