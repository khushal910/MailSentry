"""
Model loading strategies for the backend serving layer (Factory + Strategy).

All loaders consolidated in one file for project simplicity.

The backend loader returns raw model objects or bundles — the actual
prediction logic lives in :mod:`prediction_engine`.

Extensibility
-------------
To add ONNX serving::

    class OnnxModelLoader(BaseModelLoader): ...
    ModelLoaderFactory.register("onnx", OnnxModelLoader)

No changes to PredictionEngine or the API layer.
"""

from __future__ import annotations

import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Type

logger = logging.getLogger(__name__)


# ============================================================================
# Transformer bundle (lightweight container)
# ============================================================================


class TransformerBundle:
    """
    Lightweight container for a loaded transformer model + tokenizer.

    The :class:`TransformerPredictor` in the prediction engine uses these
    components directly for tokenization and inference.
    """

    __slots__ = ("model", "tokenizer", "device")

    def __init__(self, model: Any, tokenizer: Any, device: str) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = device


# ============================================================================
# Model Loaders
# ============================================================================


class BaseModelLoader(ABC):
    """Abstract interface for model deserialization in the backend."""

    @abstractmethod
    def load(self, champion_dir: str, metadata: dict) -> Any:
        """
        Load and return a model (or bundle) from ``champion_dir/model/``.

        Parameters
        ----------
        champion_dir : str
            Path to the ``champion/`` directory inside the model registry.
        metadata : dict
            Parsed ``metadata.json`` contents.
        """


class SklearnModelLoader(BaseModelLoader):
    """Loads sklearn models saved with **joblib**."""

    def load(self, champion_dir: str, metadata: dict) -> Any:
        import joblib

        model_path = os.path.join(champion_dir, "model", "model.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Sklearn model not found at: {model_path}")
        model = joblib.load(model_path)
        logger.info("Loaded sklearn model via joblib ← %s", model_path)
        return model


class TransformerModelLoader(BaseModelLoader):
    """
    Loads HuggingFace transformer models using ``from_pretrained()``.

    Returns a :class:`TransformerBundle` containing the raw model,
    tokenizer, and device — the prediction engine handles inference logic.
    """

    def load(self, champion_dir: str, metadata: dict) -> TransformerBundle:
        try:
            import torch
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )
        except ImportError as exc:
            raise ImportError(
                "PyTorch and HuggingFace transformers are required to serve "
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

        logger.info(
            "Loaded transformer model ← %s (device: %s)", model_dir, device
        )
        return TransformerBundle(model=model, tokenizer=tokenizer, device=device)


# ============================================================================
# Factory
# ============================================================================


class ModelLoaderFactory:
    """
    Factory for selecting the correct loader based on ``metadata["serialization"]``.

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
        logger.info(
            "Registered model loader: %s → %s", serialization, loader_class.__name__
        )

    @classmethod
    def create(cls, metadata: dict) -> BaseModelLoader:
        """Create the appropriate loader for the given metadata."""
        serialization = metadata.get("serialization", "")
        loader_class = cls._registry.get(serialization)
        if loader_class is None:
            raise ValueError(
                f"No model loader registered for serialization '{serialization}'. "
                f"Available: {list(cls._registry.keys())}"
            )
        return loader_class()
