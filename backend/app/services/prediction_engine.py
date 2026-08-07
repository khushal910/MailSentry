"""
PredictionEngine
================
Delegates classification requests to the independent ml-service microservice over HTTP.
Provides a graceful keyword fallback if ml-service is temporarily unreachable.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    Singleton orchestrator for email prediction requests.
    Delegates to MLServiceClient microservice API with keyword fallback.
    """

    _instance: Optional["PredictionEngine"] = None

    def __init__(self, models_dir: Optional[str] = None) -> None:
        self.models_dir = models_dir

    @classmethod
    def reload(cls) -> None:
        """Resets singleton cache if needed."""
        cls._instance = None

    def predict(self, subject: str, body: str) -> dict[str, Any]:
        """
        Classifies email content. Delegates to MLServiceClient microservice API.
        Falls back to keyword heuristic if ml-service is unreachable.
        """
        try:
            from app.services.ml_client import MLServiceClient

            client = MLServiceClient()
            return client.predict_sync(subject=subject, body=body)
        except Exception as err:
            logger.warning(
                "MLServiceClient unreachable (%s) — using keyword heuristic fallback.",
                err,
            )

        # Fallback when microservice is unreachable
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
            "predicted_label": "spam" if is_spam else "safe",
            "predicted_score": 0.95 if is_spam else 0.50,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }
