"""
Model Registry — single source of truth for model versioning and champion management.

Manages the ``champion/`` (active production model) and ``archive/`` (previous versions).
Delegates all file operations to an injected :class:`BaseStorageService`, making
it straightforward to swap local filesystem for cloud storage.

Directory layout managed by this module::

    model_registry/
        champion/
            metadata.json
            model/          ← model artifacts
            preprocessor/   ← TF-IDF / label encoder
        archive/
            v1/
            v2/
            …
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

from src.entity.model_metadata import ModelMetadata
from src.logger import logger
from src.services.storage_service import BaseStorageService, LocalStorageService


class ModelRegistry:
    """
    Versioned model registry with champion promotion and rollback.

    Parameters
    ----------
    registry_root : str
        Absolute or relative path to the top-level ``model_registry/`` directory.
    storage : BaseStorageService, optional
        Storage backend (defaults to :class:`LocalStorageService`).
    """

    CHAMPION_DIR = "champion"
    ARCHIVE_DIR = "archive"
    METADATA_FILE = "metadata.json"

    def __init__(
        self,
        registry_root: str,
        storage: Optional[BaseStorageService] = None,
    ) -> None:
        self.root = os.path.abspath(registry_root)
        self.champion_path = os.path.join(self.root, self.CHAMPION_DIR)
        self.archive_path = os.path.join(self.root, self.ARCHIVE_DIR)
        self.storage = storage or LocalStorageService()

        # Ensure base directories exist
        self.storage.makedirs(self.champion_path)
        self.storage.makedirs(self.archive_path)

    # ── Queries ───────────────────────────────────────────────────────────

    def has_champion(self) -> bool:
        """Return *True* if a champion model with metadata is present."""
        return self.storage.exists(
            os.path.join(self.champion_path, self.METADATA_FILE)
        )

    def load_champion_metadata(self) -> ModelMetadata:
        """Load and return the current champion's metadata."""
        meta_path = os.path.join(self.champion_path, self.METADATA_FILE)
        data = self.storage.read_json(meta_path)
        return ModelMetadata.from_dict(data)

    def get_next_version(self) -> str:
        """Scan ``archive/`` for ``vN`` directories and return ``v(N+1)``."""
        existing = self.storage.list_dirs(self.archive_path)
        version_numbers: List[int] = []
        for dirname in existing:
            match = re.match(r"^v(\d+)$", dirname)
            if match:
                version_numbers.append(int(match.group(1)))
        return f"v{max(version_numbers, default=0) + 1}"

    def list_versions(self) -> List[Dict[str, object]]:
        """List all archived versions with metadata summaries."""
        versions: List[Dict[str, object]] = []
        for dirname in self.storage.list_dirs(self.archive_path):
            meta_path = os.path.join(self.archive_path, dirname, self.METADATA_FILE)
            if self.storage.exists(meta_path):
                data = self.storage.read_json(meta_path)
                versions.append({
                    "version": dirname,
                    "model_name": data.get("model_name", "unknown"),
                    "score": data.get("score", 0.0),
                    "trained_at": data.get("trained_at", ""),
                })
        return versions

    # ── Mutations ─────────────────────────────────────────────────────────

    def promote_champion(
        self,
        staging_dir: str,
        metadata: ModelMetadata,
    ) -> ModelMetadata:
        """
        Install a new champion model from a staging directory.

        1. Archive the current champion (if one exists) → ``archive/vN``
        2. Compute the next version number
        3. Copy the staging directory contents into ``champion/``
        4. Write ``metadata.json`` with the final version

        Parameters
        ----------
        staging_dir : str
            Temporary directory containing the model artifacts produced by
            :class:`ModelSaverFactory` (``model/``, ``preprocessor/``, etc.).
        metadata : ModelMetadata
            Metadata for the new champion. The ``version`` field is set
            automatically.

        Returns
        -------
        ModelMetadata
            The metadata with its ``version`` field populated.
        """
        # Step 1: archive current champion
        if self.has_champion():
            current_meta = self.load_champion_metadata()
            archive_dest = os.path.join(self.archive_path, current_meta.version)
            logger.info(
                "Archiving current champion %s -> %s",
                current_meta.version,
                archive_dest,
            )

            self.storage.move(self.champion_path, archive_dest)
            self.storage.makedirs(self.champion_path)

        # Step 2: compute next version (after archiving, so scan is correct)
        version = self.get_next_version()
        metadata.version = version

        # Step 3: install new champion
        self.storage.copy_tree(staging_dir, self.champion_path)

        # Step 4: write metadata
        meta_path = os.path.join(self.champion_path, self.METADATA_FILE)
        self.storage.write_json(meta_path, metadata.to_dict())

        logger.info(
            "Promoted new champion: %s (version %s, %s=%.4f)",
            metadata.model_name,
            version,
            metadata.metric,
            metadata.score,
        )
        return metadata

    def rollback(self, version: str) -> ModelMetadata:
        """
        Instantly roll back to a previously archived version.

        The current champion is archived first (no data loss), then the
        target version is promoted to champion.  No retraining is required.

        Parameters
        ----------
        version : str
            Version identifier to restore, e.g. ``"v2"``.

        Returns
        -------
        ModelMetadata
            Metadata of the restored champion.

        Raises
        ------
        ValueError
            If the requested version does not exist in the archive.
        """
        target_dir = os.path.join(self.archive_path, version)
        if not self.storage.exists(target_dir):
            available = self.storage.list_dirs(self.archive_path)
            raise ValueError(
                f"Version '{version}' not found in archive. "
                f"Available versions: {available}"
            )

        # Archive current champion (swap)
        if self.has_champion():
            current_meta = self.load_champion_metadata()
            current_archive = os.path.join(self.archive_path, current_meta.version)
            logger.info(
                "Archiving current champion %s before rollback",
                current_meta.version,
            )
            self.storage.move(self.champion_path, current_archive)
            self.storage.makedirs(self.champion_path)

        # Promote target version
        self.storage.move(target_dir, self.champion_path)
        restored_meta = self.load_champion_metadata()
        logger.info(
            "Rolled back to version %s (model: %s, %s=%.4f)",
            version,
            restored_meta.model_name,
            restored_meta.metric,
            restored_meta.score,
        )
        return restored_meta
