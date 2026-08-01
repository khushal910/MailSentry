import logging
from datetime import datetime, timezone
from pymongo.database import Database
from pymongo import ASCENDING
from app.db.mongodb import get_database
from app.core.config import settings

from bson import ObjectId

logger = logging.getLogger(__name__)

class GoogleAccountRepository:
    """
    Repository layer for managing the `google_accounts` MongoDB collection.
    """

    def __init__(self, db: Database | None = None):
        self.db = db if db is not None else get_database()
        self.collection = self.db[settings.GOOGLE_ACCOUNT_COLLECTION_NAME]


    def ensure_indexes(self) -> None:
        """
        Creates indexes on google_accounts collection:
        - Unique index on google_email
        - Index on user_id
        """
        try:
            self.collection.create_index("google_email", unique=True)
            self.collection.create_index("user_id", sparse=True)
            logger.info("Indexes ensured on google_accounts collection.")
        except Exception as e:
            logger.error(f"Error creating indexes on google_accounts: {str(e)}")

    def find_by_email(self, google_email: str) -> dict | None:
        """
        Finds a Google account document by google_email.
        """
        return self.collection.find_one({"google_email": google_email.strip().lower()})

    def find_by_user_id(self, user_id: str) -> dict | None:
        """
        Finds a Google account document by user_id.
        """
        doc = self.collection.find_one({"user_id": str(user_id)})
        if not doc and ObjectId.is_valid(user_id):
            doc = self.collection.find_one({"user_id": ObjectId(user_id)})
        return doc

    def disconnect_account(self, user_id: str) -> bool:
        """
        Marks Google account as disconnected for the user and unsets refresh token.
        """
        now = datetime.now(timezone.utc)
        query = {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]} if ObjectId.is_valid(user_id) else {"user_id": str(user_id)}
        result = self.collection.update_many(
            query,
            {"$set": {"google_connected": False, "refresh_token": None, "updated_at": now}}
        )
        modified = getattr(result, "modified_count", 0)
        return (modified > 0) if isinstance(modified, (int, float)) else True

    def upsert_account(
        self,
        google_email: str,
        google_user_id: str | None = None,
        user_id: str | None = None,
        encrypted_refresh_token: str | None = None,
        access_token_expiry: datetime | None = None,
    ) -> dict:
        """
        Upserts (creates or updates) a Google account document in MongoDB.

        Rules:
        - Stores google_user_id, refresh_token (encrypted), google_connected=True, user_id.
        - Never stores access_token permanently.
        - Preserves existing encrypted refresh_token if new one is not provided.
        """
        email = google_email.strip().lower()
        now = datetime.now(timezone.utc)
        existing = self.find_by_email(email)

        if existing:
            # Update existing Google account document
            update_fields: dict = {
                "updated_at": now,
                "google_connected": True,
            }

            if google_user_id:
                update_fields["google_user_id"] = google_user_id

            if access_token_expiry is not None:
                update_fields["access_token_expiry"] = access_token_expiry

            if user_id:
                update_fields["user_id"] = user_id

            # Update refresh_token only if a new non-empty token was provided
            if encrypted_refresh_token:
                update_fields["refresh_token"] = encrypted_refresh_token

            self.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": update_fields}
            )

            logger.info(f"Updated Google account in MongoDB: {email}")
            return self.find_by_email(email) or {}
        else:
            # Create new Google account document
            doc = {
                "user_id": user_id,
                "google_user_id": google_user_id,
                "google_email": email,
                "refresh_token": encrypted_refresh_token,
                "access_token_expiry": access_token_expiry,
                "google_connected": True,
                "created_at": now,
                "updated_at": now,
            }

            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            logger.info(f"Created new Google account in MongoDB: {email}")
            return doc

    def has_valid_refresh_token(self, user_id: str | None = None, google_email: str | None = None) -> bool:
        """
        Checks if a Google account record exists for the user_id or google_email
        AND contains a non-empty stored refresh_token.
        """
        doc = None
        if user_id:
            doc = self.find_by_user_id(user_id)
        if not doc and google_email:
            doc = self.find_by_email(google_email)

        if doc and doc.get("refresh_token"):
            logger.debug("Found existing valid refresh token for account.")
            return True
        return False

    def update_access_token_expiry(
        self, google_email: str, access_token_expiry: datetime
    ) -> bool:
        """
        Updates only the access_token_expiry timestamp for a given Google account.
        """
        email = google_email.strip().lower()
        now = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"google_email": email},
            {"$set": {"access_token_expiry": access_token_expiry, "updated_at": now}}
        )
        return result.modified_count > 0

    def get_decrypted_refresh_token(self, google_email: str) -> str | None:
        """
        Retrieves and decrypts the refresh token for a Google account by email.
        Helper method prepared for Gmail API integration and token refresh.
        """
        from app.utils.encryption_util import decrypt_token
        doc = self.find_by_email(google_email)
        if not doc or not doc.get("refresh_token"):
            return None
        return decrypt_token(doc["refresh_token"])


