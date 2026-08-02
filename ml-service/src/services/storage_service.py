"""
Storage abstraction for the Model Registry.

Decouples the registry from filesystem details so the storage backend
can be swapped for S3, GCS, or Azure Blob in the future without
touching registry logic.

Usage
-----
Default (local filesystem)::

    storage = LocalStorageService()

Cloud (future)::

    storage = S3StorageService(bucket="my-models")
    registry = ModelRegistry(root, storage=storage)
"""

from __future__ import annotations

import json
import os
import shutil
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.logger import logger


class BaseStorageService(ABC):
    """Abstract storage interface — all registry I/O goes through this."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a path exists."""

    @abstractmethod
    def makedirs(self, path: str) -> None:
        """Create directory tree (no-op if exists)."""

    @abstractmethod
    def list_dirs(self, path: str) -> List[str]:
        """List immediate subdirectory names under *path*."""

    @abstractmethod
    def move(self, src: str, dst: str) -> None:
        """Move *src* to *dst*, replacing *dst* if it exists."""

    @abstractmethod
    def copy_tree(self, src: str, dst: str) -> None:
        """Recursively copy *src* tree to *dst*, replacing *dst* if it exists."""

    @abstractmethod
    def read_json(self, path: str) -> Dict[str, Any]:
        """Deserialize a JSON file and return as dict."""

    @abstractmethod
    def write_json(self, path: str, data: Dict[str, Any]) -> None:
        """Serialize *data* to a JSON file at *path*."""


class LocalStorageService(BaseStorageService):
    """
    Filesystem-backed storage implementation.

    Replace with ``S3StorageService`` or ``GCSStorageService`` for cloud
    deployments — the ``ModelRegistry`` code stays unchanged.
    """

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def makedirs(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def list_dirs(self, path: str) -> List[str]:
        if not os.path.exists(path):
            return []
        return sorted(
            d for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d))
        )

    def move(self, src: str, dst: str) -> None:
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)
        logger.debug("Moved %s -> %s", src, dst)

    def copy_tree(self, src: str, dst: str) -> None:
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        logger.debug("Copied tree %s -> %s", src, dst)


    def read_json(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def write_json(self, path: str, data: Dict[str, Any]) -> None:
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        logger.debug("Wrote JSON to %s", path)
