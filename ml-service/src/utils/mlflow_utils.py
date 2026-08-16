"""
Utility functions for configuring and logging MLflow experiments.

This module centralizes all MLflow operations so that ModelTrainer
only focuses on model training.
"""

from __future__ import annotations

import sys
from typing import Any, Dict

# Reconfigure stdout/stderr on Windows to handle MLflow unicode emojis (e.g. \U0001f3c3)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.catboost

from src.exception import MyException
from src.logger import logger

import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier


# ============================================================================
# Log Model
# ============================================================================

def log_model_to_mlflow(
    model_name: str,
    model: Any,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    preprocessor_path: Optional[str] = None,
    label_encoder_path: Optional[str] = None,
    schema_path: Optional[str] = None,
    metadata_dict: Optional[Dict[str, Any]] = None,
    register_model: bool = False,
    registered_model_name: Optional[str] = None,
    alias: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Log a trained model along with its complete inference artifact bundle into MLflow.

    Logs:
    - Parameters & metrics
    - Model object
    - Preprocessor (preprocessing.pkl) & Label Encoder (label_encoder.pkl)
    - Schema (schema.yaml) & Metadata (metadata.json)
    - Registers in MLflow Model Registry if register_model=True
    """
    import os
    import json
    import tempfile
    from pathlib import Path
    from src.constants import MLFLOW_MODEL_NAME, MLFLOW_MODEL_ALIAS

    try:
        with mlflow.start_run(run_name=model_name) as run:
            run_id = run.info.run_id

            # 1. Log Parameters & Metrics
            if params:
                mlflow.log_params(params)
            if metrics:
                mlflow.log_metrics(metrics)

            # 2. Log Model Artifact
            if isinstance(model, xgb.XGBClassifier):
                mlflow.xgboost.log_model(xgb_model=model, artifact_path="model")
            elif isinstance(model, CatBoostClassifier):
                mlflow.catboost.log_model(cb_model=model, artifact_path="model")
            elif isinstance(model, lgb.LGBMClassifier):
                mlflow.lightgbm.log_model(lgb_model=model, artifact_path="model")
            elif model is not None:
                mlflow.sklearn.log_model(sk_model=model, artifact_path="model")

            # 3. Log Complete Inference Artifact Bundle
            with tempfile.TemporaryDirectory() as tmp_dir:
                bundle_dir = Path(tmp_dir) / "model_bundle"
                os.makedirs(bundle_dir, exist_ok=True)

                # Copy preprocessor if available
                if preprocessor_path and os.path.exists(preprocessor_path):
                    import shutil
                    shutil.copy2(preprocessor_path, bundle_dir / "preprocessing.pkl")

                # Copy label encoder if available
                if label_encoder_path and os.path.exists(label_encoder_path):
                    import shutil
                    shutil.copy2(label_encoder_path, bundle_dir / "label_encoder.pkl")

                # Copy schema if available
                if schema_path and os.path.exists(schema_path):
                    import shutil
                    shutil.copy2(schema_path, bundle_dir / "schema.yaml")

                # Save metadata json
                import time
                meta = metadata_dict or {}
                meta["model_name"] = model_name
                meta["mlflow_run_id"] = run_id
                meta["logged_at"] = int(time.time() * 1000)
                with open(bundle_dir / "metadata.json", "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)

                mlflow.log_artifacts(str(bundle_dir), artifact_path="model_bundle")

            logger.info("Successfully logged %s artifact bundle to MLflow (run_id: %s)", model_name, run_id)

            # 4. Optional MLflow Model Registry Registration
            if register_model:
                from src.services.mlflow_model_registry import MLflowModelRegistryService
                target_reg_name = registered_model_name or MLFLOW_MODEL_NAME
                target_alias = alias or MLFLOW_MODEL_ALIAS
                registry_service = MLflowModelRegistryService(model_name=target_reg_name)
                res = registry_service.register_and_promote_model(
                    run_id=run_id,
                    artifact_path="model_bundle",
                    alias=target_alias,
                    extra_metadata=meta,
                )
                return res

            return {"run_id": run_id, "model_name": model_name}

    except Exception as e:
        logger.exception("Error logging model to MLflow: %s", e)
        raise MyException(e, sys) from e    