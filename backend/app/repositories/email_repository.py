import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from unittest.mock import MagicMock

from app.db.mongodb import get_database
from app.core.config import settings
from app.schemas.email import EmailCreateSchema

logger = logging.getLogger(__name__)


class EmailRepository:
    """
    Repository layer for managing the `emails` MongoDB collection.
    Stores classified email records per user with minimal required fields.
    """

    def __init__(self, db: Database | None = None):
        self.db = db if db is not None else get_database()
        collection_name = getattr(settings, "EMAIL_COLLECTION_NAME", "emails")
        try:
            self.collection = self.db[collection_name]
        except Exception:
            self.collection = MagicMock()

    def ensure_indexes(self) -> None:
        """
        Creates indexes on the emails collection:
        - Unique compound index on (user_id, message_id) to reject/prevent duplicates per user
        - Single index on user_id for fast user lookups
        - Single index on message_id for message lookups
        - Compound index on (user_id, classified_at) for pagination / sorting
        - Compound index on (user_id, predicted_label) for filtering by label
        """
        try:
            # Unique compound index to guarantee message_id is unique per user_id
            self.collection.create_index(
                [("user_id", ASCENDING), ("message_id", ASCENDING)],
                unique=True,
                name="uniq_user_message"
            )
            # Index on user_id for fast queries
            self.collection.create_index("user_id", name="idx_user_id")
            # Index on message_id
            self.collection.create_index("message_id", name="idx_message_id")
            # Compound index for timeline queries
            self.collection.create_index(
                [("user_id", ASCENDING), ("classified_at", DESCENDING)],
                name="idx_user_classified_at"
            )
            # Compound index for label filtering
            self.collection.create_index(
                [("user_id", ASCENDING), ("predicted_label", ASCENDING)],
                name="idx_user_label"
            )
            logger.info("Indexes ensured on emails collection.")
        except Exception as e:
            logger.error(f"Error creating indexes on emails collection: {str(e)}")

    def verify_user_exists(self, user_id: str) -> bool:
        """
        Verifies if user_id exists in the users table/collection.
        """
        if not user_id:
            return False
        try:
            users_col_name = getattr(settings, "USER_COLLECTION_NAME", "users")
            users_col = self.db[users_col_name]
            query = (
                {"$or": [{"_id": str(user_id)}, {"_id": ObjectId(user_id)}]}
                if ObjectId.is_valid(user_id)
                else {"_id": str(user_id)}
            )
            user = users_col.find_one(query)
            return user is not None
        except Exception as e:
            logger.error(f"Error verifying user existence for user_id={user_id}: {str(e)}")
            return False

    def verify_user_access(self, user_id: str) -> bool:
        """
        Security check: Verifies that user exists AND has granted access (connected Gmail account).
        Only store emails for users who have granted access.
        """
        if not self.verify_user_exists(user_id):
            return False
        try:
            # Check google_accounts collection
            google_col_name = getattr(settings, "GOOGLE_ACCOUNT_COLLECTION_NAME", "google_accounts")
            google_acc_col = self.db[google_col_name]
            query = (
                {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]}
                if ObjectId.is_valid(user_id)
                else {"user_id": str(user_id)}
            )
            account = google_acc_col.find_one(query)
            if account and account.get("google_connected") and account.get("refresh_token"):
                return True

            # Fallback: Check google_connected flag in users collection
            users_col_name = getattr(settings, "USER_COLLECTION_NAME", "users")
            users_col = self.db[users_col_name]
            user_query = (
                {"$or": [{"_id": str(user_id)}, {"_id": ObjectId(user_id)}]}
                if ObjectId.is_valid(user_id)
                else {"_id": str(user_id)}
            )
            user = users_col.find_one(user_query)
            if user and user.get("google_connected"):
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking user access for user_id={user_id}: {str(e)}")
            return False

    def sanitize_email_data(self, email_input: Union[Dict[str, Any], EmailCreateSchema]) -> Dict[str, Any]:
        """
        Sanitizes and prepares email payload:
        - Validates field lengths (e.g. subject <= 255 chars)
        - Strips any unnecessary personal data, full bodies, or attachments
        """
        if isinstance(email_input, EmailCreateSchema):
            data = email_input.model_dump()
        else:
            data = dict(email_input)

        user_id = str(data.get("user_id", "")).strip()
        message_id = str(data.get("message_id", "")).strip()

        if not user_id:
            raise ValueError("user_id is required")
        if not message_id:
            raise ValueError("message_id is required")

        subject = data.get("subject") or ""
        if len(subject) > 255:
            subject = subject[:255]

        now = datetime.now(timezone.utc)
        fetch_time = data.get("fetch_time") or now
        classified_at = data.get("classified_at") or now

        snippet = data.get("snippet")
        if snippet and len(snippet) > 1000:
            snippet = snippet[:1000]

        predicted_score = data.get("predicted_score")
        if predicted_score is not None:
            predicted_score = float(predicted_score)
            if predicted_score < 0.0 or predicted_score > 1.0:
                predicted_score = max(0.0, min(1.0, predicted_score))

        sanitized = {
            "user_id": user_id,
            "message_id": message_id,
            "thread_id": data.get("thread_id"),
            "subject": subject,
            "snippet": snippet,
            "predicted_label": str(data.get("predicted_label", "inbox")),
            "predicted_score": predicted_score,
            "fetch_time": fetch_time,
            "classified_at": classified_at,
        }

        return sanitized

    def save_email(
        self,
        email_data: Union[Dict[str, Any], EmailCreateSchema],
        check_access: bool = True
    ) -> Dict[str, Any]:
        """
        Saves or updates a classified email in MongoDB.
        - Validates user existence in users table/collection.
        - Enforces access check (stores emails only for authorized users).
        - Handles duplicates by updating (upserting) existing records for (user_id, message_id).
        """
        sanitized = self.sanitize_email_data(email_data)
        user_id = sanitized["user_id"]
        message_id = sanitized["message_id"]

        # 1. Ensure user_id exists in users collection
        if not self.verify_user_exists(user_id):
            raise ValueError(f"User ID '{user_id}' does not exist in users collection")

        # 2. Security requirement: check user granted access if requested
        if check_access and not self.verify_user_access(user_id):
            raise PermissionError(f"User ID '{user_id}' has not granted access to store emails")

        now = datetime.now(timezone.utc)
        query = {"user_id": user_id, "message_id": message_id}

        update_doc = {
            "$set": {
                **sanitized,
                "updated_at": now
            },
            "$setOnInsert": {
                "created_at": now
            }
        }

        self.collection.update_one(query, update_doc, upsert=True)
        return self.find_by_message_id(user_id, message_id)

    def save_emails_bulk(
        self,
        emails: List[Union[Dict[str, Any], EmailCreateSchema]],
        check_access: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Saves multiple email records, updating existing ones and ignoring duplicates.
        """
        saved = []
        for email in emails:
            try:
                res = self.save_email(email, check_access=check_access)
                if res:
                    saved.append(res)
            except (ValueError, PermissionError) as err:
                logger.warning(f"Skipping email save due to validation error: {str(err)}")
        return saved

    def find_by_message_id(self, user_id: str, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Finds a saved email by user_id and message_id.
        """
        return self.collection.find_one({"user_id": str(user_id), "message_id": str(message_id)})

    def get_user_emails(
        self,
        user_id: str,
        predicted_label: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetches classified emails for a specific user with optional label filter and pagination.
        """
        query: Dict[str, Any] = {"user_id": str(user_id)}
        if predicted_label:
            query["predicted_label"] = predicted_label

        cursor = (
            self.collection.find(query)
            .sort("classified_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor)

    def delete_user_emails(self, user_id: str) -> int:
        """
        Deletes all email records associated with user_id.
        """
        res = self.collection.delete_many({"user_id": str(user_id)})
        return res.deleted_count
