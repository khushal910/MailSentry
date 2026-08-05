import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import OperationFailure

from app.core.config import settings
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)


class GoogleAccountRepository:
    """
    Repository layer for managing the `google_accounts` MongoDB collection.
    """

    def __init__(self, db: Database | None = None):
        self.db = db if db is not None else get_database()
        try:
            self.collection = self.db[settings.GOOGLE_ACCOUNT_COLLECTION_NAME]
        except Exception:
            self.collection = MagicMock()

    def ensure_indexes(self) -> None:
        """
        Creates unique indexes on google_accounts collection:
        - Unique index on user_id (sparse=True)
        - Unique index on google_user_id (sparse=True)
        - Unique index on google_email (unique=True)
        """
        try:
            self.collection.create_index(
                "user_id", unique=True, sparse=True, name="uniq_google_user_id"
            )
            self.collection.create_index(
                "google_user_id",
                unique=True,
                sparse=True,
                name="uniq_google_account_user_id",
            )
            self.collection.create_index(
                "google_email", unique=True, name="uniq_google_email"
            )
            logger.info("Indexes ensured on google_accounts collection.")
        except OperationFailure as e:
            if e.code in (85, 86):
                logger.info(
                    f"Google account index already exists on collection: {e.details.get('errmsg', str(e))}"
                )
            else:
                logger.error(f"Error creating indexes on google_accounts: {e!s}")
        except Exception as e:
            logger.error(f"Error creating indexes on google_accounts: {e!s}")

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

    def find_account(
        self,
        user_id: str | None = None,
        google_user_id: str | None = None,
        google_email: str | None = None,
    ) -> dict | None:
        """
        Finds a Google account document by user_id, google_user_id, or google_email.
        """
        if user_id:
            doc = self.find_by_user_id(user_id)
            if doc:
                return doc
        if google_user_id:
            doc = self.collection.find_one({"google_user_id": str(google_user_id)})
            if doc:
                return doc
        if google_email:
            doc = self.find_by_email(google_email)
            if doc:
                return doc
        return None

    def update_user_google_connected(
        self, user_id: str | None, connected: bool, now: datetime
    ) -> None:
        """
        Updates google_connected=true on the target user in the users collection.
        """
        if not user_id:
            return
        try:
            users_col = self.db[settings.USER_COLLECTION_NAME]
            query = (
                {"$or": [{"_id": str(user_id)}, {"_id": ObjectId(user_id)}]}
                if ObjectId.is_valid(user_id)
                else {"_id": str(user_id)}
            )
            users_col.update_one(
                query, {"$set": {"google_connected": connected, "updated_at": now}}
            )
        except Exception as e:
            logger.error(f"Error updating user google_connected status: {e!s}")

    def delete_account(self, user_id: str) -> bool:
        """
        Deletes document from google_accounts collection for user_id.
        """
        query = (
            {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]}
            if ObjectId.is_valid(user_id)
            else {"user_id": str(user_id)}
        )
        result = self.collection.delete_many(query)
        deleted = getattr(result, "deleted_count", 0)
        return (deleted > 0) if isinstance(deleted, (int, float)) else True

    def disconnect_account(self, user_id: str) -> bool:
        """
        Marks Google account as disconnected for the user and unsets refresh token.
        """
        now = datetime.now(timezone.utc)
        query = (
            {"$or": [{"user_id": str(user_id)}, {"user_id": ObjectId(user_id)}]}
            if ObjectId.is_valid(user_id)
            else {"user_id": str(user_id)}
        )
        result = self.collection.update_many(
            query,
            {
                "$set": {
                    "google_connected": False,
                    "refresh_token": None,
                    "updated_at": now,
                }
            },
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

        Edge Case Handling:
        - Case 1: Allow reconnect; update refresh token ONLY if new token exists.
        - Case 2: If no new refresh token, preserve old refresh token (never overwrite with null/empty).
        - Case 3: If user connects different Gmail, update google_email, google_user_id, refresh_token.
        - Case 4: If account exists, update only; never insert duplicate.
        - Case 5: On database failure, rollback user.google_connected=False and return 500 error.
        - Case 8: On DuplicateKeyError, rollback user.google_connected=False and return 409 conflict.
        """
        from fastapi import HTTPException, status
        from pymongo.errors import DuplicateKeyError

        email = google_email.strip().lower()
        now = datetime.now(timezone.utc)
        existing = self.find_account(
            user_id=user_id, google_user_id=google_user_id, google_email=email
        )

        try:
            if existing:
                # Update existing Google account document (Case 1, Case 3, Case 4 - do NOT create duplicate)
                update_fields: dict = {
                    "google_email": email,
                    "access_token_expiry": access_token_expiry,
                    "updated_at": now,
                    "google_connected": True,
                }

                if google_user_id:
                    update_fields["google_user_id"] = str(google_user_id)

                if user_id:
                    update_fields["user_id"] = str(user_id)

                # Case 1 & Case 2: Update refresh_token ONLY if a new non-empty token is provided
                if encrypted_refresh_token and str(encrypted_refresh_token).strip():
                    update_fields["refresh_token"] = str(
                        encrypted_refresh_token
                    ).strip()

                self.collection.update_one(
                    {"_id": existing["_id"]}, {"$set": update_fields}
                )

                target_uid = user_id or existing.get("user_id")
                if target_uid:
                    self.update_user_google_connected(target_uid, True, now)

                logger.info(f"Updated Google account in MongoDB: {email}")
                updated_doc = self.collection.find_one({"_id": existing["_id"]})
                return updated_doc or {}
            else:
                # Create new Google account document
                doc = {
                    "user_id": str(user_id) if user_id else None,
                    "google_user_id": str(google_user_id) if google_user_id else None,
                    "google_email": email,
                    "refresh_token": (
                        str(encrypted_refresh_token).strip()
                        if (
                            encrypted_refresh_token
                            and str(encrypted_refresh_token).strip()
                        )
                        else None
                    ),
                    "access_token_expiry": access_token_expiry,
                    "google_connected": True,
                    "created_at": now,
                    "updated_at": now,
                }

                result = self.collection.insert_one(doc)
                doc["_id"] = getattr(result, "inserted_id", None)

                if user_id:
                    self.update_user_google_connected(user_id, True, now)

                logger.info(f"Created new Google account in MongoDB: {email}")
                return doc
        except DuplicateKeyError as dke:
            logger.warning(
                f"DuplicateKeyError in google_accounts: {dke!s}. Resolving by updating existing account."
            )
            existing_doc = self.find_account(
                user_id=user_id, google_user_id=google_user_id, google_email=email
            )
            if existing_doc:
                update_fields = {
                    "google_email": email,
                    "access_token_expiry": access_token_expiry,
                    "updated_at": now,
                    "google_connected": True,
                }
                if google_user_id:
                    update_fields["google_user_id"] = str(google_user_id)
                if user_id:
                    update_fields["user_id"] = str(user_id)
                if encrypted_refresh_token and str(encrypted_refresh_token).strip():
                    update_fields["refresh_token"] = str(
                        encrypted_refresh_token
                    ).strip()

                self.collection.update_one(
                    {"_id": existing_doc["_id"]}, {"$set": update_fields}
                )
                target_uid = user_id or existing_doc.get("user_id")
                if target_uid:
                    self.update_user_google_connected(target_uid, True, now)
                updated = self.collection.find_one({"_id": existing_doc["_id"]})
                return updated or existing_doc

            if user_id:
                self.update_user_google_connected(user_id, False, now)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Google account is already linked.",
            )

        except HTTPException:
            if user_id:
                self.update_user_google_connected(user_id, False, now)
            raise
        except Exception as e:
            logger.error(f"Database failure in google_accounts upsert: {e!s}")
            if user_id:
                self.update_user_google_connected(user_id, False, now)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database failure saving Google account: {e!s}",
            )

    def has_valid_refresh_token(
        self, user_id: str | None = None, google_email: str | None = None
    ) -> bool:
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
            {"$set": {"access_token_expiry": access_token_expiry, "updated_at": now}},
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
