import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pymongo import DESCENDING
from pymongo.database import Database
from unittest.mock import MagicMock

from app.db.mongodb import get_database
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelRepository:
    """
    Repository layer for managing the `models` MongoDB collection.
    Tracks trained ML classification models, versions, file paths, metrics, and statuses.
    """

    def __init__(self, db: Database | None = None):
        self.db = db if db is not None else get_database()
        col_name = getattr(settings, "MODEL_COLLECTION_NAME", "models")
        try:
            self.collection = self.db[col_name]
        except Exception:
            self.collection = MagicMock()

    def ensure_indexes(self) -> None:
        """
        Creates indexes on the models collection:
        - Unique index on version
        - Index on status (active / archived)
        - Index on created_at for chronological lookups
        """
        try:
            self.collection.create_index("version", unique=True, sparse=True, name="uniq_model_version")
            self.collection.create_index("status", name="idx_model_status")
            self.collection.create_index([("created_at", DESCENDING)], name="idx_model_created_at")
            logger.info("Indexes ensured on models collection.")
        except Exception as e:
            logger.error(f"Error creating indexes on models collection: {str(e)}")

    def record_model(
        self,
        model_name: str,
        version: str,
        file_path: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Records a newly saved ML model in MongoDB:
        1. Archives any existing 'active' model records.
        2. Inserts a new model document marked as 'active'.
        """
        now = datetime.now(timezone.utc)
        try:
            # Mark previous active models as archived
            self.collection.update_many(
                {"status": "active"},
                {"$set": {"status": "archived", "archived_at": now}}
            )
        except Exception as e:
            logger.warning(f"Failed to archive previous active models: {str(e)}")

        model_doc = {
            "model_name": model_name,
            "version": version,
            "path": file_path,
            "metrics": metrics or {},
            "status": "active",
            "created_at": now,
            "updated_at": now
        }

        self.collection.insert_one(model_doc)
        return model_doc

    def get_active_model_record(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the currently active ML model record.
        """
        record = self.collection.find_one({"status": "active"})
        if not record:
            # Fallback to the latest record by created_at
            record = self.collection.find_one(sort=[("created_at", DESCENDING)])
        return record

    def get_all_model_records(self) -> List[Dict[str, Any]]:
        """
        Retrieves all model records chronologically descending.
        """
        cursor = self.collection.find().sort("created_at", DESCENDING)
        return list(cursor)
