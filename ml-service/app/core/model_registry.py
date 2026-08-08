import os
from typing import Any, Dict, Optional

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "mlops": {
        "key": "mlops",
        "name": "Scikit-Learn MLOps Pipeline",
        "provider": "scikit-learn",
        "base_model": "TF-IDF + Naive Bayes / Random Forest",
        "adapter": None,
        "lora_enabled": False,
        "lora_r": 0,
        "target_modules": [],
        "description": "Scikit-Learn MLOps text classification pipeline utilizing TF-IDF vectorization and tabular artifact serialization.",
        "class_name": "MlopsClassifier",
        "module_path": "app.services.classifiers.mlops_classifier",
        "metrics": {
            "accuracy": 98.45,
            "precision": 98.10,
            "recall": 98.80,
            "f1_score": 98.45,
            "roc_auc": 99.80,
            "model_size_mb": 0.05,
            "inference_time_ms": 1.75,
        },
    },
    "roberta": {
        "key": "roberta",
        "name": "RoBERTa-base",
        "provider": "Hugging Face",
        "base_model": "FacebookAI/roberta-base",
        "adapter": "ssheroz/spam-email-classifier-roberta-r8",
        "lora_enabled": True,
        "lora_r": 8,
        "target_modules": ["query", "value"],
        "description": "Pretrained RoBERTa transformer fine-tuned with LoRA r=8 adapter (ssheroz/spam-email-classifier-roberta-r8) for binary email spam classification.",
        "class_name": "RobertaClassifier",
        "module_path": "app.services.classifiers.roberta_classifier",
        "metrics": {
            "accuracy": 99.12,
            "precision": 98.95,
            "recall": 99.40,
            "f1_score": 99.17,
            "roc_auc": 99.96,
            "model_size_mb": 498.50,
            "inference_time_ms": 12.45,
        },
    },
    "deberta-v3-base": {
        "key": "deberta-v3-base",
        "name": "DeBERTa-v3-base",
        "provider": "Hugging Face",
        "base_model": "microsoft/deberta-v3-base",
        "adapter": os.getenv("DEBERTA_ADAPTER", "ssheroz/spam-email-classifier-deberta-v3-base-r8"),
        "lora_enabled": True,
        "lora_r": 8,
        "target_modules": ["query_proj", "key_proj", "value_proj"],
        "description": "DeBERTa-v3 transformer with disentangled attention, fine-tuned with LoRA r=8 adapter for enterprise email spam classification.",
        "class_name": "DebertaClassifier",
        "module_path": "app.services.classifiers.deberta_classifier",
        "metrics": {
            "accuracy": 99.35,
            "precision": 99.10,
            "recall": 99.60,
            "f1_score": 99.35,
            "roc_auc": 99.98,
            "model_size_mb": 512.00,
            "inference_time_ms": 14.20,
        },
    },
}

# Alias mapping to canonical keys
MODEL_ALIASES: Dict[str, str] = {
    "mlops": "mlops",
    "sklearn": "mlops",
    "roberta": "roberta",
    "roberta-base": "roberta",
    "facebookai/roberta-base": "roberta",
    "deberta": "deberta-v3-base",
    "deberta-v3": "deberta-v3-base",
    "deberta-v3-base": "deberta-v3-base",
    "microsoft/deberta-v3-base": "deberta-v3-base",
}


def normalize_model_key(raw_key: Optional[str]) -> str:
    """
    Resolve raw model string alias to canonical model registry key.
    Defaults to 'mlops' if key is empty or unmapped.
    """
    if not raw_key:
        return "mlops"
    cleaned = str(raw_key).strip().lower()
    return MODEL_ALIASES.get(cleaned, cleaned)


def get_model_config(raw_key: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata configuration dictionary for a given model key or alias.
    """
    canonical_key = normalize_model_key(raw_key)
    return MODEL_REGISTRY.get(canonical_key)


def list_supported_models() -> list[str]:
    """
    Return list of canonical supported model keys.
    """
    return list(MODEL_REGISTRY.keys())
