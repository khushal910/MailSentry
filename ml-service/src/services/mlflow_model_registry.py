"""
Centralized MLflow Model Registry Service.

Manages central model registration, versioning, alias promotion (@champion, @production, @staging),
zero-downtime rollback, and lightweight reference synchronization with MongoDB.
"""

from __future__ import annotations

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import mlflow
from mlflow.tracking import MlflowClient

from src.constants import (
    MLFLOW_MODEL_NAME,
    MLFLOW_MODEL_ALIAS,
    MODEL_METADATA_COLLECTION_NAME,
    DATABASE_NAME_REAL_USER,
    MONGODB_URI_REAL_USER,
    MONGODB_URL_KEY,
)
from src.logger import logger
from src.exception import MyException


def get_git_commit_sha() -> str:
    """Helper to extract current Git commit SHA."""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        return sha
    except Exception:
        return "git_sha_unavailable"


def get_dvc_dataset_hash(dvc_lock_path: Optional[str] = None) -> str:
    """Helper to extract current DVC dataset hash from dvc.lock if present."""
    try:
        path = dvc_lock_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dvc.lock"))
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # Parse MD5 hash under data_ingestion section
                for line in content.splitlines():
                    if "md5:" in line:
                        return line.split("md5:")[1].strip()
        return "dvc_hash_default"
    except Exception:
        return "dvc_hash_unavailable"


