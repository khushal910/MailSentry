"""
Checkpoint manager for model artifact serialization, deserialization, validation, and versioning.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.entity.config_entity import _ModelEvaluation
from src.entity.model_metadata import ModelMetadata
from src.exception import MyException
from src.logger import logger
from src.services.model_saver import ModelLoaderFactory, ModelSaverFactory
from src.services.storage_service import LocalStorageService
from src.utils.main_utils import read_yaml_file, write_yaml_file


def compute_sha256(file_path: str | Path) -> str:
    """
    Compute SHA-256 checksum of a file in binary chunks.

    Parameters
    ----------
    file_path : str | Path
        Path to file.

    Returns
    -------
    str
        SHA-256 hex digest or empty string if file does not exist.
    """
    try:
        path = Path(file_path)
        if not path.is_file():
            return ""

        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as exc:
        logger.warning("Error computing SHA-256 for %s: %s", file_path, exc)
        return ""


class CheckpointManager:
    """
    Dedicated manager for model checkpoint creation, validation, loading, deletion, and atomic replacement.

    Responsibilities:
    - Compute SHA-256 file checksums & comprehensive per-model config_hash
    - Save model checkpoints into temporary staging directories (_tmp)
    - Verify temporary checkpoint integrity before replacing active checkpoints
    - Atomically promote temporary checkpoints to active checkpoints
    - Load model checkpoints into _ModelEvaluation objects
    - Delete stale or corrupted checkpoints
    - Fail-fast checkpoint validation
    """

    CURRENT_CHECKPOINT_VERSION: str = "1.0.0"

    def __init__(self, checkpoints_dir: str | Path, default_metric: str = "f1") -> None:
        """
        Initialize CheckpointManager.

        Parameters
        ----------
        checkpoints_dir : str | Path
            Directory where per-model checkpoints are stored.
        default_metric : str
            Default evaluation metric (e.g. 'f1').
        """
        try:
            self.checkpoints_dir = Path(checkpoints_dir)
            self.default_metric = default_metric
            self.storage = LocalStorageService()
            os.makedirs(self.checkpoints_dir, exist_ok=True)
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def compute_file_checksum(self, file_path: str | Path) -> str:
        """
        Compute SHA-256 checksum of a file.
        """
        return compute_sha256(file_path)

    def compute_config_hash(
        self,
        model_name: str,
        train_file_hash: str,
        test_file_hash: str,
        prep_file_hashes: Dict[str, str],
        params: Dict[str, Any],
        search_space: Dict[str, Any],
        tuner_config: Dict[str, Any],
        framework: str = "sklearn",
        serialization: str = "joblib",
        metric: Optional[str] = None,
    ) -> str:
        """
        Compute a comprehensive SHA-256 config_hash for a specific model.

        Includes all factors that alter training results (model weights):
        - model_name
        - train dataset SHA-256
        - test dataset SHA-256
        - preprocessor SHA-256 hashes
        - model hyperparameter config
        - hyperparameter search space
        - tuner config (n_iter, cv, random_state)
        - framework name
        - serialization type

        Note: Evaluation selection metric is intentionally excluded so changing
        selection metrics (e.g. Accuracy -> F1) does NOT invalidate trained checkpoints.
        """
        try:
            # Clean tuner_config to remove metric/scoring if present
            clean_tuner_config = {
                k: v for k, v in (tuner_config or {}).items()
                if k not in ("scoring", "metric")
            }

            hash_payload = {
                "model_name": str(model_name),
                "train_dataset_hash": str(train_file_hash),
                "test_dataset_hash": str(test_file_hash),
                "preprocessor_hashes": prep_file_hashes or {},
                "params": params or {},
                "search_space": search_space or {},
                "tuner_config": clean_tuner_config,
                "framework": str(framework),
                "serialization": str(serialization),
                "checkpoint_version": self.CURRENT_CHECKPOINT_VERSION,
            }
            payload_str = json.dumps(hash_payload, sort_keys=True, default=str)
            return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def get_checkpoint_dir(self, model_name: str) -> Path:
        """
        Get absolute path to a model's active checkpoint directory.
        """
        return self.checkpoints_dir / model_name

    def get_temp_checkpoint_dir(self, model_name: str) -> Path:
        """
        Get absolute path to a model's temporary staging checkpoint directory.
        """
        return self.checkpoints_dir / f"{model_name}_tmp"

    def checkpoint_exists(self, model_name: str) -> bool:
        """
        Check if active checkpoint directory for a model exists.
        """
        chk_dir = self.get_checkpoint_dir(model_name)
        return chk_dir.is_dir()

    def verify_checkpoint(
        self,
        checkpoint_dir: str | Path,
        expected_config_hash: str,
    ) -> bool:
        """
        Verify file presence, readability, checkpoint_version, and config_hash for any checkpoint directory.

        Parameters
        ----------
        checkpoint_dir : str | Path
            Directory path of checkpoint to verify (e.g. temporary or active).
        expected_config_hash : str
            Expected SHA-256 config_hash.

        Returns
        -------
        bool
            True if verification succeeds fast; False otherwise.
        """
        try:
            chk_dir = Path(checkpoint_dir)
            if not chk_dir.is_dir():
                logger.info("Verification failed: Directory '%s' does not exist.", chk_dir)
                return False

            meta_path = chk_dir / "metadata.json"
            if not meta_path.is_file():
                logger.info("Verification failed: metadata.json missing in '%s'.", chk_dir)
                return False

            try:
                meta_dict = self.storage.read_json(str(meta_path))
            except Exception as e:
                logger.warning("Verification failed: Unreadable metadata.json in '%s' (%s).", chk_dir, e)
                return False

            meta_version = meta_dict.get("checkpoint_version")
            if meta_version != self.CURRENT_CHECKPOINT_VERSION:
                logger.info(
                    "Verification failed: Version mismatch (stored: %s, required: %s) in '%s'.",
                    meta_version,
                    self.CURRENT_CHECKPOINT_VERSION,
                    chk_dir,
                )
                return False

            stored_hash = meta_dict.get("config_hash")
            if stored_hash != expected_config_hash:
                logger.info("Verification failed: config_hash mismatch in '%s'.", chk_dir)
                return False

            metrics_path = chk_dir / "metrics.yaml"
            if not metrics_path.is_file():
                logger.info("Verification failed: metrics.yaml missing in '%s'.", chk_dir)
                return False

            try:
                metrics_data = read_yaml_file(metrics_path)
                if not isinstance(metrics_data, dict) or not metrics_data:
                    logger.info("Verification failed: metrics.yaml is empty or invalid in '%s'.", chk_dir)
                    return False
            except Exception as e:
                logger.warning("Verification failed: Unreadable metrics.yaml in '%s' (%s).", chk_dir, e)
                return False

            params_path = chk_dir / "params.yaml"
            if not params_path.is_file():
                logger.info("Verification failed: params.yaml missing in '%s'.", chk_dir)
                return False

            serialization = meta_dict.get("serialization", "joblib")
            model_dir = chk_dir / "model"
            if not model_dir.is_dir():
                logger.info("Verification failed: model directory missing in '%s'.", chk_dir)
                return False

            if serialization == "joblib":
                model_file = model_dir / "model.joblib"
                if not model_file.is_file() or model_file.stat().st_size == 0:
                    logger.info("Verification failed: model.joblib missing or 0 bytes in '%s'.", chk_dir)
                    return False
            elif serialization == "huggingface":
                config_file = model_dir / "config.json"
                if not config_file.is_file():
                    logger.info("Verification failed: transformer config.json missing in '%s'.", chk_dir)
                    return False
                weights_exist = any(
                    (model_dir / name).is_file() and (model_dir / name).stat().st_size > 0
                    for name in ["model.safetensors", "pytorch_model.bin"]
                )
                if not weights_exist:
                    logger.info("Verification failed: transformer model weights missing or 0 bytes in '%s'.", chk_dir)
                    return False

            logger.info("Checkpoint verification succeeded for '%s'.", chk_dir)
            return True

        except Exception as exc:
            logger.warning("Verification encountered error for '%s': %s", checkpoint_dir, exc)
            return False

    def validate_checkpoint(
        self,
        model_name: str,
        current_config_hash: str,
    ) -> bool:
        """
        Validate active checkpoint directory <model_name>.
        """
        chk_dir = self.get_checkpoint_dir(model_name)
        return self.verify_checkpoint(chk_dir, current_config_hash)

    def save_temporary_checkpoint(
        self,
        model_eval: _ModelEvaluation,
        config_hash: str,
    ) -> str:
        """
        Save model checkpoint artifacts into temporary staging directory <model_name>_tmp.

        The existing active checkpoint <model_name> remains untouched.
        """
        try:
            tmp_chk_dir = self.get_temp_checkpoint_dir(model_eval.name)
            if tmp_chk_dir.is_dir():
                shutil.rmtree(tmp_chk_dir)
            os.makedirs(tmp_chk_dir, exist_ok=True)

            is_transformer = (
                model_eval.name.lower().startswith("distilbert")
                or hasattr(model_eval.model, "save_pretrained")
            )

            framework = "transformers" if is_transformer else "sklearn"
            serialization = "huggingface" if is_transformer else "joblib"
            input_type = "raw_text" if is_transformer else "tfidf"
            preprocessor_name = "distilbert-tokenizer" if is_transformer else "tfidf"

            metadata = ModelMetadata(
                model_name=model_eval.name,
                framework=framework,
                serialization=serialization,
                task="binary_classification",
                input_type=input_type,
                output_type="probability",
                preprocessor=preprocessor_name,
                metric=self.default_metric,
                score=float(model_eval.metrics.get(self.default_metric, 0.0)),
                metrics=model_eval.metrics,
                trained_at=datetime.now(timezone.utc).isoformat(),
            )

            meta_dict = metadata.to_dict()
            meta_dict["config_hash"] = config_hash
            meta_dict["checkpoint_version"] = self.CURRENT_CHECKPOINT_VERSION

            saver = ModelSaverFactory.create(metadata)
            saver.save(model=model_eval.model, target_dir=str(tmp_chk_dir), metadata=metadata)

            write_yaml_file(str(tmp_chk_dir / "metrics.yaml"), model_eval.metrics)
            write_yaml_file(str(tmp_chk_dir / "params.yaml"), model_eval.params or {})
            self.storage.write_json(str(tmp_chk_dir / "metadata.json"), meta_dict)

            logger.info(
                "Saved temporary staging checkpoint for model '%s' at: %s",
                model_eval.name,
                tmp_chk_dir,
            )
            return str(tmp_chk_dir)
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def promote_checkpoint(self, model_name: str) -> str:
        """
        Atomically promote temporary staging checkpoint <model_name>_tmp -> active <model_name>.

        Steps:
        1. Verify <model_name>_tmp exists.
        2. Delete existing <model_name> directory with Windows lock handling.
        3. Rename or move <model_name>_tmp -> <model_name>.
        4. Return promoted path.
        """
        try:
            tmp_chk_dir = self.get_temp_checkpoint_dir(model_name)
            final_chk_dir = self.get_checkpoint_dir(model_name)

            if not tmp_chk_dir.is_dir():
                raise FileNotFoundError(f"Temporary staging checkpoint missing: {tmp_chk_dir}")

            if final_chk_dir.is_dir():
                def remove_readonly(func: Any, path: Any, exc_info: Any) -> None:
                    try:
                        os.chmod(path, 0o777)
                        func(path)
                    except Exception:
                        pass

                shutil.rmtree(final_chk_dir, onerror=remove_readonly)
                for _ in range(5):
                    if not final_chk_dir.exists():
                        break
                    time.sleep(0.1)

            try:
                os.rename(tmp_chk_dir, final_chk_dir)
            except OSError:
                shutil.move(str(tmp_chk_dir), str(final_chk_dir))

            logger.info(
                "Atomically promoted checkpoint '%s_tmp' -> '%s'.",
                model_name,
                model_name,
            )
            return str(final_chk_dir)
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def cleanup_temporary_checkpoint(self, model_name: str) -> None:
        """
        Safely delete temporary staging checkpoint <model_name>_tmp if present.
        """
        try:
            tmp_chk_dir = self.get_temp_checkpoint_dir(model_name)
            if tmp_chk_dir.is_dir():
                shutil.rmtree(tmp_chk_dir)
                logger.info("Cleaned up temporary staging checkpoint for '%s': %s", model_name, tmp_chk_dir)
        except Exception as exc:
            logger.warning("Failed to clean up temporary checkpoint for '%s': %s", model_name, exc)

    def save_checkpoint(
        self,
        model_eval: _ModelEvaluation,
        config_hash: str,
    ) -> str:
        """
        Save model checkpoint directly to active directory <model_name>.
        """
        try:
            chk_dir = self.get_checkpoint_dir(model_eval.name)
            os.makedirs(chk_dir, exist_ok=True)

            is_transformer = (
                model_eval.name.lower().startswith("distilbert")
                or hasattr(model_eval.model, "save_pretrained")
            )

            framework = "transformers" if is_transformer else "sklearn"
            serialization = "huggingface" if is_transformer else "joblib"
            input_type = "raw_text" if is_transformer else "tfidf"
            preprocessor_name = "distilbert-tokenizer" if is_transformer else "tfidf"

            metadata = ModelMetadata(
                model_name=model_eval.name,
                framework=framework,
                serialization=serialization,
                task="binary_classification",
                input_type=input_type,
                output_type="probability",
                preprocessor=preprocessor_name,
                metric=self.default_metric,
                score=float(model_eval.metrics.get(self.default_metric, 0.0)),
                metrics=model_eval.metrics,
                trained_at=datetime.now(timezone.utc).isoformat(),
            )

            meta_dict = metadata.to_dict()
            meta_dict["config_hash"] = config_hash
            meta_dict["checkpoint_version"] = self.CURRENT_CHECKPOINT_VERSION

            saver = ModelSaverFactory.create(metadata)
            saver.save(model=model_eval.model, target_dir=str(chk_dir), metadata=metadata)

            write_yaml_file(str(chk_dir / "metrics.yaml"), model_eval.metrics)
            write_yaml_file(str(chk_dir / "params.yaml"), model_eval.params or {})
            self.storage.write_json(str(chk_dir / "metadata.json"), meta_dict)

            logger.info("Saved checkpoint for model '%s' at: %s", model_eval.name, chk_dir)
            return str(chk_dir)

        except Exception as exc:
            raise MyException(exc, sys) from exc

    def load_checkpoint(self, model_name: str) -> _ModelEvaluation:
        """
        Load model checkpoint and return a reconstructed _ModelEvaluation object.
        """
        try:
            chk_dir = self.get_checkpoint_dir(model_name)
            if not chk_dir.is_dir():
                raise FileNotFoundError(f"Checkpoint directory missing for '{model_name}': {chk_dir}")

            metrics_path = chk_dir / "metrics.yaml"
            if not metrics_path.is_file():
                raise FileNotFoundError(f"Checkpoint metrics.yaml missing at: {metrics_path}")
            metrics = read_yaml_file(metrics_path)

            params_path = chk_dir / "params.yaml"
            params = read_yaml_file(params_path) if params_path.is_file() else {}

            meta_path = chk_dir / "metadata.json"
            if meta_path.is_file():
                meta_dict = self.storage.read_json(str(meta_path))
                metadata = ModelMetadata.from_dict(meta_dict)
            else:
                is_transformer = model_name.lower().startswith("distilbert")
                serialization = "huggingface" if is_transformer else "joblib"
                framework = "transformers" if is_transformer else "sklearn"
                metadata = ModelMetadata(
                    model_name=model_name,
                    framework=framework,
                    serialization=serialization,
                    task="binary_classification",
                    input_type="raw_text" if is_transformer else "tfidf",
                    output_type="probability",
                    preprocessor="distilbert-tokenizer" if is_transformer else "tfidf",
                    metric=self.default_metric,
                    score=float(metrics.get(self.default_metric, 0.0)),
                    metrics=metrics,
                    trained_at=datetime.now(timezone.utc).isoformat(),
                )

            loader = ModelLoaderFactory.create(metadata)
            loaded_model = loader.load(str(chk_dir), metadata)

            logger.info("Loaded checkpoint for model '%s'.", model_name)
            return _ModelEvaluation(
                name=model_name,
                model=loaded_model,
                params=params,
                metrics=metrics,
            )
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def delete_checkpoint(self, model_name: str) -> None:
        """
        Safely delete checkpoint directory for a model.
        """
        try:
            chk_dir = self.get_checkpoint_dir(model_name)
            if chk_dir.is_dir():
                shutil.rmtree(chk_dir)
                logger.info("Deleted checkpoint directory for '%s': %s", model_name, chk_dir)
        except Exception as exc:
            logger.warning("Failed to delete checkpoint directory for '%s': %s", model_name, exc)
