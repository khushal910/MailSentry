import logging
import os
from typing import Optional

from app.core.config import settings
from app.core.model_registry import (
    MODEL_REGISTRY,
    get_model_config,
    list_supported_models,
    normalize_model_key,
)
from app.services.classifiers.base import BaseClassifier
from app.services.classifiers.mlops_classifier import MlopsClassifier

logger = logging.getLogger("ml_service.classifier_factory")


def print_startup_banner(classifier: BaseClassifier) -> None:
    provider = classifier.provider_name.lower()
    details = classifier.details

    lines = [
        "==================================================",
        f"Email classifier: {classifier.provider_name.upper()}",
        "==================================================",
        f"Provider: {provider}",
    ]

    if provider == "otis":
        lines.append(f"Base Model: {details.get('base_model', 'Titeiiko/OTIS-Official-Spam-Model')}")
        lines.append(f"Device: {classifier.device_name}")
    elif provider in ("deberta-v3-base", "deberta"):
        lines.append(f"Base Model: {details.get('base_model', 'microsoft/deberta-v3-base')}")
        lines.append(f"Adapter: {details.get('adapter', 'ssheroz/spam-email-classifier-deberta-v3-base-r8')}")
        lines.append(f"Device: {classifier.device_name}")
        lines.append(f"Target Modules: {details.get('target_modules', ['query_proj', 'key_proj', 'value_proj'])}")
    elif provider == "roberta":
        lines.append(f"Base Model: {details.get('base_model', 'FacebookAI/roberta-base')}")
        lines.append(f"Adapter: {details.get('adapter', 'ssheroz/spam-email-classifier-roberta-r8')}")
        lines.append(f"Device: {classifier.device_name}")
    elif provider in ("linear_svc", "mlops"):
        lines.append(f"Model: Scikit-Learn LinearSVC Pipeline")
        lines.append(f"Artifact: {details.get('model_path', settings.MODELS_DIR)}")

    lines.append("==================================================")
    banner_text = "\n".join(lines)
    logger.info("\n" + banner_text)


def create_classifier(model_type: Optional[str] = None) -> BaseClassifier:
    """
    Factory function that creates and returns the requested spam classifier instance.
    Selected via EMAIL_CLASSIFIER_MODEL or CLASSIFICATION_MODEL environment variable (default: 'linear_svc').
    """
    if model_type is None:
        model_type = (
            getattr(settings, "EMAIL_CLASSIFIER_MODEL", None)
            or getattr(settings, "CLASSIFICATION_MODEL", None)
            or os.getenv("EMAIL_CLASSIFIER_MODEL")
            or os.getenv("CLASSIFICATION_MODEL", "linear_svc")
        )

    canonical_key = normalize_model_key(model_type)

    if canonical_key in ("linear_svc", "mlops"):
        classifier = MlopsClassifier()
        print_startup_banner(classifier)
        return classifier

    if canonical_key == "otis":
        from app.services.classifiers.otis_classifier import OtisClassifier

        classifier = OtisClassifier()
        print_startup_banner(classifier)
        return classifier

    if canonical_key == "roberta":
        from app.services.classifiers.roberta_classifier import RobertaClassifier

        classifier = RobertaClassifier()
        print_startup_banner(classifier)
        return classifier

    if canonical_key == "deberta-v3-base":
        from app.services.classifiers.deberta_classifier import DebertaClassifier

        classifier = DebertaClassifier()
        print_startup_banner(classifier)
        return classifier

    supported = ", ".join(list_supported_models())
    err_msg = (
        f"Unsupported EMAIL_CLASSIFIER_MODEL: {model_type}. "
        f"Supported models: {supported}"
    )
    logger.error(err_msg)
    raise ValueError(err_msg)

