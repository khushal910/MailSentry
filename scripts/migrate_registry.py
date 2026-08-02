"""
One-time migration script to bootstrap the Model Registry from existing legacy model artifacts.

Usage
-----
Run from project root:

    python scripts/migrate_registry.py
"""

from __future__ import annotations

import json
import os
import sys
import shutil
from datetime import datetime, timezone
import yaml
import joblib

# Add ml-service/src to sys.path so imports work properly
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ML_SERVICE_DIR = os.path.join(ROOT_DIR, "ml-service")
if ML_SERVICE_DIR not in sys.path:
    sys.path.insert(0, ML_SERVICE_DIR)

from src.entity.model_metadata import ModelMetadata
from src.services.storage_service import LocalStorageService
from src.services.model_registry import ModelRegistry


def migrate() -> None:
    print("Starting Model Registry migration...")

    registry_path = os.path.join(ROOT_DIR, "model_registry")
    registry = ModelRegistry(registry_path)

    if registry.has_champion():
        print(f"Model Registry at '{registry_path}' already contains a champion model. Skipping migration.")
        return

    # Check for legacy artifacts in ml-service/artifact/
    model_trainer_dir = os.path.join(ML_SERVICE_DIR, "artifact", "model_trainer")
    data_transform_dir = os.path.join(ML_SERVICE_DIR, "artifact", "data_transformation")
    backend_models_dir = os.path.join(ROOT_DIR, "backend", "models")

    legacy_model_pkl = os.path.join(model_trainer_dir, "model.pkl")
    legacy_backend_pkl = os.path.join(backend_models_dir, "model.pkl")
    legacy_distilbert_dir = os.path.join(model_trainer_dir, "distilbert_model")
    legacy_report_path = os.path.join(model_trainer_dir, "model_report.yaml")

    staging_dir = os.path.join(registry_path, "_staging_tmp")
    staging_model_dir = os.path.join(staging_dir, "model")
    staging_prep_dir = os.path.join(staging_dir, "preprocessor")

    os.makedirs(staging_model_dir, exist_ok=True)
    os.makedirs(staging_prep_dir, exist_ok=True)

    # 1. Determine model framework and copy model file
    if os.path.exists(legacy_distilbert_dir) and os.path.isdir(legacy_distilbert_dir):
        print(f"Found legacy DistilBERT model directory at {legacy_distilbert_dir}")
        shutil.copytree(legacy_distilbert_dir, staging_model_dir, dirs_exist_ok=True)
        model_name = "DistilBERT"
        framework = "transformers"
        serialization = "huggingface"
        input_type = "raw_text"
        preprocessor_name = "distilbert-tokenizer"
    else:
        source_pkl = None
        if os.path.exists(legacy_model_pkl):
            source_pkl = legacy_model_pkl
        elif os.path.exists(legacy_backend_pkl):
            source_pkl = legacy_backend_pkl

        if source_pkl and os.path.exists(source_pkl):
            print(f"Found legacy pickle model at {source_pkl}")
            import pickle
            try:
                with open(source_pkl, "rb") as f:
                    model_obj = pickle.load(f)
                target_joblib = os.path.join(staging_model_dir, "model.joblib")
                joblib.dump(model_obj, target_joblib)
                print(f"Converted pickle -> joblib at {target_joblib}")
                model_name = getattr(model_obj, "__class__", type(model_obj)).__name__
            except Exception as e:
                print(f"Error loading legacy pickle: {e}")
                model_name = "LegacyModel"
        else:
            print("No legacy model files found. Initializing empty champion metadata template.")
            model_name = "None"

        framework = "sklearn"
        serialization = "joblib"
        input_type = "tfidf"
        preprocessor_name = "tfidf"

    # 2. Copy preprocessor files if present
    prep_pkl = os.path.join(data_transform_dir, "preprocessing.pkl")
    label_enc_pkl = os.path.join(data_transform_dir, "label_encoder.pkl")

    if not os.path.exists(prep_pkl):
        prep_pkl = os.path.join(backend_models_dir, "preprocessing.pkl")
    if not os.path.exists(label_enc_pkl):
        label_enc_pkl = os.path.join(backend_models_dir, "label_encoder.pkl")

    if os.path.exists(prep_pkl):
        shutil.copy2(prep_pkl, os.path.join(staging_prep_dir, "preprocessing.pkl"))
        print(f"Copied preprocessing.pkl -> {staging_prep_dir}")
    if os.path.exists(label_enc_pkl):
        shutil.copy2(label_enc_pkl, os.path.join(staging_prep_dir, "label_encoder.pkl"))
        print(f"Copied label_encoder.pkl -> {staging_prep_dir}")

    # 3. Parse legacy report for metrics
    metrics = {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0}
    score = 0.0
    if os.path.exists(legacy_report_path):
        try:
            with open(legacy_report_path, "r", encoding="utf-8") as f:
                report_data = yaml.safe_load(f)
            if isinstance(report_data, dict):
                report_name = report_data.get("best_model_name")
                if report_name:
                    model_name = report_name
                winner_metrics = report_data.get("winner_metrics")
                if isinstance(winner_metrics, dict):
                    metrics = winner_metrics
                    score = float(winner_metrics.get("f1", 0.0))
        except Exception as err:
            print(f"Warning: Could not parse {legacy_report_path}: {err}")

    # 4. Construct metadata and promote to champion
    metadata = ModelMetadata(
        model_name=model_name,
        framework=framework,
        serialization=serialization,
        task="binary_classification",
        input_type=input_type,
        output_type="probability",
        preprocessor=preprocessor_name,
        metric="f1",
        score=score,
        metrics=metrics,
        version="v1",
        trained_at=datetime.now(timezone.utc).isoformat(),
        training_time_sec=0.0,
        inference_time_ms=0.0,
        model_size_mb=0.0,
        memory_usage_mb=0.0
    )

    registry.promote_champion(staging_dir, metadata)

    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)

    print("Migration complete! Champion model successfully established at:")
    print(f"  {registry.champion_path}")


if __name__ == "__main__":
    migrate()
