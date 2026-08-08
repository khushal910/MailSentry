import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.classifier_factory import create_classifier
from app.services.classifiers.base import BaseClassifier

logger = logging.getLogger("ml_service.ml_engine")


class MLEngine:
    """
    Independent ML Engine responsible for orchestrating the active classifier provider
    (selected via CLASSIFICATION_MODEL env var) and executing predictions.
    """

    _instance: Optional["MLEngine"] = None

    def __init__(self, model_type: Optional[str] = None):
        self.classifier: BaseClassifier = create_classifier(model_type)

    @classmethod
    def get_instance(cls, model_type: Optional[str] = None, force_reload: bool = False) -> "MLEngine":
        if cls._instance is None or force_reload:
            cls._instance = MLEngine(model_type=model_type)
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self.classifier.is_loaded

    @property
    def version(self) -> str:
        if hasattr(self.classifier, "version"):
            return getattr(self.classifier, "version")
        return "v1.0.0"

    @property
    def model_type(self) -> str:
        return self.classifier.provider_name

    @property
    def preprocessor(self) -> Any:
        if hasattr(self.classifier, "preprocessor"):
            return getattr(self.classifier, "preprocessor")
        return None

    @property
    def label_encoder(self) -> Any:
        if hasattr(self.classifier, "label_encoder"):
            return getattr(self.classifier, "label_encoder")
        return None

    @property
    def metadata(self) -> Dict[str, Any]:
        details = self.classifier.details
        return {
            "provider": self.classifier.provider_name,
            "model_type": f"{self.classifier.provider_name.upper()} Classifier",
            "device": self.classifier.device_name,
            "details": details,
            "version": self.version,
        }

    @property
    def schema(self) -> Dict[str, Any]:
        if hasattr(self.classifier, "schema"):
            return getattr(self.classifier, "schema")
        return {}

    def predict(
        self, subject: str, body: str, threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        return self.classifier.predict(subject=subject, body=body, threshold=threshold)
