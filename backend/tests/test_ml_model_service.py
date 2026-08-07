import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from app.repositories.model_repository import ModelRepository
from app.services.ml_model_service import MLModelService


class TestMLModelService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_models_col = MagicMock()
        self.repo = ModelRepository()
        self.service = MLModelService(models_dir=self.temp_dir, repo=self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_version_string(self):
        v_str = self.service.generate_version_string()
        self.assertTrue(v_str.startswith("v"))

    def test_verify_model_integrity_nonexistent_file(self):
        with self.assertRaises(ValueError):
            self.service.verify_model_integrity(os.path.join(self.temp_dir, "nonexistent.pkl"))

    def test_verify_model_integrity_empty_file(self):
        empty_file = os.path.join(self.temp_dir, "empty.pkl")
        with open(empty_file, "wb") as f:
            pass
        with self.assertRaises(ValueError):
            self.service.verify_model_integrity(empty_file)

    def test_load_latest_model_returns_client(self):
        client = self.service.load_latest_model()
        self.assertIsNotNone(client)

    def test_get_model_or_raise_returns_client(self):
        client = self.service.get_model_or_raise()
        self.assertIsNotNone(client)

    @patch("app.services.ml_client.MLServiceClient.predict_sync")
    def test_classify_text_delegates(self, mock_predict):
        mock_predict.return_value = {
            "subject": "Test",
            "predicted_label": "safe",
            "predicted_score": 0.99
        }
        res = self.service.classify_text(subject="Test", body="Content")
        self.assertEqual(res["predicted_label"], "safe")


if __name__ == "__main__":
    unittest.main()
