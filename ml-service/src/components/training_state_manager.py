"""
Training state manager for tracking per-model execution status and checkpointing metadata.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.exception import MyException
from src.logger import logger
from src.utils.main_utils import read_yaml_file, write_yaml_file


class TrainingStateManager:
    """
    Manages training state and checkpointing metadata in training_state.yaml.

    Responsibilities:
    - create training_state.yaml if missing
    - load YAML state
    - update model status, timestamps, and config_hash
    - save YAML safely
    - mark completed, failed, or pending
    - query model status and stored config_hash
    - reset state
    """

    TRAINING_VERSION: str = "1.0.0"

    def __init__(self, path: str | Path) -> None:
        """
        Initialize TrainingStateManager with file path.

        Parameters
        ----------
        path : str | Path
            Path to training_state.yaml.
        """
        try:
            self.path = Path(path)
            self.state: Dict[str, Any] = self.load()
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def load(self) -> Dict[str, Any]:
        """
        Load training state from YAML file if it exists, otherwise initialize new state.

        Returns
        -------
        Dict[str, Any]
            The loaded or initialized training state dictionary.
        """
        try:
            if self.path.exists():
                logger.info("Loading previous training session state from %s", self.path)
                content = read_yaml_file(self.path)
                if isinstance(content, dict) and "models" in content:
                    return content

            logger.info("Initializing new training state at %s", self.path)
            now_iso = datetime.now(timezone.utc).isoformat()
            initial_state: Dict[str, Any] = {
                "training_started_at": now_iso,
                "last_updated_at": now_iso,
                "training_version": self.TRAINING_VERSION,
                "models": {},
            }
            self.save_state(initial_state)
            return initial_state
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def save_state(self, state_dict: Dict[str, Any]) -> None:
        """
        Write state dictionary to training_state.yaml.
        """
        try:
            write_yaml_file(str(self.path), state_dict)
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def save(self) -> None:
        """
        Persist current internal state to disk, updating last_updated_at.
        """
        self.state["last_updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save_state(self.state)

    def update_last_updated(self) -> None:
        """
        Update last_updated_at timestamp and save state.
        """
        self.save()

    def is_completed(self, model_name: str) -> bool:
        """
        Query whether a model has been marked as completed.
        """
        models = self.state.get("models", {})
        if isinstance(models, dict):
            model_info = models.get(model_name, {})
            if isinstance(model_info, dict):
                return model_info.get("status") == "completed"
        return False

    def get_config_hash(self, model_name: str) -> Optional[str]:
        """
        Retrieve stored config_hash for a model from training state.
        """
        models = self.state.get("models", {})
        if isinstance(models, dict):
            info = models.get(model_name, {})
            if isinstance(info, dict):
                return info.get("config_hash")
        return None

    def mark_completed(
        self,
        model_name: str,
        checkpoint: Optional[str] = None,
        config_hash: Optional[str] = None,
    ) -> None:
        """
        Mark a model as completed and record its config_hash and checkpoint path.
        """
        try:
            if "models" not in self.state or not isinstance(self.state["models"], dict):
                self.state["models"] = {}

            self.state["models"][model_name] = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "checkpoint": checkpoint or "",
                "config_hash": config_hash or "",
            }
            self.save()
            logger.info("Marked model '%s' as completed in training state.", model_name)
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def mark_failed(self, model_name: str, reason: str) -> None:
        """
        Mark a model as failed with a specified reason.
        """
        try:
            if "models" not in self.state or not isinstance(self.state["models"], dict):
                self.state["models"] = {}

            self.state["models"][model_name] = {
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "reason": str(reason),
            }
            self.save()
            logger.warning(
                "Marked model '%s' as failed in training state. Reason: %s",
                model_name,
                reason,
            )
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def mark_pending(self, model_name: str) -> None:
        """
        Mark a model status as pending before training or retraining.
        """
        try:
            if "models" not in self.state or not isinstance(self.state["models"], dict):
                self.state["models"] = {}

            self.state["models"][model_name] = {
                "status": "pending",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self.save()
            logger.info("Marked model '%s' as pending in training state.", model_name)
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def get_model_status(self, model_name: str) -> Optional[str]:
        """
        Get current status of a model.
        """
        models = self.state.get("models", {})
        if isinstance(models, dict):
            model_info = models.get(model_name, {})
            if isinstance(model_info, dict):
                return model_info.get("status")
        return None

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get metadata dictionary for a specific model.
        """
        models = self.state.get("models", {})
        if isinstance(models, dict):
            info = models.get(model_name, {})
            if isinstance(info, dict):
                return info
        return {}

    def reset_state(self) -> None:
        """
        Reset training state by clearing all recorded model statuses.
        """
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            self.state = {
                "training_started_at": now_iso,
                "last_updated_at": now_iso,
                "training_version": self.TRAINING_VERSION,
                "models": {},
            }
            self.save_state(self.state)
            logger.info("Reset training state at %s", self.path)
        except Exception as exc:
            raise MyException(exc, sys) from exc
