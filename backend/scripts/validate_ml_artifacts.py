#!/usr/bin/env python3
"""
MailSentry ML Artifact & Pipeline Validator — Stage 8 CI Step

Validates machine learning model artifacts, metadata integrity, preprocessors,
and executes end-to-end inference verification.
"""

import sys
import os
import json
import hashlib
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("ml_validator")

# Ensure backend root is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


def compute_file_sha256(filepath: str) -> str:
    """Computes SHA256 hash of a binary file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    logger.info("Starting MailSentry Production ML Artifact Validation...")
    ml_service_models_dir = os.path.abspath(
        os.path.join(BACKEND_ROOT, "..", "ml-service", "models")
    )
    models_dir = (
        ml_service_models_dir
        if os.path.exists(ml_service_models_dir)
        else os.path.join(BACKEND_ROOT, "models")
    )
    prod_dir = os.path.join(models_dir, "production")

    if not os.path.exists(prod_dir):
        logger.error(f"Production model directory missing at '{prod_dir}'!")
        sys.exit(1)

    # 1. Metadata Validation
    metadata_path = os.path.join(prod_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        logger.error(f"Metadata file missing at '{metadata_path}'!")
        sys.exit(1)

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        logger.info(f"Metadata loaded: model='{metadata.get('model_name')}', version='{metadata.get('version')}', framework='{metadata.get('framework')}'")
    except Exception as e:
        logger.error(f"Failed to parse metadata.json: {e}")
        sys.exit(1)

    required_keys = ["model_name", "version", "framework"]
    for key in required_keys:
        if key not in metadata:
            logger.error(f"Metadata missing required key: '{key}'")
            sys.exit(1)

    # 2. Model File Validation
    model_dir = os.path.join(prod_dir, "model")
    possible_models = ["model.joblib", "model.pkl", "model.bin"]
    found_model_path = None
    if os.path.exists(model_dir):
        for name in possible_models:
            p = os.path.join(model_dir, name)
            if os.path.exists(p):
                found_model_path = p
                break

    if not found_model_path:
        logger.error(f"No model file ({possible_models}) found in '{model_dir}'!")
        sys.exit(1)

    model_hash = compute_file_sha256(found_model_path)
    logger.info(f"Model artifact validated: {os.path.basename(found_model_path)} (SHA256: {model_hash[:16]}...)")

    # 3. Preprocessor Validation
    preprocessor_dir = os.path.join(prod_dir, "preprocessor")
    prep_pkl = os.path.join(preprocessor_dir, "preprocessing.pkl")
    label_encoder_pkl = os.path.join(preprocessor_dir, "label_encoder.pkl")

    if not os.path.exists(prep_pkl):
        logger.warning(f"Vectorization preprocessor missing at '{prep_pkl}'! (Falling back to raw text)")
    else:
        prep_hash = compute_file_sha256(prep_pkl)
        logger.info(f"Preprocessor artifact validated: preprocessing.pkl (SHA256: {prep_hash[:16]}...)")

    if not os.path.exists(label_encoder_pkl):
        logger.warning(f"Label encoder missing at '{label_encoder_pkl}'!")
    else:
        le_hash = compute_file_sha256(label_encoder_pkl)
        logger.info(f"Label encoder validated: label_encoder.pkl (SHA256: {le_hash[:16]}...)")

    # 4. Pipeline & Inference Test Execution
    logger.info("Executing end-to-end inference verification via PredictionEngine...")
    try:
        from app.services.prediction_engine import PredictionEngine
        engine = PredictionEngine(models_dir)

        test_subject = "Urgent: Verify your account security code 8910"
        test_body = "We noticed a login attempt from a new device. Use code 8910 to verify."
        result = engine.predict(subject=test_subject, body=test_body)

        logger.info(f"Inference test passed! Prediction: label='{result.get('predicted_label')}', score={result.get('predicted_score')}")
    except Exception as e:
        logger.error(f"Inference verification failed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("ALL ML Artifact & Pipeline Validations PASSED SUCCESSFULLY! 🚀")
    sys.exit(0)


if __name__ == "__main__":
    main()
