"""
Rich model metadata for the Model Registry.

This dataclass captures the complete lifecycle information for a trained model.
The backend relies entirely on this metadata to determine how to load, preprocess,
and predict — eliminating all hardcoded framework-specific conditionals.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict


@dataclass
class ModelMetadata:
    """
    Complete metadata for a trained model in the registry.

    Examples
    --------
    Sklearn model::

        ModelMetadata(
            model_name="LinearSVC", framework="sklearn", serialization="joblib",
            input_type="tfidf", preprocessor="tfidf", score=0.990, ...
        )

    Transformer model::

        ModelMetadata(
            model_name="DistilBERT", framework="transformers", serialization="huggingface",
            input_type="raw_text", preprocessor="distilbert-tokenizer", score=0.989, ...
        )
    """

    # ── Identity ──────────────────────────────────────────────────────────
    model_name: str = ""
    framework: str = ""                # "sklearn" | "transformers"
    serialization: str = ""            # "joblib"  | "huggingface"

    # ── Task ──────────────────────────────────────────────────────────────
    task: str = "binary_classification"
    input_type: str = ""               # "tfidf"   | "raw_text"
    output_type: str = "probability"

    # ── Preprocessing ─────────────────────────────────────────────────────
    preprocessor: str = ""             # "tfidf"   | "distilbert-tokenizer"

    # ── Performance ───────────────────────────────────────────────────────
    metric: str = ""                   # primary metric name, e.g. "f1"
    score: float = 0.0                 # primary metric value
    metrics: Dict[str, float] = field(default_factory=dict)

    # ── Versioning ────────────────────────────────────────────────────────
    version: str = ""                  # "v1", "v2", …
    trained_at: str = ""               # ISO-8601 timestamp

    # ── Benchmark ─────────────────────────────────────────────────────────
    training_time_sec: float = 0.0
    inference_time_ms: float = 0.0
    model_size_mb: float = 0.0
    memory_usage_mb: float = 0.0

    # ── Serialization helpers ─────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        """
        Construct from a dictionary, silently ignoring unknown keys.
        This makes the schema forward-compatible — old metadata files
        missing new fields will use dataclass defaults.
        """
        known = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path: str) -> None:
        """Persist metadata as a JSON file."""
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "ModelMetadata":
        """Load metadata from a JSON file."""
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
