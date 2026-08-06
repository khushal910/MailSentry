import logging
import re
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import OperationFailure

from app.core.config import settings
from app.db.mongodb import get_database
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
                name="uniq_user_message",
            )
            # Index on user_id for fast queries
            self.collection.create_index("user_id", name="idx_user_id")
            # Index on message_id
            self.collection.create_index("message_id", name="idx_message_id")
            # Compound index for timeline queries
            self.collection.create_index(
                [("user_id", ASCENDING), ("classified_at", DESCENDING)],
                name="idx_user_classified_at",
            )
            # Compound index for label filtering with timeline sorting
            self.collection.create_index(
                [
                    ("user_id", ASCENDING),
                    ("predicted_label", ASCENDING),
                    ("classified_at", DESCENDING),
                ],
                name="idx_user_label_classified_at",
            )
            logger.info("Indexes ensured on emails collection.")
        except OperationFailure as e:
            if e.code in (85, 86):
                logger.info(
                    f"Email index already exists on collection: {e.details.get('errmsg', str(e))}"
                )
            else:
                logger.error(f"Error creating indexes on emails collection: {e!s}")
        except Exception as e:
            logger.error(f"Error creating indexes on emails collection: {e!s}")

    def verify_user_exists(self, user_id: str) -> bool:
        """
        Verifies if user_id exists in users or google_accounts collection.
        """
        if not user_id or not str(user_id).strip():
            return False
        try:
            users_col_name = getattr(settings, "USER_COLLECTION_NAME", "users")
            users_col = self.db[users_col_name]
            query = (
                {"$or": [{"_id": str(user_id)}, {"_id": ObjectId(user_id)}]}
                if ObjectId.is_valid(user_id)
                else {"_id": str(user_id)}
            )
            user_doc = users_col.find_one(query)
            if user_doc:
                return True

            google_col_name = getattr(
                settings, "GOOGLE_ACCOUNT_COLLECTION_NAME", "google_accounts"
            )
            google_col = self.db[google_col_name]
            g_query = (
                {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]}
                if ObjectId.is_valid(user_id)
                else {"user_id": str(user_id)}
            )
            acc_doc = google_col.find_one(g_query)
            if isinstance(acc_doc, dict) and acc_doc:
                return True

            return False
        except Exception as e:
            logger.error(f"Error verifying user existence for user_id={user_id}: {e!s}")
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
            google_col_name = getattr(
                settings, "GOOGLE_ACCOUNT_COLLECTION_NAME", "google_accounts"
            )
            google_acc_col = self.db[google_col_name]
            query = (
                {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]}
                if ObjectId.is_valid(user_id)
                else {"user_id": str(user_id)}
            )
            account = google_acc_col.find_one(query)
            if (
                account
                and account.get("google_connected")
                and account.get("refresh_token")
            ):
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
            logger.error(f"Error checking user access for user_id={user_id}: {e!s}")
            return False

    @staticmethod
    def _strip_html(text: str) -> str:
        """
        Removes all HTML/XML tags from a string to prevent stored XSS.
        e.g. '<b>Hello</b> world' -> 'Hello world'
        """
        return re.sub(r"<[^>]+>", "", text or "")

    def sanitize_email_data(
        self, email_input: dict[str, Any] | EmailCreateSchema
    ) -> dict[str, Any]:
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

        subject = self._strip_html(data.get("subject") or "")

        now = datetime.now(timezone.utc)

        def _parse_utc_dt(val: Any, default_dt: datetime) -> datetime:
            if not val:
                return default_dt
            if isinstance(val, datetime):
                if val.tzinfo is None:
                    return val.replace(tzinfo=timezone.utc)
                return val
            if isinstance(val, str) and val.strip():
                try:
                    s = val.strip().replace("Z", "+00:00")
                    dt = datetime.fromisoformat(s)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except Exception:
                    return default_dt
            return default_dt

        fetch_time = _parse_utc_dt(data.get("fetch_time"), now)
        classified_at = _parse_utc_dt(data.get("classified_at"), now)

        snippet = self._strip_html(data.get("snippet") or "") or None

        predicted_score = data.get("predicted_score")
        if predicted_score is not None:
            predicted_score = float(predicted_score)
            if predicted_score < 0.0 or predicted_score > 1.0:
                predicted_score = max(0.0, min(1.0, predicted_score))

        raw_date = data.get("sent_at") or data.get("received_at")
        parsed_sent = _parse_utc_dt(raw_date, classified_at)
        sent_at = parsed_sent.isoformat()
        received_at = parsed_sent.isoformat()

        sanitized = {
            "user_id": user_id,
            "message_id": message_id,
            "thread_id": data.get("thread_id"),
            "subject": subject,
            "snippet": snippet,
            "predicted_label": str(data.get("predicted_label", "ham")),
            "predicted_score": predicted_score,
            "fetch_time": fetch_time,
            "classified_at": classified_at,
            "received_at": received_at,
            "sent_at": sent_at,
            "updated_at": now,
        }
        return sanitized

    def save_email(
        self,
        email_data: dict[str, Any] | EmailCreateSchema,
        check_access: bool = True,
    ) -> dict[str, Any]:
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
            raise PermissionError(
                f"User ID '{user_id}' has not granted access to store emails"
            )

        now = datetime.now(timezone.utc)
        query = {"user_id": user_id, "message_id": message_id}

        update_doc = {
            "$set": {**sanitized, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        }

        self.collection.update_one(query, update_doc, upsert=True)
        return self.find_by_message_id(user_id, message_id)

    def save_emails_bulk(
        self,
        emails: list[dict[str, Any] | EmailCreateSchema],
        check_access: bool = True,
    ) -> list[dict[str, Any]]:
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
                logger.warning(f"Skipping email save due to validation error: {err!s}")
        return saved

    def find_by_message_id(
        self, user_id: str, message_id: str
    ) -> dict[str, Any] | None:
        """
        Finds a saved email by user_id and message_id.
        """
        return self.collection.find_one(
            {"user_id": str(user_id), "message_id": str(message_id)}
        )

    def get_existing_message_ids(self, user_id: str, message_ids: list[str]) -> set:
        """
        Returns a set of message_ids from the given list that already exist in MongoDB for the user.
        Uses a single $in batch query instead of N individual database queries.
        """
        if not message_ids:
            return set()
        clean_ids = [str(m).strip() for m in message_ids if str(m).strip()]
        if not clean_ids:
            return set()
        query = {"user_id": str(user_id), "message_id": {"$in": clean_ids}}
        try:
            docs = self.collection.find(query, {"message_id": 1})
            return {doc["message_id"] for doc in docs if "message_id" in doc}
        except Exception as e:
            logger.error(
                f"Error querying existing message_ids for user_id={user_id}: {e}"
            )
            return set()

    def get_user_emails(
        self,
        user_id: str,
        predicted_label: str | None = None,
        search: str | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Fetches classified emails for a specific user with optional label filter, search, and pagination.
        """
        query: dict[str, Any] = (
            {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]}
            if ObjectId.is_valid(user_id)
            else {"user_id": str(user_id)}
        )
        if predicted_label:
            query["predicted_label"] = predicted_label

        if search and search.strip():
            term = re.escape(search.strip())
            regex = {"$regex": term, "$options": "i"}
            query["$and"] = [
                {
                    "$or": [
                        {"subject": regex},
                        {"snippet": regex},
                        {"predicted_label": regex},
                        {"prediction": regex},
                        {"sender": regex},
                        {"from": regex},
                    ]
                }
            ]

        cursor = (
            self.collection.find(query)
            .sort(
                [
                    ("sent_at", DESCENDING),
                    ("received_at", DESCENDING),
                    ("classified_at", DESCENDING),
                    ("fetch_time", DESCENDING),
                    ("_id", DESCENDING),
                ]
            )
            .skip(skip)
            .limit(limit)
        )
        return list(cursor)

    def count_user_emails(
        self,
        user_id: str,
        predicted_label: str | None = None,
        search: str | None = None,
    ) -> int:
        """
        Counts total classified emails stored for a user, optionally filtered by predicted_label and search query.
        """
        query: dict[str, Any] = (
            {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]}
            if ObjectId.is_valid(user_id)
            else {"user_id": str(user_id)}
        )
        if predicted_label:
            query["predicted_label"] = predicted_label

        if search and search.strip():
            term = re.escape(search.strip())
            regex = {"$regex": term, "$options": "i"}
            query["$and"] = [
                {
                    "$or": [
                        {"subject": regex},
                        {"snippet": regex},
                        {"predicted_label": regex},
                        {"prediction": regex},
                        {"sender": regex},
                        {"from": regex},
                    ]
                }
            ]

        try:
            return self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting emails for user_id={user_id}: {e}")
            return 0

    def delete_user_emails(self, user_id: str) -> int:
        """
        Deletes all email records associated with user_id.
        """
        res = self.collection.delete_many({"user_id": str(user_id)})
        return res.deleted_count

    def find_by_id(self, email_id: str) -> dict[str, Any] | None:
        """
        Finds an email document in MongoDB by message_id or _id (supporting ObjectId, message_id, and string formats).
        Returns None if email_id is invalid or document is not found.
        """
        if not email_id or not str(email_id).strip():
            return None

        clean_id = str(email_id).strip()
        or_conditions: list[dict[str, Any]] = [
            {"message_id": clean_id},
            {"_id": clean_id},
        ]
        if ObjectId.is_valid(clean_id):
            or_conditions.append({"_id": ObjectId(clean_id)})

        query = {"$or": or_conditions}

        try:
            return self.collection.find_one(query)
        except Exception as e:
            logger.error(f"Error finding email by ID '{clean_id}': {e!s}")
            return None

    def update_summary(
        self,
        email_id: str,
        summary: str,
        summary_model: str | None = "gemini-2.5-flash",
        summary_created_at: datetime | str | None = None,
    ) -> bool:
        """
        Updates or sets the 'summary', 'summary_created_at', and 'summary_model' fields
        of an existing email document in MongoDB (by message_id or _id).
        """
        if not email_id or not str(email_id).strip():
            return False

        clean_id = str(email_id).strip()
        or_conditions: list[dict[str, Any]] = [
            {"message_id": clean_id},
            {"_id": clean_id},
        ]
        if ObjectId.is_valid(clean_id):
            or_conditions.append({"_id": ObjectId(clean_id)})

        query = {"$or": or_conditions}

        now = datetime.now(timezone.utc)

        if summary_created_at is None:
            created_at_val: datetime | str = now
        elif isinstance(summary_created_at, datetime):
            created_at_val = (
                summary_created_at.replace(tzinfo=timezone.utc)
                if summary_created_at.tzinfo is None
                else summary_created_at
            )
        else:
            created_at_val = str(summary_created_at).strip()

        model_name = str(summary_model).strip() if summary_model else "gemini-2.5-flash"

        update_payload = {
            "summary": str(summary).strip(),
            "summary_created_at": created_at_val,
            "summary_model": model_name,
            "updated_at": now,
        }

        try:
            result = self.collection.update_one(query, {"$set": update_payload})
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating summary for email ID '{clean_id}': {e!s}")
            return False

