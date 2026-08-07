import glob
import logging
import os
import pickle
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.model_repository import ModelRepository
from app.services.prediction_engine import PredictionEngine

logger = logging.getLogger(__name__)


class MLModelService:
    """
    Service layer for MailSentry backend.
    Delegates email classification to independent ml-service microservice over HTTP.
    """

    _cached_model: Any | None = None
    _cached_preprocessor: Any | None = None
    _cached_label_encoder: Any | None = None
    _cached_version: str | None = None
    _cached_model_type: str | None = None

    def __init__(
        self, models_dir: str | None = None, repo: ModelRepository | None = None
    ):
        self.models_dir = (
            models_dir
            if models_dir is not None
            else getattr(settings, "MODELS_DIR", os.path.join(os.getcwd(), "models"))
        )
        self.repo = repo if repo is not None else ModelRepository()

    def generate_version_string(self) -> str:
        """Generates a timestamp-based version string e.g., v20260801_103527."""
        now = datetime.now(timezone.utc)
        return f"v{now.strftime('%Y%m%d_%H%M%S')}"

    def verify_model_integrity(self, file_path: str) -> Any:
        if not os.path.exists(file_path):
            raise ValueError(f"Model file '{file_path}' does not exist.")
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"Model file '{file_path}' is empty.")
        with open(file_path, "rb") as f:
            return pickle.load(f)

    def load_latest_model(self, force_reload: bool = False) -> Any | None:
        """
        Returns MLServiceClient microservice handler.
        """
        from app.services.ml_client import MLServiceClient

        return MLServiceClient()

    def get_model_or_raise(self) -> Any:
        """
        Returns active MLServiceClient handler.
        """
        from app.services.ml_client import MLServiceClient

        return MLServiceClient()

    def load_preprocessor(self) -> Any | None:
        return None

    def load_label_encoder(self) -> Any | None:
        return None

    def classify_text(self, subject: str, body: str) -> dict[str, Any]:
        """
        Classifies email content using independent ml-service microservice.
        Delegates HTTP request via MLServiceClient.
        """
        from app.services.ml_client import MLServiceClient

        client = MLServiceClient()
        try:
            return client.predict_sync(subject=subject, body=body)
        except Exception as exc:
            logger.warning(
                f"MLServiceClient prediction failed ({exc}), falling back to PredictionEngine."
            )
            engine = PredictionEngine(self.models_dir)
            return engine.predict(subject=subject, body=body)
