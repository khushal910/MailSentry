"""
MLflow Model Loader & Dual-Layer Cache.

Handles dynamic resolution of MLflow model URIs (models:/mailsentry-email-classifier@champion,
models:/mailsentry-email-classifier/17), cold-start downloading, in-memory LRU caching,
local disk caching, schema validation, and inference execution.
"""

from __future__ import annotations

import os
import sys
import json
import joblib
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import mlflow
except ImportError:
    mlflow = None

from src.constants import MLFLOW_MODEL_NAME, MLFLOW_MODEL_ALIAS, MLFLOW_CACHE_DIR
from src.logger import logger
from src.exception import MyException



class LoadedModelContainer:
    """Container holding in-memory loaded artifacts for a specific model version."""

    def __init__(
        self,
        model_name: str,
        version: str,
        run_id: str,
        model_uri: str,
        model_obj: Any,
        preprocessor: Any,
        label_encoder: Any,
        schema: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        self.model_name = model_name
        self.version = version
        self.run_id = run_id
        self.model_uri = model_uri
        self.model_obj = model_obj
        self.preprocessor = preprocessor
        self.label_encoder = label_encoder
        self.schema = schema
        self.metadata = metadata
        self.loaded_at = datetime.now(timezone.utc).isoformat()

    def predict(self, subject: str, body: str) -> Dict[str, Any]:
        """Runs inference using the loaded artifacts."""
        subject_str = (subject or "").strip()
        body_str = (body or "").strip()

        # Combine subject and body text
        combined_text = f"{subject_str} {body_str}".strip()

        # Prepare DataFrame input matching pipeline schema
        df = pd.DataFrame([{
            "Subject": subject_str,
            "Message": body_str if body_str else subject_str,
        }])

        # Feature transformation
        if self.preprocessor is not None:
            try:
                # Check if preprocessor transforms raw text or dataframe
                if hasattr(self.preprocessor, "transform"):
                    features = self.preprocessor.transform([combined_text] if isinstance(combined_text, str) else df)
                else:
                    features = [combined_text]
            except Exception:
                features = [combined_text]
        else:
            features = [combined_text]

        # Predict with model
        score = 0.5
        label = "ham"
        import numpy as np

        if hasattr(self.model_obj, "predict_proba"):
            raw_probs = self.model_obj.predict_proba(features)
            probs = np.array(raw_probs)
            if probs.ndim == 2 and probs.shape[1] >= 2:
                raw_score = float(probs[0][1])
                label = "spam" if raw_score >= 0.5 else "ham"
                score = raw_score if label == "spam" else (1.0 - raw_score)
            else:
                raw_pred = self.model_obj.predict(features)[0]
                label = str(raw_pred).lower()
                score = 0.95
        elif hasattr(self.model_obj, "predict"):
            preds = self.model_obj.predict(features)
            raw_pred = preds[0] if isinstance(preds, (list, tuple, pd.Series)) or hasattr(preds, "__getitem__") else preds
            label = "spam" if str(raw_pred).lower() in ("1", "spam", "true", "phishing") else "ham"
            score = 0.95

        # Decode label with label encoder if available
        if self.label_encoder is not None and hasattr(self.label_encoder, "inverse_transform"):
            try:
                decoded = self.label_encoder.inverse_transform([raw_pred])[0]
                label = str(decoded).lower()
            except Exception:
                pass

        # Map 'ham' to 'safe' for standard MailSentry API alignment
        display_label = "safe" if label in ("ham", "not_spam", "clean", "safe") else "spam"

        return {
            "subject": subject_str[:255],
            "predicted_label": display_label,
            "predicted_score": round(score, 4),
            "model_name": self.model_name,
            "model_version": self.version,
            "mlflow_run_id": self.run_id,
            "model_uri": self.model_uri,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }


class MLflowModelLoader:
    """
    Singleton Loader managing dynamic MLflow model downloading and dual-layer caching.
    """

    _instance: Optional[MLflowModelLoader] = None
    _memory_cache: Dict[str, LoadedModelContainer] = {}

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self.cache_dir = cache_dir or MLFLOW_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    @classmethod
    def get_instance(cls, cache_dir: Optional[str] = None) -> MLflowModelLoader:
        if cls._instance is None:
            cls._instance = cls(cache_dir=cache_dir)
        return cls._instance

    @classmethod
    def clear_cache(cls) -> None:
        """Clears memory cache."""
        cls._memory_cache.clear()
        logger.info("Cleared MLflowModelLoader memory cache.")

    def parse_uri(self, uri_or_alias: str) -> Tuple[str, str, str]:
        """
        Parses model URI into (model_name, version_or_alias, resolved_alias_type).
        Supported formats:
        - models:/mailsentry-email-classifier@champion
        - models:/mailsentry-email-classifier/17
        - mailsentry-email-classifier:17
        - mailsentry-email-classifier@champion
        """
        clean_uri = uri_or_alias.strip()

        if clean_uri.startswith("models:/"):
            clean_uri = clean_uri.replace("models:/", "")

        if "@" in clean_uri:
            parts = clean_uri.split("@")
            name = parts[0].strip("/")
            alias = parts[1].strip()
            return name, alias, "alias"
        elif "/" in clean_uri:
            parts = clean_uri.split("/")
            name = parts[0].strip()
            version = parts[1].strip()
            return name, version, "version"
        elif ":" in clean_uri:
            parts = clean_uri.split(":")
            name = parts[0].strip()
            version = parts[1].strip()
            return name, version, "version"
        else:
            # Default to model name with default alias
            return clean_uri, MLFLOW_MODEL_ALIAS, "alias"

    def resolve_model_uri(self, model_name: str, version_or_alias: str, is_alias: bool) -> Tuple[str, str, str]:
        """
        Resolves URI to (exact_version, mlflow_uri, cache_key).
        """
        if is_alias:
            from src.services.mlflow_model_registry import MLflowModelRegistryService
            reg = MLflowModelRegistryService(model_name=model_name)
            try:
                version = reg.resolve_alias(version_or_alias)
                logger.info("Resolved alias '@%s' -> model version '%s'", version_or_alias, version)
            except Exception as e:
                logger.info("MLflow model registry '%s' with alias '@%s' not initialized yet. Using local fallback.", model_name, version_or_alias)
                version = "1"
        else:
            version = version_or_alias.lstrip("v")

        mlflow_uri = f"models:/{model_name}/{version}"
        cache_key = f"{model_name}:{version}"
        return version, mlflow_uri, cache_key

    def load_model(self, model_uri_or_alias: Optional[str] = None) -> LoadedModelContainer:
        """
        Loads a model container by URI/alias with dual-layer caching.
        """
        target_uri = model_uri_or_alias or f"models:/{MLFLOW_MODEL_NAME}@{MLFLOW_MODEL_ALIAS}"
        model_name, ver_or_alias, res_type = self.parse_uri(target_uri)
        is_alias = (res_type == "alias")

        version, mlflow_uri, cache_key = self.resolve_model_uri(model_name, ver_or_alias, is_alias)

        # Layer 1: In-Memory Cache Check
        if cache_key in self._memory_cache:
            logger.debug("In-memory cache HIT for key '%s'", cache_key)
            return self._memory_cache[cache_key]

        # Layer 2: Local Disk Cache Check
        version_disk_dir = os.path.join(self.cache_dir, f"version_{version}")
        os.makedirs(version_disk_dir, exist_ok=True)

        bundle_path = os.path.join(version_disk_dir, "model_bundle")
        if not os.path.exists(bundle_path):
            bundle_path = version_disk_dir

        has_model = any(os.path.exists(os.path.join(bundle_path, f)) for f in ["model.joblib", "model.pkl", "model/model.joblib"])

        if not has_model:
            logger.info("Disk cache MISS for '%s'. Attempting artifact download from MLflow (%s)...", cache_key, mlflow_uri)
            try:
                downloaded_dir = mlflow.artifacts.download_artifacts(artifact_uri=mlflow_uri, dst_path=version_disk_dir)
                logger.info("Successfully downloaded MLflow artifacts to '%s'", downloaded_dir)
                bundle_path = downloaded_dir
            except Exception as dl_err:
                # Check if local fallback models exist in local workspace
                fallback_local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
                if os.path.exists(fallback_local_dir):
                    logger.info("MLflow model registry download unavailable. Loading local fallback model from: %s", fallback_local_dir)
                    bundle_path = fallback_local_dir
                else:
                    raise MyException(f"MLflow model download failed and no local fallback exists: {dl_err}", sys) from dl_err

        # Load artifacts from bundle directory
        model_obj, preprocessor, label_encoder, schema, metadata = self._load_artifacts_from_dir(bundle_path)

        run_id = metadata.get("mlflow_run_id", "unknown_run")
        container = LoadedModelContainer(
            model_name=model_name,
            version=version,
            run_id=run_id,
            model_uri=mlflow_uri,
            model_obj=model_obj,
            preprocessor=preprocessor,
            label_encoder=label_encoder,
            schema=schema,
            metadata=metadata,
        )

        # Store in In-Memory Cache
        self._memory_cache[cache_key] = container
        logger.info("Successfully loaded and cached model container '%s' in memory.", cache_key)
        return container

    def _load_artifacts_from_dir(self, base_dir: str) -> Tuple[Any, Any, Any, Dict[str, Any], Dict[str, Any]]:
        """Deserializes all artifacts from a downloaded bundle folder."""
        # Find model file
        model_file = None
        for candidate in [
            os.path.join(base_dir, "model.joblib"),
            os.path.join(base_dir, "model.pkl"),
            os.path.join(base_dir, "model_bundle", "model.joblib"),
            os.path.join(base_dir, "model", "model.joblib"),
            os.path.join(base_dir, "production", "model", "model.joblib"),
        ]:
            if os.path.exists(candidate):
                model_file = candidate
                break

        model_obj = None
        if model_file:
            model_obj = joblib.load(model_file)
        else:
            logger.warning("No model object binary found in '%s'", base_dir)

        # Find preprocessor
        prep_file = None
        for candidate in [
            os.path.join(base_dir, "preprocessing.pkl"),
            os.path.join(base_dir, "model_bundle", "preprocessing.pkl"),
            os.path.join(base_dir, "preprocessor", "preprocessing.pkl"),
            os.path.join(base_dir, "production", "preprocessor", "preprocessing.pkl"),
        ]:
            if os.path.exists(candidate):
                prep_file = candidate
                break

        preprocessor = joblib.load(prep_file) if prep_file else None

        # Find label encoder
        enc_file = None
        for candidate in [
            os.path.join(base_dir, "label_encoder.pkl"),
            os.path.join(base_dir, "model_bundle", "label_encoder.pkl"),
            os.path.join(base_dir, "preprocessor", "label_encoder.pkl"),
            os.path.join(base_dir, "production", "preprocessor", "label_encoder.pkl"),
        ]:
            if os.path.exists(candidate):
                enc_file = candidate
                break

        label_encoder = joblib.load(enc_file) if enc_file else None

        # Metadata json
        meta_file = None
        for candidate in [
            os.path.join(base_dir, "metadata.json"),
            os.path.join(base_dir, "model_bundle", "metadata.json"),
            os.path.join(base_dir, "production", "metadata.json"),
        ]:
            if os.path.exists(candidate):
                meta_file = candidate
                break

        metadata = {}
        if meta_file:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        schema = {"target_column": "Spam/Ham", "drop_columns": ["Message ID", "Date"]}
        return model_obj, preprocessor, label_encoder, schema, metadata
