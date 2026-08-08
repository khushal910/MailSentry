from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseClassifier(ABC):
    """
    Abstract Base Class defining the contract for all email classification model providers.
    """

    @abstractmethod
    def load(self) -> bool:
        """
        Load model weights and artifacts into memory.
        Must be called once at application startup.
        """
        pass

    @abstractmethod
    def predict(
        self, subject: str, body: str, threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Run prediction inference on subject and body text.
        Must return normalized result schema:
        {
            "subject": str,
            "predicted_label": str ("spam" or "safe"),
            "predicted_score": float,
            "probabilities": {"safe": float, "spam": float},
            "classified_at": str (ISO timestamp),
            "version": str,
            "model": str ("mlops" or "roberta")
        }
        """
        pass

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def device_name(self) -> str:
        pass

    @property
    @abstractmethod
    def details(self) -> Dict[str, Any]:
        pass
