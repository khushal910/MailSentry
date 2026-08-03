"""
Model persistence — saving and loading strategies (Factory + Strategy pattern).

All savers and loaders live in this single module for navigability.

**Saving** is used by the training pipeline to serialize the winning model.
**Loading** is used by the training pipeline to reload the current production
champion during the comparison stage.

The backend has its own independent :mod:`model_loader` module because the
serving context has different requirements (e.g. returning a raw
model + tokenizer bundle for the prediction engine).

Extensibility
-------------
To add a new framework (e.g. ONNX)::

    class OnnxModelSaver(BaseModelSaver): ...
    class OnnxModelLoader(BaseModelLoader): ...

    ModelSaverFactory.register("onnx", OnnxModelSaver)
    ModelLoaderFactory.register("onnx", OnnxModelLoader)

No changes to ModelTrainer, PredictionEngine, or the backend API.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from src.entity.model_metadata import ModelMetadata
from src.logger import logger


# ============================================================================
# Model Savers
# ============================================================================


class BaseModelSaver(ABC):
    """Abstract interface for model serialization."""

    @abstractmethod
    def save(self, model: Any, target_dir: str, metadata: ModelMetadata) -> None:
        """
        Serialize *model* artifacts into ``target_dir/model/``.

        Parameters
        ----------
        model : Any
            Trained model object.
        target_dir : str
            Staging directory — the saver creates ``model/`` inside it.
        metadata : ModelMetadata
            Metadata (read-only context, not mutated).
        """


class SklearnModelSaver(BaseModelSaver):
    """Saves sklearn-compatible models using **joblib** (optimized for NumPy)."""

    def save(self, model: Any, target_dir: str, metadata: ModelMetadata) -> None:
        import joblib

        model_dir = os.path.join(target_dir, "model")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "model.joblib")
        joblib.dump(model, model_path)
        logger.info("Saved sklearn model via joblib -> %s", model_path)


class TransformerModelSaver(BaseModelSaver):
    """Saves HuggingFace transformer models using **save_pretrained()**."""

    def save(self, model: Any, target_dir: str, metadata: ModelMetadata) -> None:
        model_dir = os.path.join(target_dir, "model")
        os.makedirs(model_dir, exist_ok=True)

        if not hasattr(model, "save_pretrained"):
            raise TypeError(
                f"Model {type(model).__name__} does not support save_pretrained(). "
                f"Ensure the model is wrapped with a HuggingFace-compatible wrapper."
            )

        model.save_pretrained(model_dir)
        logger.info("Saved transformer model via save_pretrained → %s", model_dir)


class ModelSaverFactory:
    """
    Factory for selecting the correct saver based on ``metadata.serialization``.

    Built-in registrations::

        "joblib"      → SklearnModelSaver
        "huggingface" → TransformerModelSaver
    """

    _registry: Dict[str, Type[BaseModelSaver]] = {
        "joblib": SklearnModelSaver,
        "huggingface": TransformerModelSaver,
    }

    @classmethod
    def register(cls, serialization: str, saver_class: Type[BaseModelSaver]) -> None:
        """Register a new saver at runtime."""
        cls._registry[serialization] = saver_class
        logger.info("Registered model saver: %s → %s", serialization, saver_class.__name__)

    @classmethod
    def create(cls, metadata: ModelMetadata) -> BaseModelSaver:
        """Create the appropriate saver for the given metadata."""
        saver_class = cls._registry.get(metadata.serialization)
        if saver_class is None:
            raise ValueError(
                f"No model saver registered for serialization '{metadata.serialization}'. "
                f"Available: {list(cls._registry.keys())}"
            )
        return saver_class()


# ============================================================================
# Model Loaders  (used by ModelTrainer for production model comparison)
# ============================================================================


class BaseModelLoader(ABC):
    """Abstract interface for model deserialization."""

    @abstractmethod
    def load(self, champion_dir: str, metadata: ModelMetadata) -> Any:
        """
        Load and return a model object from ``champion_dir/model/``.

        The returned object must support ``.predict()`` so the training
        pipeline can run comparison predictions.
        """


class SklearnModelLoader(BaseModelLoader):
    """Loads sklearn models previously saved with joblib."""

    def load(self, champion_dir: str, metadata: ModelMetadata) -> Any:
        import joblib

        model_path = os.path.join(champion_dir, "model", "model.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Sklearn model not found at: {model_path}")
        model = joblib.load(model_path)
        logger.info("Loaded sklearn model via joblib <- %s", model_path)
        return model


class TransformerModelLoader(BaseModelLoader):
    """
    Loads HuggingFace transformer models and wraps them in
    :class:`DistilBERTModelWrapper` for predict() compatibility.
    """

    def load(self, champion_dir: str, metadata: ModelMetadata) -> Any:
        # Import here to keep transformers/torch as optional dependencies
        from src.components.transformer_trainer import DistilBERTModelWrapper

        try:
            import torch
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )
        except ImportError as exc:
            raise ImportError(
                "PyTorch and HuggingFace transformers are required to load "
                "transformer models."
            ) from exc

        model_dir = os.path.join(champion_dir, "model")
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Transformer model not found at: {model_dir}")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        model.to(device)
        model.eval()

        logger.info("Loaded transformer model ← %s (device: %s)", model_dir, device)
        return DistilBERTModelWrapper(model=model, tokenizer=tokenizer, device=device)


class ModelLoaderFactory:
    """
    Factory for selecting the correct loader based on ``metadata.serialization``.

    Built-in registrations::

        "joblib"      → SklearnModelLoader
        "huggingface" → TransformerModelLoader
    """

    _registry: Dict[str, Type[BaseModelLoader]] = {
        "joblib": SklearnModelLoader,
        "huggingface": TransformerModelLoader,
    }

    @classmethod
    def register(cls, serialization: str, loader_class: Type[BaseModelLoader]) -> None:
        """Register a new loader at runtime."""
        cls._registry[serialization] = loader_class
        logger.info("Registered model loader: %s → %s", serialization, loader_class.__name__)

    @classmethod
    def create(cls, metadata: ModelMetadata) -> BaseModelLoader:
        """Create the appropriate loader for the given metadata."""
        loader_class = cls._registry.get(metadata.serialization)
        if loader_class is None:
            raise ValueError(
                f"No model loader registered for serialization '{metadata.serialization}'. "
                f"Available: {list(cls._registry.keys())}"
            )
        return loader_class()
