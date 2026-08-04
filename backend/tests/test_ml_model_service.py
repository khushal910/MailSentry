import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.repositories.model_repository import ModelRepository
from app.services.ml_model_service import MLModelService


class DummyClassifier:
    """Dummy ML Model for testing serialization and predictions."""

    def predict(self, X):
        return ["spam" for _ in X]


class MockDatabase:
    """Mock Database implementation for testing ModelRepository."""

    def __init__(self, models_col):
        self.models_col = models_col

    def __getitem__(self, name):
        return self.models_col


class TestMLModelService(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_models_col = MagicMock()
        self.db_mock = MockDatabase(models_col=self.mock_models_col)
        self.repo = ModelRepository(db=self.db_mock)
        self.service = MLModelService(models_dir=self.temp_dir, repo=self.repo)

        # Reset service static cache before each test
        MLModelService._cached_model = None
        MLModelService._cached_version = None

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_register_model_versioning_and_db_record(self):
        """Verifies saving model creates versioned .pkl file, latest_model.pkl, and DB record."""
        dummy_model = DummyClassifier()
        metrics = {"f1": 0.95, "accuracy": 0.96}

        record = self.service.save_and_register_model(
            model_obj=dummy_model, model_name="spam_classifier", metrics=metrics
        )

        self.assertIsNotNone(record)
        self.assertEqual(record["model_name"], "spam_classifier")
        self.assertTrue(record["version"].startswith("v"))
        self.assertEqual(record["status"], "active")

        # Check versioned file and latest_model.pkl exist
        latest_file = os.path.join(self.temp_dir, "latest_model.pkl")
        self.assertTrue(os.path.exists(latest_file))
        self.assertTrue(os.path.exists(record["path"]))

        # Check DB update calls
        self.mock_models_col.update_many.assert_called_once()
        self.mock_models_col.insert_one.assert_called_once()

    def test_test_mode_validation_detects_corrupted_model(self):
        """Test mode verification must fail if saved file is corrupted or unreadable."""
        corrupted_file = os.path.join(self.temp_dir, "corrupted_model.pkl")
        with open(corrupted_file, "w") as f:
            f.write("CORRUPTED_NON_PICKLE_DATA")

        with self.assertRaises(ValueError) as ctx:
            self.service.verify_model_integrity(corrupted_file)
        self.assertIn("integrity check failed", str(ctx.exception))

    def test_cleanup_retains_latest_three_versions(self):
        """Disk cleanup must keep only the latest 3 versions and delete older versions."""
        dummy_model = DummyClassifier()

        # Create 5 versioned model files
        for i in range(5):
            fname = f"spam_classifier_v20260801_10000{i}.pkl"
            fpath = os.path.join(self.temp_dir, fname)
            with open(fpath, "wb") as f:
                import pickle

                pickle.dump(dummy_model, f)
            # Set artificial modification times
            os.utime(fpath, (1000 + i * 10, 1000 + i * 10))

        deleted = self.service.cleanup_old_models(
            model_name="spam_classifier", keep_count=3
        )
        self.assertEqual(len(deleted), 2)

        # Check remaining files (excluding latest_model.pkl if present)
        remaining = [
            f for f in os.listdir(self.temp_dir) if f.startswith("spam_classifier_v")
        ]
        self.assertEqual(len(remaining), 3)

    def test_load_latest_model(self):
        """Service loads latest model file on demand."""
        dummy_model = DummyClassifier()
        self.service.save_and_register_model(dummy_model)

        loaded_model = self.service.load_latest_model(force_reload=True)
        self.assertIsNotNone(loaded_model)
        self.assertIsInstance(loaded_model, DummyClassifier)
        self.assertEqual(loaded_model.predict(["test"]), ["spam"])

    def test_get_model_or_raise_returns_500_when_missing(self):
        """If model file is missing or corrupted, get_model_or_raise raises 500 Internal Server Error."""
        # Ensure no files in temp_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        empty_service = MLModelService(models_dir=self.temp_dir, repo=self.repo)

        with self.assertRaises(HTTPException) as ctx:
            empty_service.get_model_or_raise()

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn("ML classification model is not available", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
