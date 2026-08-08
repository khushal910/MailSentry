import logging
import os
from typing import Optional

from app.core.config import settings
from app.services.classifiers.base import BaseClassifier
from app.services.classifiers.mlops_classifier import MlopsClassifier

logger = logging.getLogger("ml_service.classifier_factory")


def print_startup_banner(classifier: BaseClassifier) -> None:
    provider = classifier.provider_name.lower()
    details = classifier.details

    lines = [
        "==================================================",
        "MailSentry Classification Model",
        "==================================================",
        f"Provider: {provider}",
    ]

    if provider == "roberta":
        lines.append(f"Base Model: {details.get('base_model', 'FacebookAI/roberta-base')}")
        lines.append(f"Adapter: {details.get('adapter', 'ssheroz/spam-email-classifier-roberta-r8')}")
        lines.append(f"Device: {classifier.device_name}")
    elif provider == "mlops":
        lines.append(f"Model: Scikit-Learn / MLOps Pipeline")
        lines.append(f"Artifact: {details.get('model_path', settings.MODELS_DIR)}")

    lines.append("==================================================")
    banner_text = "\n".join(lines)
    logger.info("\n" + banner_text)


def create_classifier(model_type: Optional[str] = None) -> BaseClassifier:
    """
    Factory function that creates and returns the requested spam classifier instance.
    Selected via CLASSIFICATION_MODEL environment variable (default: 'mlops').
    """
    if model_type is None:
        model_type = getattr(settings, "CLASSIFICATION_MODEL", None) or os.getenv(
            "CLASSIFICATION_MODEL", "mlops"
        )

    provider = str(model_type).lower().strip()

    if provider == "mlops":
        classifier = MlopsClassifier()
        print_startup_banner(classifier)
        return classifier

    if provider == "roberta":
        from app.services.classifiers.roberta_classifier import RobertaClassifier

        classifier = RobertaClassifier()
        print_startup_banner(classifier)
        return classifier

    err_msg = (
        f"Unsupported CLASSIFICATION_MODEL='{model_type}'. "
        f"Supported values: mlops, roberta"
    )
    logger.error(err_msg)
    raise ValueError(err_msg)
