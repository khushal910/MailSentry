import logging
from datetime import datetime, timezone
from pymongo.database import Database
from pymongo import ASCENDING
from app.db.mongodb import get_database
from app.core.config import settings

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
        return self.collection.find_one({"user_id": user_id})

    def upsert_account(
        self,
        google_email: str,
        user_id: str | None = None,
        encrypted_refresh_token: str | None = None,
        access_token_expiry: datetime | None = None,
    ) -> dict:
        """
        Upserts (creates or updates) a Google account document in MongoDB.

        Rules:
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
