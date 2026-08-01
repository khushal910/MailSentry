import os
import glob
import pickle
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status

import joblib
from app.core.config import settings
from app.repositories.model_repository import ModelRepository
from app.services.ml_preprocessing import MLPreprocessing

logger = logging.getLogger(__name__)


class MLModelService:
    """
    Service layer for saving, validating, versioning, cleaning up, loading ML classification models,
    and running standalone preprocessing and predictions in backend.
    """

    _cached_model: Optional[Any] = None
    _cached_preprocessor: Optional[Any] = None
    _cached_label_encoder: Optional[Any] = None
    _cached_version: Optional[str] = None

    def __init__(self, models_dir: Optional[str] = None, repo: Optional[ModelRepository] = None):
        self.models_dir = (
            models_dir
            if models_dir is not None
            else getattr(settings, "MODELS_DIR", os.path.join(os.getcwd(), "models"))
        )
        os.makedirs(self.models_dir, exist_ok=True)
        self.repo = repo if repo is not None else ModelRepository()

    def generate_version_string(self) -> str:
        """Generates a timestamp-based version string e.g., v20260801_103527."""
        now = datetime.now(timezone.utc)
        return f"v{now.strftime('%Y%m%d_%H%M%S')}"

    def cleanup_old_models(self, model_name: str = "spam_classifier", keep_count: int = 3) -> List[str]:
        """
        Cleans up old versioned model files from disk, retaining only the latest `keep_count` versions.
        Does NOT delete latest_model.pkl.
        """
        pattern = os.path.join(self.models_dir, f"{model_name}_v*.pkl")
        files = glob.glob(pattern)

        # Sort files by modification time descending (newest first)
        files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

        deleted_files = []
        if len(files) > keep_count:
            files_to_delete = files[keep_count:]
            for fpath in files_to_delete:
                try:
                    os.remove(fpath)
                    deleted_files.append(fpath)
                    logger.info(f"Cleaned up old model file: {fpath}")
                except Exception as e:
                    logger.error(f"Failed to delete old model file '{fpath}': {str(e)}")

        return deleted_files

    def verify_model_integrity(self, file_path: str) -> Any:
        """
        Test mode validation: Loads the serialized model file from disk to ensure it is not corrupted.
        """
        if not os.path.exists(file_path):
            raise ValueError(f"Model file '{file_path}' does not exist.")
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"Model file '{file_path}' is empty.")

        try:
            with open(file_path, "rb") as f:
                model_obj = pickle.load(f)
            if model_obj is None:
                raise ValueError("Deserialized model object is None.")
            return model_obj
        except Exception as e:
            raise ValueError(f"Model file integrity check failed for '{file_path}': {str(e)}")

    def save_and_register_model(
        self,
        model_obj: Any,
        model_name: str = "spam_classifier",
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Saves a trained ML model:
        1. Serializes model to versioned file (e.g. spam_classifier_v20260801_103527.pkl).
        2. Copies/saves to latest_model.pkl.
        3. Runs test mode validation to verify the saved file is not corrupted.
        4. Updates database record in models collection.
        5. Cleans up old model files, keeping the latest 3 versions.
        """
        if model_obj is None:
            raise ValueError("Cannot save None model object.")

        version = self.generate_version_string()
        versioned_filename = f"{model_name}_{version}.pkl"
        versioned_filepath = os.path.join(self.models_dir, versioned_filename)
        latest_filepath = os.path.join(self.models_dir, "latest_model.pkl")

        # 1. Serialize model to versioned file and latest pointer
        with open(versioned_filepath, "wb") as f:
            pickle.dump(model_obj, f)
        with open(latest_filepath, "wb") as f:
            pickle.dump(model_obj, f)

        # 2. Validation: Test mode load check to ensure file is not corrupted
        self.verify_model_integrity(versioned_filepath)
        self.verify_model_integrity(latest_filepath)

        # 3. Database tracking: record model in MongoDB
        record = self.repo.record_model(
            model_name=model_name,
            version=version,
            file_path=versioned_filepath,
            metrics=metrics
        )

        # 4. Disk cleanup: retain latest 3 versions
        self.cleanup_old_models(model_name=model_name, keep_count=3)

        # 5. Update cached model in memory
        MLModelService._cached_model = model_obj
        MLModelService._cached_version = version

        logger.info(f"Model successfully saved, verified, registered, and cached. Version: {version}")
        return record

    def load_latest_model(self, force_reload: bool = False) -> Optional[Any]:
        """
        Loads the latest model file from disk.
        Returns None if model file is missing or corrupted.
        """
        if not force_reload and MLModelService._cached_model is not None:
            return MLModelService._cached_model

        latest_filepath = os.path.join(self.models_dir, "latest_model.pkl")

        # Find latest model file if latest_model.pkl is missing
        target_path = latest_filepath
        if not os.path.exists(target_path):
            pattern = os.path.join(self.models_dir, "*.pkl")
            all_files = glob.glob(pattern)
            # Exclude auxiliary artifact files (preprocessing.pkl and label_encoder.pkl)
            files = [
                f for f in all_files
                if not os.path.basename(f).startswith("preprocessing")
                and not os.path.basename(f).startswith("label_encoder")
            ]
            if not files:
                logger.warning(f"No model files found in '{self.models_dir}'.")
                return None
            files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
            target_path = files[0]

        try:
            model_obj = self.verify_model_integrity(target_path)
            MLModelService._cached_model = model_obj
            logger.info(f"Successfully loaded latest model from '{target_path}'.")
            return model_obj
        except Exception as e:
            logger.error(f"Error loading model from '{target_path}': {str(e)}")
            MLModelService._cached_model = None
            return None

    def get_model_or_raise(self) -> Any:
        """
        Returns the active model.
        Raises HTTP 500 error if model file is missing or unavailable.
        """
        model = self.load_latest_model()
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ML classification model is not available"
            )
        return model

    def load_preprocessor(self) -> Optional[Any]:
        """Loads preprocessor (preprocessing.pkl) from models_dir if present."""
        if MLModelService._cached_preprocessor is not None:
            return MLModelService._cached_preprocessor

        preprocessor_path = os.path.join(self.models_dir, "preprocessing.pkl")
        if os.path.exists(preprocessor_path):
            try:
                obj = joblib.load(preprocessor_path)
                MLModelService._cached_preprocessor = obj
                logger.info(f"Loaded preprocessor from '{preprocessor_path}'.")
                return obj
            except Exception as e:
                logger.warning(f"Failed to load preprocessor: {e}")
        return None

    def load_label_encoder(self) -> Optional[Any]:
        """Loads label encoder (label_encoder.pkl) from models_dir if present."""
        if MLModelService._cached_label_encoder is not None:
            return MLModelService._cached_label_encoder

        encoder_path = os.path.join(self.models_dir, "label_encoder.pkl")
        if os.path.exists(encoder_path):
            try:
                obj = joblib.load(encoder_path)
                MLModelService._cached_label_encoder = obj
                logger.info(f"Loaded label encoder from '{encoder_path}'.")
                return obj
            except Exception as e:
                logger.warning(f"Failed to load label encoder: {e}")
        return None

    def classify_text(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Classifies email content using backend's standalone preprocessing and ML model.
        Returns predicted_label, predicted_score, subject, and classified_at timestamp.
        """
        model = self.get_model_or_raise()

        subject_str = (subject or "").strip()
        body_str = (body or "").strip()

        # Step 1: Preprocess text using backend's standalone MLPreprocessing pipeline
        cleaned_text = MLPreprocessing.preprocess_email_text(subject_str, body_str)

        preprocessor = self.load_preprocessor()
        label_encoder = self.load_label_encoder()

        predicted_label = "inbox"
        predicted_score = 0.85

        try:
            # Step 2: Vectorize feature string if standalone preprocessor is present
            if preprocessor is not None and hasattr(preprocessor, "transform"):
                X_features = preprocessor.transform([cleaned_text])
            else:
                # Scikit-Learn Pipeline or raw text
                X_features = [cleaned_text]

            # Step 3: Run model prediction
            if hasattr(model, "predict"):
                res = model.predict(X_features)
                if res is not None and len(res) > 0:
                    raw_val = res[0]
                    # Step 4: Decode label using label_encoder if available
                    if label_encoder is not None and hasattr(label_encoder, "inverse_transform"):
                        try:
                            decoded = label_encoder.inverse_transform([raw_val])
                            predicted_label = str(decoded[0])
                        except Exception:
                            predicted_label = "spam" if str(raw_val) in ("1", "1.0", "Spam", "spam") else "inbox"
                    elif isinstance(raw_val, (int, float)):
                        predicted_label = "spam" if int(raw_val) == 1 else "inbox"
                    else:
                        predicted_label = str(raw_val)

            # Step 5: Run probability / confidence calculation
            import numpy as np
            if hasattr(model, "predict_proba"):
                try:
                    proba = model.predict_proba(X_features)
                    if proba is not None and len(proba) > 0:
                        predicted_score = round(float(np.max(proba[0])), 4)
                except Exception:
                    pass
            elif hasattr(model, "decision_function"):
                try:
                    dec = model.decision_function(X_features)
                    if dec is not None and len(dec) > 0:
                        val = float(dec[0])
                        # Sigmoid transformation converting margin distance into confidence score
                        prob = 1.0 / (1.0 + np.exp(-abs(val)))
                        predicted_score = round(float(prob), 4)
                except Exception:
                    pass

        except Exception as err:
            logger.warning(f"Model prediction fallback engaged due to: {err}")
            # Fallback heuristic if estimator or preprocessor encounters mismatch
            combined_text = f"{subject_str} {body_str}".lower()
            spam_keywords = ["spam", "winner", "lottery", "claim", "prize", "free money", "urgent security"]
            if any(k in combined_text for k in spam_keywords):
                predicted_label = "spam"
                predicted_score = 0.95

        return {
            "subject": subject_str[:255],
            "predicted_label": predicted_label,
            "predicted_score": predicted_score,
            "classified_at": datetime.now(timezone.utc).isoformat()
        }


