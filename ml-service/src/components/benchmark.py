"""
Benchmark stage for the ML training pipeline.

Inserted between Evaluate and Save::

    Train → Evaluate → **Benchmark** → Save

Measures every candidate model's operational characteristics so the
winning model's metadata includes production-relevant performance data.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
import tracemalloc
from typing import Any, Dict

import numpy as np

from src.logger import logger


class Benchmark:
    """
    Measures training time, inference latency, serialized model size,
    and peak memory usage for a trained model.
    """

    def __init__(self, n_inference_samples: int = 100) -> None:
        self.n_inference_samples = n_inference_samples

    # ── Individual measurements ───────────────────────────────────────────

    def measure_inference_time(self, model: Any, x_sample: np.ndarray) -> float:
        """
        Average single-sample inference time in **milliseconds**.

        Runs a warm-up prediction first, then averages over *n* samples.
        """
        n = min(self.n_inference_samples, len(x_sample))
        sample = x_sample[:n]

        # Warm-up call — JIT / cache effects
        try:
            model.predict(sample[:1])
        except Exception:
            pass

        start = time.perf_counter()
        for i in range(n):
            model.predict(sample[i : i + 1])
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / max(n, 1)) * 1000
        return round(avg_ms, 3)

    def measure_model_size(self, model: Any, serialization: str) -> float:
        """
        Serialized model size in **MB**.

        Temporarily serializes the model to measure on-disk footprint
        without persisting it permanently.
        """
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                if serialization == "huggingface" and hasattr(model, "save_pretrained"):
                    model.save_pretrained(tmpdir)
                    total = sum(
                        os.path.getsize(os.path.join(dp, f))
                        for dp, _, filenames in os.walk(tmpdir)
                        for f in filenames
                    )
                else:
                    import joblib

                    path = os.path.join(tmpdir, "model.joblib")
                    joblib.dump(model, path)
                    total = os.path.getsize(path)
                return round(total / (1024 * 1024), 2)
        except Exception as exc:
            logger.warning("Could not measure model size: %s", exc)
            return 0.0

    def measure_memory_usage(self, model: Any, x_sample: np.ndarray) -> float:
        """
        Peak memory delta in **MB** during a single prediction call.

        Uses ``tracemalloc`` to capture Python-level allocations.
        """
        try:
            sample = x_sample[:1]
            tracemalloc.start()
            model.predict(sample)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return round(peak / (1024 * 1024), 2)
        except Exception as exc:
            logger.warning("Could not measure memory usage: %s", exc)
            if tracemalloc.is_tracing():
                tracemalloc.stop()
            return 0.0

    # ── Orchestrator ──────────────────────────────────────────────────────

    def run(
        self,
        model: Any,
        x_test: np.ndarray,
        serialization: str,
        training_time_sec: float = 0.0,
    ) -> Dict[str, float]:
        """
        Run the full benchmark suite.

        Parameters
        ----------
        model : Any
            Trained model with a ``predict()`` method.
        x_test : np.ndarray
            Test feature matrix for inference benchmarks.
        serialization : str
            ``"joblib"`` or ``"huggingface"`` — determines size measurement strategy.
        training_time_sec : float
            Pre-measured wall-clock training time (passed through).

        Returns
        -------
        Dict[str, float]
            Keys: ``training_time_sec``, ``inference_time_ms``,
            ``model_size_mb``, ``memory_usage_mb``.
        """
        logger.info("Running benchmark suite …")

        results = {
            "training_time_sec": round(training_time_sec, 2),
            "inference_time_ms": self.measure_inference_time(model, x_test),
            "model_size_mb": self.measure_model_size(model, serialization),
            "memory_usage_mb": self.measure_memory_usage(model, x_test),
        }

        logger.info(
            "Benchmark complete — inference: %.1f ms, size: %.1f MB, memory: %.1f MB",
            results["inference_time_ms"],
            results["model_size_mb"],
            results["memory_usage_mb"],
        )
        return results
