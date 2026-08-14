"""
Unit and Integration tests for Centralized MLflow Model Versioning, Dual-Layer Caching, Alias Promotion, and Rollback.
"""

import os
import sys

# Ensure ml-service root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False

from src.services.mlflow_model_registry import (
    MLflowModelRegistryService,
    get_git_commit_sha,
    get_dvc_dataset_hash,
)
from app.services.mlflow_model_loader import MLflowModelLoader, LoadedModelContainer


@unittest.skipUnless(HAS_MLFLOW, "MLflow package not installed")
class TestMLflowModelVersioning(unittest.TestCase):

    def setUp(self):
        MLflowModelLoader.clear_cache()


    def test_git_sha_and_dvc_hash_helpers(self):
        """Test Git SHA and DVC dataset hash extraction helpers."""
        sha = get_git_commit_sha()
        self.assertIsInstance(sha, str)
        self.assertTrue(len(sha) > 0)

        dvc_hash = get_dvc_dataset_hash()
        self.assertIsInstance(dvc_hash, str)
        self.assertTrue(len(dvc_hash) > 0)

    def test_parse_uri(self):
        """Test MLflow model URI parsing helper."""
        loader = MLflowModelLoader.get_instance()

        # Alias URI
        name, ver_or_alias, res_type = loader.parse_uri("models:/mailsentry-email-classifier@champion")
        self.assertEqual(name, "mailsentry-email-classifier")
        self.assertEqual(ver_or_alias, "champion")
        self.assertEqual(res_type, "alias")

        # Version URI
        name, ver_or_alias, res_type = loader.parse_uri("models:/mailsentry-email-classifier/17")
        self.assertEqual(name, "mailsentry-email-classifier")
        self.assertEqual(ver_or_alias, "17")
        self.assertEqual(res_type, "version")

        # Short colon URI
        name, ver_or_alias, res_type = loader.parse_uri("mailsentry-email-classifier:18")
        self.assertEqual(name, "mailsentry-email-classifier")
        self.assertEqual(ver_or_alias, "18")
        self.assertEqual(res_type, "version")

    @patch("src.services.mlflow_model_registry.MlflowClient")
    def test_alias_promotion_and_rollback(self, mock_client_cls):
        """Test model promotion to @champion and rollback to an earlier version."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Mock resolve_alias
        mock_mv = MagicMock()
        mock_mv.version = "17"
        mock_client.get_model_version_by_alias.return_value = mock_mv

        reg_service = MLflowModelRegistryService(model_name="mailsentry-email-classifier")

        # Test set_model_alias (v18 -> champion)
        res_promote = reg_service.set_model_alias(version="18", alias="champion")
        mock_client.set_registered_model_alias.assert_called_with(
            name="mailsentry-email-classifier", alias="champion", version="18"
        )
        self.assertEqual(res_promote["model_version"], "18")
        self.assertEqual(res_promote["stage"], "champion")

        # Test rollback (v18 -> v17 champion)
        res_rollback = reg_service.rollback_alias(target_version="17", alias="champion")
        mock_client.set_registered_model_alias.assert_called_with(
            name="mailsentry-email-classifier", alias="champion", version="17"
        )
        self.assertEqual(res_rollback["model_version"], "17")

    def test_loaded_model_container_predict(self):
        """Test inference execution using LoadedModelContainer."""
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.05, 0.95]]

        container = LoadedModelContainer(
            model_name="mailsentry-email-classifier",
            version="18",
            run_id="run_123",
            model_uri="models:/mailsentry-email-classifier/18",
            model_obj=mock_model,
            preprocessor=None,
            label_encoder=None,
            schema={},
            metadata={"f1": 0.99},
        )

        res = container.predict(subject="Urgent Security Verification", body="Click here to claim money")
        self.assertEqual(res["predicted_label"], "spam")
        self.assertEqual(res["predicted_score"], 0.95)
        self.assertEqual(res["model_version"], "18")
        self.assertEqual(res["model_name"], "mailsentry-email-classifier")

    @patch("src.services.mlflow_model_registry.MlflowClient")
    @patch("src.services.mlflow_model_registry.MLflowModelRegistryService.resolve_alias")
    def test_dual_layer_caching_and_clear(self, mock_resolve, mock_client):
        """Test in-memory cache hit, disk cache hit, and memory cache clearing."""
        mock_resolve.return_value = "18"


        with tempfile.TemporaryDirectory() as tmp_dir:
            loader = MLflowModelLoader(cache_dir=tmp_dir)

            # Create fake disk cache bundle folder for version 18
            ver_dir = Path(tmp_dir) / "version_18"
            os.makedirs(ver_dir, exist_ok=True)

            # Save fake model.joblib in disk cache
            import joblib
            fake_model = {"model_type": "LinearSVC", "C": 1.0}
            joblib.dump(fake_model, ver_dir / "model.joblib")

            meta_data = {"mlflow_run_id": "run_test_18", "accuracy": 0.99}
            with open(ver_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta_data, f)

            # Cold load -> Disk Cache Hit -> Populates Memory Cache
            c1 = loader.load_model("models:/mailsentry-email-classifier@champion")
            self.assertEqual(c1.version, "18")
            self.assertEqual(c1.run_id, "run_test_18")

            # Second load -> In-Memory Cache Hit
            c2 = loader.load_model("models:/mailsentry-email-classifier@champion")
            self.assertIs(c1, c2)

            # Clear cache
            loader.clear_cache()
            self.assertEqual(len(loader._memory_cache), 0)


if __name__ == "__main__":
    unittest.main()