class MLflowModelRegistryService:
    """
    Service to register, promote, resolve, and roll back models in MLflow Model Registry.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or MLFLOW_MODEL_NAME
        self.client = MlflowClient()

    def register_and_promote_model(
        self,
        run_id: str,
        artifact_path: str = "model_bundle",
        alias: str = MLFLOW_MODEL_ALIAS,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Registers a model run to MLflow Model Registry and sets the target alias (@champion).
        """
        try:
            model_uri = f"runs:/{run_id}/{artifact_path}"
            logger.info("Registering model URI '%s' under model name '%s'...", model_uri, self.model_name)

            # Create or register model version
            reg_version = mlflow.register_model(model_uri=model_uri, name=self.model_name)
            version_str = str(reg_version.version)

            logger.info("Registered new MLflow model version '%s' for model '%s'", version_str, self.model_name)

            # Set alias (e.g. champion / production)
            if alias:
                clean_alias = alias.lstrip("@")
                self.client.set_registered_model_alias(name=self.model_name, alias=clean_alias, version=version_str)
                logger.info("Assigned alias '@%s' to model version '%s'", clean_alias, version_str)

            # Prepare full metadata summary
            now_iso = datetime.now(timezone.utc).isoformat()
            metadata_dict = {
                "model_name": self.model_name,
                "model_version": version_str,
                "mlflow_run_id": run_id,
                "mlflow_model_uri": f"models:/{self.model_name}/{version_str}",
                "alias_uri": f"models:/{self.model_name}@{alias.lstrip('@')}" if alias else "",
                "stage": alias.lstrip("@") if alias else "registered",
                "dataset_version": get_dvc_dataset_hash(),
                "git_commit": get_git_commit_sha(),
                "registered_at": now_iso,
            }
            if extra_metadata:
                metadata_dict.update(extra_metadata)

            # Sync reference document to MongoDB
            self.sync_mongodb_metadata(metadata_dict)

            return metadata_dict

        except Exception as e:
            logger.error("Failed to register and promote model in MLflow: %s", e)
            raise MyException(e, sys) from e

    def set_model_alias(self, version: str, alias: str) -> Dict[str, Any]:
        """
        Assigns or moves an alias (e.g. 'champion', 'staging') to a specific version.
        """
        try:
            clean_alias = alias.lstrip("@")
            clean_version = str(version).lstrip("v")

            self.client.set_registered_model_alias(name=self.model_name, alias=clean_alias, version=clean_version)
            logger.info("Successfully set alias '@%s' -> version '%s' on model '%s'", clean_alias, clean_version, self.model_name)

            metadata_dict = {
                "model_name": self.model_name,
                "model_version": clean_version,
                "mlflow_model_uri": f"models:/{self.model_name}/{clean_version}",
                "alias_uri": f"models:/{self.model_name}@{clean_alias}",
                "stage": clean_alias,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self.sync_mongodb_metadata(metadata_dict)
            return metadata_dict

        except Exception as e:
            logger.error("Failed to set model alias in MLflow: %s", e)
            raise MyException(e, sys) from e

    def resolve_alias(self, alias: str) -> str:
        """
        Resolves an alias (e.g. 'champion') to an exact version string (e.g. '18').
        """
        try:
            clean_alias = alias.lstrip("@")
            mv = self.client.get_model_version_by_alias(name=self.model_name, alias=clean_alias)
            return str(mv.version)
        except Exception as e:
            raise ValueError(f"Model alias '@{alias}' for '{self.model_name}' not found in MLflow: {e}")

    def rollback_alias(self, target_version: str, alias: str = MLFLOW_MODEL_ALIAS) -> Dict[str, Any]:
        """
        Performs zero-downtime rollback by switching the production alias back to target_version.
        """
        logger.info("Initiating rollback for model '%s': moving alias '@%s' to version '%s'", self.model_name, alias, target_version)
        return self.set_model_alias(version=target_version, alias=alias)

    def list_model_versions(self) -> List[Dict[str, Any]]:
        """
        Lists all registered versions and active aliases for this model.
        """
        try:
            versions_list = []
            registered_model = self.client.get_registered_model(self.model_name)
            aliases = registered_model.aliases if hasattr(registered_model, "aliases") else {}

            # Invert alias mapping: version -> list of aliases
            version_aliases: Dict[str, List[str]] = {}
            for al_name, al_ver in aliases.items():
                version_aliases.setdefault(str(al_ver), []).append(al_name)

            for mv in self.client.search_model_versions(f"name='{self.model_name}'"):
                ver_str = str(mv.version)
                versions_list.append({
                    "version": ver_str,
                    "run_id": mv.run_id,
                    "current_stage": mv.current_stage,
                    "aliases": version_aliases.get(ver_str, []),
                    "created_at": datetime.fromtimestamp(mv.creation_timestamp / 1000.0, tz=timezone.utc).isoformat(),
                    "source": mv.source,
                })

            versions_list.sort(key=lambda x: int(x["version"]) if x["version"].isdigit() else x["version"], reverse=True)
            return versions_list
        except Exception as e:
            logger.warning("Could not list model versions from MLflow: %s", e)
            return []

    def sync_mongodb_metadata(self, metadata_dict: Dict[str, Any]) -> None:
        """
        Writes lightweight model metadata reference document to MongoDB model_metadata collection.
        Does NOT store heavy binary blobs.
        """
        try:
            import pymongo

            mongo_uri = MONGODB_URI_REAL_USER or MONGODB_URL_KEY
            if not mongo_uri:
                logger.info("MongoDB URI not set. Skipping MongoDB metadata reference sync.")
                return

            db_name = DATABASE_NAME_REAL_USER or "mailsentry"
            client = pymongo.MongoClient(mongo_uri)
            try:
                db = client[db_name]
                collection = db[MODEL_METADATA_COLLECTION_NAME]

                doc_id = f"model_ref_{metadata_dict.get('model_name', self.model_name)}"
                metadata_dict["_id"] = doc_id
                metadata_dict["last_updated_at"] = datetime.now(timezone.utc).isoformat()

                collection.replace_one({"_id": doc_id}, metadata_dict, upsert=True)
                logger.info("Successfully synced model reference metadata to MongoDB collection '%s'", MODEL_METADATA_COLLECTION_NAME)
            finally:
                client.close()

        except Exception as err:
            logger.warning("Could not sync model metadata reference to MongoDB: %s", err)
