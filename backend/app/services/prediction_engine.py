"""
Prediction Engine — Singleton orchestrator with model caching.

Contains all predictor strategies, the predictor factory, and the
top-level engine.  The backend API never sees framework-specific code::

    engine = PredictionEngine(registry_path)
    result = engine.predict(subject, body)

**Singleton + Caching**:  The model, tokenizer, and preprocessor are
loaded *once* at first access.  Subsequent calls reuse the cached objects.
Call ``PredictionEngine.reload()`` after a champion update or rollback.

Extensibility
-------------
To add a RoBERTa predictor::

    class RoBERTaPredictor(BasePredictor): ...
    PredictorFactory.register("roberta", RoBERTaPredictor)

No changes to PredictionEngine or the API layer.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.services.model_loader import ModelLoaderFactory, TransformerBundle

import builtins
import sys
import types
import app.services.ml_preprocessing as ml_prep

logger = logging.getLogger(__name__)

# Register global unpickling aliases so joblib/pickle finds URLFeatureExtractor everywhere
setattr(builtins, "URLFeatureExtractor", ml_prep.URLFeatureExtractor)

for _mod_name in (
    "__main__",
    "unittest.__main__",
    "src.components.data_transformation",
    "src.components",
):
    if _mod_name not in sys.modules:
        _mod = types.ModuleType(_mod_name)
        sys.modules[_mod_name] = _mod
    setattr(sys.modules[_mod_name], "URLFeatureExtractor", ml_prep.URLFeatureExtractor)


# ============================================================================
# Predictor strategies
# ============================================================================


class BasePredictor(ABC):
    """
    Abstract prediction interface.

    Every predictor exposes the same ``predict(subject, body)`` method,
    regardless of the underlying framework.  The API layer is unaware
    which concrete predictor is active.
    """

    @abstractmethod
    def predict(self, subject: str, body: str) -> dict[str, Any]:
        """
        Classify email content.

        Returns
        -------
        dict
            ``{predicted_label, predicted_score, subject, classified_at}``
        """


class SklearnPredictor(BasePredictor):
    """
    Sklearn prediction strategy.

    Pipeline: text cleaning → TF-IDF transform → model.predict() → label decode.
    """

    def __init__(self, model: Any, champion_dir: str) -> None:
        self.model = model
        self.preprocessor = self._load_artifact(champion_dir, "preprocessing.pkl")
        self.label_encoder = self._load_artifact(champion_dir, "label_encoder.pkl")

    @staticmethod
    def _load_artifact(champion_dir: str, filename: str) -> Any | None:
        """Load a pickle/joblib artifact from champion_dir or champion_dir/preprocessor/."""
        import builtins
        import joblib
        import pickle
        import sys
        import types
        import app.services.ml_preprocessing as ml_prep

        # Alias URLFeatureExtractor across builtins & sys.modules
        setattr(builtins, "URLFeatureExtractor", ml_prep.URLFeatureExtractor)

        for mod_name in ("__main__", "src.components.data_transformation", "src.components"):
            if mod_name not in sys.modules:
                mod = types.ModuleType(mod_name)
                sys.modules[mod_name] = mod
            setattr(sys.modules[mod_name], "URLFeatureExtractor", ml_prep.URLFeatureExtractor)

        possible_paths = [
            os.path.join(champion_dir, filename),
            os.path.join(champion_dir, "preprocessor", filename),
        ]
        path = next((p for p in possible_paths if os.path.exists(p)), None)
        if path:
            try:
                try:
                    obj = joblib.load(path)
                except (AttributeError, ModuleNotFoundError, ImportError):
                    with open(path, "rb") as f:
                        class CustomUnpickler(pickle.Unpickler):
                            def find_class(self, module, name):
                                if name == "URLFeatureExtractor":
                                    return ml_prep.URLFeatureExtractor
                                return super().find_class(module, name)

                        obj = CustomUnpickler(f).load()
                logger.info("Loaded %s from %s", filename, path)
                return obj
            except Exception as exc:
                logger.warning("Failed to load %s: %s", filename, exc)
        return None

    def predict(self, subject: str, body: str) -> dict[str, Any]:
        from app.core.config import settings
        from app.services.ml_preprocessing import MLPreprocessing

        subject_str = (subject or "").strip()
        body_str = (body or "").strip()
        cleaned_text = MLPreprocessing.preprocess_email_text(subject_str, body_str)

        threshold = float(getattr(settings, "CLASSIFICATION_THRESHOLD", 0.50))
        predicted_label = "safe"
        predicted_score = 0.50

        try:
            # Vectorize
            if self.preprocessor is not None and hasattr(
                self.preprocessor, "transform"
            ):
                X_features = self.preprocessor.transform([cleaned_text])
            else:
                X_features = [cleaned_text]

            # Determine class & score based on probabilities and configurable threshold
            if hasattr(self.model, "predict_proba"):
                try:
                    proba = self.model.predict_proba(X_features)[0]
                    if len(proba) >= 2:
                        spam_prob = float(proba[1])
                        is_spam = spam_prob >= threshold
                        predicted_label = "spam" if is_spam else "safe"
                        predicted_score = round(float(spam_prob if is_spam else proba[0]), 4)
                    else:
                        predicted_score = round(float(proba[0]), 4)
                        predicted_label = "spam" if predicted_score >= threshold else "safe"
                except Exception as proba_err:
                    logger.warning("predict_proba error: %s", proba_err)
            elif hasattr(self.model, "decision_function"):
                try:
                    dec = float(self.model.decision_function(X_features)[0])
                    spam_prob = float(1.0 / (1.0 + np.exp(-dec)))
                    is_spam = spam_prob >= threshold
                    predicted_label = "spam" if is_spam else "safe"
                    predicted_score = round(float(spam_prob if is_spam else 1.0 - spam_prob), 4)
                except Exception as dec_err:
                    logger.warning("decision_function error: %s", dec_err)
            elif hasattr(self.model, "predict"):
                try:
                    res = self.model.predict(X_features)
                    if res is not None and len(res) > 0:
                        raw_val = res[0]
                        if self.label_encoder is not None and hasattr(
                            self.label_encoder, "inverse_transform"
                        ):
                            decoded = self.label_encoder.inverse_transform([raw_val])
                            label_str = str(decoded[0]).lower()
                            predicted_label = "spam" if label_str in ("spam", "1", "1.0") else "safe"
                            predicted_score = 0.90
                        elif isinstance(raw_val, (int, float)):
                            predicted_label = "spam" if int(raw_val) == 1 else "safe"
                            predicted_score = 0.90
                        else:
                            label_str = str(raw_val).lower()
                            predicted_label = "spam" if label_str in ("spam", "1", "1.0") else "safe"
                            predicted_score = 0.90
                except Exception as pred_err:
                    logger.warning("predict error: %s", pred_err)

        except Exception as err:
            logger.warning("Sklearn prediction fallback engaged: %s", err)
            combined_text = f"{subject_str} {body_str}".lower()
            spam_keywords = [
                "spam",
                "winner",
                "lottery",
                "claim",
                "prize",
                "free money",
                "urgent security",
            ]
            if any(kw in combined_text for kw in spam_keywords):
                predicted_label = "spam"
                predicted_score = 0.95
            else:
                predicted_label = "safe"
                predicted_score = 0.85

        return {
            "subject": subject_str,
            "predicted_label": predicted_label,
            "predicted_score": predicted_score,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }


class TransformerPredictor(BasePredictor):
    """
    Transformer prediction strategy.

    Pipeline: text cleaning → tokenize → forward pass → softmax → prediction.
    """

    def __init__(self, model: Any, champion_dir: str) -> None:
        if not isinstance(model, TransformerBundle):
            raise TypeError(
                f"TransformerPredictor expects a TransformerBundle, got {type(model).__name__}"
            )
        self.bundle: TransformerBundle = model

    def predict(self, subject: str, body: str) -> dict[str, Any]:
        import torch

        from app.core.config import settings
        from app.services.ml_preprocessing import MLPreprocessing

        subject_str = (subject or "").strip()
        body_str = (body or "").strip()
        cleaned_text = MLPreprocessing.preprocess_email_text(subject_str, body_str)

        threshold = float(getattr(settings, "CLASSIFICATION_THRESHOLD", 0.50))
        predicted_label = "safe"
        predicted_score = 0.50

        try:
            self.bundle.model.eval()
            inputs = self.bundle.tokenizer(
                [cleaned_text],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.bundle.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.bundle.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()[0]

            if len(probs) >= 2:
                spam_prob = float(probs[1])
                is_spam = spam_prob >= threshold
                predicted_label = "spam" if is_spam else "safe"
                predicted_score = round(float(spam_prob if is_spam else probs[0]), 4)
            else:
                predicted_score = round(float(probs[0]), 4)
                predicted_label = "spam" if predicted_score >= threshold else "safe"

        except Exception as err:
            logger.warning("Transformer prediction fallback engaged: %s", err)
            combined_text = f"{subject_str} {body_str}".lower()
            spam_keywords = [
                "spam",
                "winner",
                "lottery",
                "claim",
                "prize",
                "free money",
                "urgent security",
            ]
            if any(kw in combined_text for kw in spam_keywords):
                predicted_label = "spam"
                predicted_score = 0.95
            else:
                predicted_label = "safe"
                predicted_score = 0.85

        return {
            "subject": subject_str,
            "predicted_label": predicted_label,
            "predicted_score": predicted_score,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }


# ============================================================================
# Predictor Factory
# ============================================================================


class PredictorFactory:
    """
    Factory for creating the correct predictor based on ``metadata["framework"]``.

    Both predictor constructors accept the same ``(model, champion_dir)``
    signature, so the factory has no framework-specific branching.

    Built-in registrations::

        "sklearn"      → SklearnPredictor
        "transformers" → TransformerPredictor
    """

    _registry: dict[str, type[BasePredictor]] = {
        "sklearn": SklearnPredictor,
        "transformers": TransformerPredictor,
    }

    @classmethod
    def register(cls, framework: str, predictor_class: type[BasePredictor]) -> None:
        """Register a new predictor at runtime."""
        cls._registry[framework] = predictor_class
        logger.info(
            "Registered predictor: %s → %s", framework, predictor_class.__name__
        )

    @classmethod
    def create(cls, metadata: dict, model: Any, champion_dir: str) -> BasePredictor:
        """Create the appropriate predictor based on ``metadata["framework"]``."""
        framework = metadata.get("framework", "")
        predictor_class = cls._registry.get(framework)
        if predictor_class is None:
            raise ValueError(
                f"No predictor registered for framework '{framework}'. "
                f"Available: {list(cls._registry.keys())}"
            )
        return predictor_class(model=model, champion_dir=champion_dir)


# ============================================================================
# Prediction Engine  (Singleton + Cached)
# ============================================================================


class PredictionEngine:
    """
    Top-level prediction orchestrator.

    **Singleton pattern** — ensures the model is loaded exactly once.
    The engine reads ``metadata.json`` from the champion directory,
    selects the correct loader and predictor via factories, and caches
    everything in memory.

    Usage (backend API)::

        engine = PredictionEngine(registry_path)   # first call loads model
        result = engine.predict(subject, body)      # all calls reuse cache

    After model update or rollback::

        PredictionEngine.reload()                  # reset cache
    """

    _instance: PredictionEngine | None = None
    _initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> PredictionEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, registry_path: str | None = None) -> None:
        if PredictionEngine._initialized:
            return

        if not registry_path:
            backend_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            registry_path = os.path.join(backend_dir, "models")

        possible_dirs = [
            os.path.join(registry_path, "production"),
            os.path.join(registry_path, "champion"),
            registry_path,
        ]

        champion_dir = next(
            (
                d
                for d in possible_dirs
                if os.path.exists(os.path.join(d, "metadata.json"))
            ),
            os.path.join(registry_path, "production"),
        )
        meta_path = os.path.join(champion_dir, "metadata.json")

        if not os.path.exists(meta_path):
            logger.warning(
                "No champion metadata found at %s — "
                "PredictionEngine will operate in fallback mode.",
                meta_path,
            )
            self.metadata: dict | None = None
            self.predictor: BasePredictor | None = None
            PredictionEngine._initialized = True
            return

        # Load metadata
        with open(meta_path, "r", encoding="utf-8") as fh:
            self.metadata = json.load(fh)

        logger.info(
            "Initializing PredictionEngine — model: %s, framework: %s",
            self.metadata.get("model_name"),
            self.metadata.get("framework"),
        )

        # Load model via factory
        loader = ModelLoaderFactory.create(self.metadata)
        model = loader.load(champion_dir, self.metadata)

        # Create predictor via factory
        self.predictor = PredictorFactory.create(self.metadata, model, champion_dir)

        PredictionEngine._initialized = True
        logger.info("PredictionEngine ready — model cached in memory.")

    def predict(self, subject: str, body: str) -> dict[str, Any]:
        """
        Classify an email.  Delegates to the cached predictor strategy.

        Falls back to a keyword heuristic if no model is loaded.
        """
        if self.predictor is not None:
            return self.predictor.predict(subject, body)

        # Fallback when no champion is available
        logger.warning("No model loaded — using keyword heuristic fallback.")
        subject_str = (subject or "").strip()
        body_str = (body or "").strip()
        combined = f"{subject_str} {body_str}".lower()
        spam_keywords = [
            "spam",
            "winner",
            "lottery",
            "claim",
            "prize",
            "free money",
            "urgent security",
        ]
        is_spam = any(kw in combined for kw in spam_keywords)
        return {
            "subject": subject_str,
            "predicted_label": "spam" if is_spam else "inbox",
            "predicted_score": 0.95 if is_spam else 0.50,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def reload(cls) -> None:
        """
        Reset the singleton so the next instantiation reloads from disk.

        Call this after ``ModelRegistry.promote_champion()`` or
        ``ModelRegistry.rollback()`` to pick up the new model without
        restarting the backend process.
        """
        cls._initialized = False
        cls._instance = None
        logger.info("PredictionEngine cache invalidated — will reload on next access.")
