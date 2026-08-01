import os
import glob
import pickle
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.model_repository import ModelRepository

logger = logging.getLogger(__name__)


class MLModelService:
    """
    Service layer for saving, validating, versioning, cleaning up, and loading ML classification models.
    """

    _cached_model: Optional[Any] = None
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
            files = glob.glob(pattern)
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
