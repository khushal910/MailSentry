import glob
import json
import logging
import os
import pickle
import builtins
import sys
import types
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import joblib
import numpy as np

from app.core.config import settings
from app.services.ml_preprocessing import MLPreprocessing, URLFeatureExtractor

logger = logging.getLogger("ml_service.ml_engine")

# Register global unpickling aliases for URLFeatureExtractor
setattr(builtins, "URLFeatureExtractor", URLFeatureExtractor)
for _mod_name in (
    "__main__",
    "unittest.__main__",
    "src.components.data_transformation",
    "src.components",
    "app.services.ml_preprocessing",
):
    if _mod_name not in sys.modules:
        _mod = types.ModuleType(_mod_name)
        sys.modules[_mod_name] = _mod
    setattr(sys.modules[_mod_name], "URLFeatureExtractor", URLFeatureExtractor)


class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == "URLFeatureExtractor":
            return URLFeatureExtractor
        return super().find_class(module, name)


class MLEngine:
    """
    Independent ML Engine responsible for loading preprocessing artifacts, label encoders,
    schema specifications, and model weights, and running predictions.
    """

    _instance: Optional["MLEngine"] = None

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = models_dir or settings.MODELS_DIR
        self.model: Any | None = None
        self.preprocessor: Any | None = None
        self.label_encoder: Any | None = None
        self.metadata: Dict[str, Any] = {}
        self.schema: Dict[str, Any] = {}
        self.version: str = "v1.0.0"
        self.is_loaded: bool = False

        self.load_artifacts()

    @classmethod
    def get_instance(cls) -> "MLEngine":
        if cls._instance is None:
            cls._instance = MLEngine()
        return cls._instance

    def load_artifacts(self) -> bool:
        logger.info(f"Loading ML artifacts from directory: '{self.models_dir}'")
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir, exist_ok=True)

        # 1. Load Preprocessor
        preproc_path = os.path.join(self.models_dir, "preprocessing.pkl")
        if not os.path.exists(preproc_path):
            preproc_path = os.path.join(self.models_dir, "production", "preprocessor", "preprocessing.pkl")

        if os.path.exists(preproc_path):
            try:
                try:
                    self.preprocessor = joblib.load(preproc_path)
                except Exception:
                    with open(preproc_path, "rb") as f:
                        self.preprocessor = CustomUnpickler(f).load()
                logger.info(f"Successfully loaded preprocessor from '{preproc_path}'")
            except Exception as exc:
                logger.warning(f"Failed loading preprocessor from '{preproc_path}': {exc}")

        # 2. Load Label Encoder
        encoder_path = os.path.join(self.models_dir, "label_encoder.pkl")
        if not os.path.exists(encoder_path):
            encoder_path = os.path.join(self.models_dir, "production", "preprocessor", "label_encoder.pkl")

        if os.path.exists(encoder_path):
            try:
                try:
                    self.label_encoder = joblib.load(encoder_path)
                except Exception:
                    with open(encoder_path, "rb") as f:
                        self.label_encoder = CustomUnpickler(f).load()
                logger.info(f"Successfully loaded label encoder from '{encoder_path}'")
            except Exception as exc:
                logger.warning(f"Failed loading label encoder from '{encoder_path}': {exc}")

        # 3. Load Model
        model_paths = [
            os.path.join(self.models_dir, "latest_model.pkl"),
            os.path.join(self.models_dir, "production", "model", "model.joblib"),
            os.path.join(self.models_dir, "production", "model", "model.pkl"),
            os.path.join(self.models_dir, "production", "model.joblib"),
            os.path.join(self.models_dir, "model.joblib"),
            os.path.join(self.models_dir, "model.pkl"),
        ]
        
        pattern_files = glob.glob(os.path.join(self.models_dir, "*.pkl"))
        pattern_files = [f for f in pattern_files if not os.path.basename(f).startswith("preprocessing") and not os.path.basename(f).startswith("label_encoder")]
        if pattern_files:
            pattern_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
            model_paths.insert(0, pattern_files[0])

        for target_path in model_paths:
            if os.path.exists(target_path):
                try:
                    if target_path.endswith(".joblib"):
                        self.model = joblib.load(target_path)
                    else:
                        with open(target_path, "rb") as f:
                            self.model = CustomUnpickler(f).load()
                    logger.info(f"Successfully loaded model from '{target_path}'")
                    break
                except Exception as exc:
                    logger.warning(f"Failed loading model from '{target_path}': {exc}")

        # 4. Load Metadata & Schema
        meta_path = os.path.join(self.models_dir, "production", "metadata.json")
        if not os.path.exists(meta_path):
            meta_path = os.path.join(self.models_dir, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                    self.version = self.metadata.get("version", self.version)
            except Exception as exc:
                logger.warning(f"Failed loading metadata from '{meta_path}': {exc}")

        schema_path = os.path.join(self.models_dir, "schema.yaml")
        if os.path.exists(schema_path):
            try:
                import yaml
                with open(schema_path, "r", encoding="utf-8") as f:
                    self.schema = yaml.safe_load(f) or {}
            except Exception as exc:
                logger.warning(f"Failed loading schema.yaml: {exc}")

        self.is_loaded = self.model is not None
        return self.is_loaded

    def predict(
        self, subject: str, body: str, threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        if not self.is_loaded or self.model is None:
            self.load_artifacts()

        eff_threshold = (
            threshold
            if threshold is not None
            else float(self.metadata.get("threshold", settings.CLASSIFICATION_THRESHOLD))
        )

        cleaned_text = MLPreprocessing.preprocess_email_text(subject, body)

        # Apply Vectorizer / Preprocessor
        if self.preprocessor is not None and hasattr(self.preprocessor, "transform"):
            try:
                features = self.preprocessor.transform([cleaned_text])
            except Exception as p_err:
                logger.warning(f"Preprocessor transform warning: {p_err}")
                features = [cleaned_text]
        else:
            features = [cleaned_text]

        # Model Prediction
        predicted_label = "safe"
        predicted_score = 0.50

        if self.model is not None:
            # Check decision function / predict_proba / predict
            if hasattr(self.model, "predict_proba"):
                try:
                    proba = self.model.predict_proba(features)[0]
                    if len(proba) >= 2:
                        spam_prob = float(proba[1])
                        is_spam = spam_prob >= eff_threshold
                        predicted_label = "spam" if is_spam else "safe"
                        predicted_score = round(float(spam_prob if is_spam else proba[0]), 4)
                    else:
                        predicted_score = round(float(proba[0]), 4)
                        predicted_label = "spam" if predicted_score >= eff_threshold else "safe"
                except Exception as proba_err:
                    logger.warning(f"predict_proba error: {proba_err}")
            
            if predicted_score == 0.50 and hasattr(self.model, "decision_function"):
                try:
                    dec = float(self.model.decision_function(features)[0])
                    prob = float(1.0 / (1.0 + np.exp(-abs(dec))))
                    predicted_score = round(prob, 4)
                    predicted_label = "spam" if dec > 0 else "safe"
                except Exception as dec_err:
                    logger.warning(f"decision_function error: {dec_err}")

            if predicted_label == "safe" and predicted_score == 0.50 and hasattr(self.model, "predict"):
                try:
                    try:
                        preds = self.model.predict(features)
                    except ValueError:
                        arr = np.array(features).reshape(-1, 1)
                        preds = self.model.predict(arr)
                    raw_val = preds[0] if len(preds) > 0 else 0
                    if self.label_encoder and hasattr(self.label_encoder, "inverse_transform"):
                        try:
                            raw_str = str(self.label_encoder.inverse_transform([raw_val])[0]).lower()
                            predicted_label = "spam" if raw_str in ("spam", "1", "1.0") else "safe"
                        except Exception:
                            raw_str = str(raw_val).lower()
                            predicted_label = "spam" if raw_str in ("spam", "1", "1.0") else "safe"
                    else:
                        raw_str = str(raw_val).lower()
                        predicted_label = "spam" if raw_str in ("spam", "1", "1.0") else "safe"
                    predicted_score = 0.85 if predicted_label == "spam" else 0.95
                except Exception as pred_err:
                    logger.warning(f"model predict error: {pred_err}")

        return {
            "subject": (subject or "")[:255],
            "predicted_label": predicted_label,
            "predicted_score": predicted_score,
            "classified_at": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
        }
