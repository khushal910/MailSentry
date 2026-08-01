import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.repositories.google_account_repository import GoogleAccountRepository
from app.services.auth.google_oauth_service import GoogleOAuthService


class TestGoogleOAuthEdgeCases(unittest.TestCase):

    def setUp(self):
        self.mock_accounts_col = MagicMock()
        self.mock_users_col = MagicMock()
        self.db_mock = MagicMock()
        self.db_mock.__getitem__.side_effect = lambda name: (
            self.mock_accounts_col if "account" in name else self.mock_users_col
        )
        self.repo = GoogleAccountRepository(db=self.db_mock)

    def test_case_1_allow_reconnect_replace_refresh_token_if_new(self):
        """Case 1: User already connected Gmail. Allow reconnect and replace refresh token only if new token exists."""
        existing_doc = {
            "_id": ObjectId(),
            "user_id": "user_101",
            "google_user_id": "g_101",
            "google_email": "user@gmail.com",
            "refresh_token": "old_encrypted_rt",
            "google_connected": True,
        }
        self.mock_accounts_col.find_one.return_value = existing_doc

        now = datetime.now(timezone.utc)
        self.repo.upsert_account(
            google_email="user@gmail.com",
            google_user_id="g_101",
            user_id="user_101",
            encrypted_refresh_token="new_encrypted_rt",
            access_token_expiry=now + timedelta(hours=1),
        )

        self.mock_accounts_col.update_one.assert_called_once()
        _, update = self.mock_accounts_col.update_one.call_args[0]
        self.assertEqual(update["$set"]["refresh_token"], "new_encrypted_rt")

    def test_case_2_no_refresh_token_does_not_erase_old_token(self):
        """Case 2: Google returns no refresh token. Do NOT erase old refresh token."""
        existing_doc = {
            "_id": ObjectId(),
            "user_id": "user_101",
            "google_user_id": "g_101",
            "google_email": "user@gmail.com",
            "refresh_token": "valid_old_rt",
            "google_connected": True,
        }
        self.mock_accounts_col.find_one.return_value = existing_doc

        self.repo.upsert_account(
            google_email="user@gmail.com",
            google_user_id="g_101",
            user_id="user_101",
            encrypted_refresh_token=None,  # No new refresh token from Google
            access_token_expiry=datetime.now(timezone.utc),
        )

        _, update = self.mock_accounts_col.update_one.call_args[0]
        self.assertNotIn("refresh_token", update["$set"])

    def test_case_3_user_connects_different_gmail(self):
        """Case 3: User connects different Gmail. Update google_email, google_user_id, refresh_token on single record."""
        existing_doc = {
            "_id": ObjectId(),
            "user_id": "user_101",
            "google_user_id": "g_old_101",
            "google_email": "old_email@gmail.com",
            "refresh_token": "old_rt",
            "google_connected": True,
        }
        self.mock_accounts_col.find_one.return_value = existing_doc

        self.repo.upsert_account(
            google_email="new_email@gmail.com",
            google_user_id="g_new_202",
            user_id="user_101",
            encrypted_refresh_token="new_rt_202",
            access_token_expiry=datetime.now(timezone.utc),
        )

        self.mock_accounts_col.insert_one.assert_not_called()
        self.mock_accounts_col.update_one.assert_called_once()
        _, update = self.mock_accounts_col.update_one.call_args[0]
        set_fields = update["$set"]
        self.assertEqual(set_fields["google_email"], "new_email@gmail.com")
        self.assertEqual(set_fields["google_user_id"], "g_new_202")
        self.assertEqual(set_fields["refresh_token"], "new_rt_202")

    def test_case_4_account_exists_update_only_no_duplicate(self):
        """Case 4: Google account document exists. Update only. Never insert duplicate."""
        existing_doc = {
            "_id": ObjectId(),
            "user_id": "user_101",
            "google_user_id": "g_101",
            "google_email": "user@gmail.com",
        }
        self.mock_accounts_col.find_one.return_value = existing_doc

        self.repo.upsert_account(
            google_email="user@gmail.com",
            google_user_id="g_101",
            user_id="user_101",
        )

        self.mock_accounts_col.insert_one.assert_not_called()
        self.mock_accounts_col.update_one.assert_called_once()

    def test_case_5_db_failure_rollback_user_google_connected(self):
        """Case 5: Database failure. Rollback user.google_connected=False and return 500 error."""
        self.mock_accounts_col.find_one.return_value = None
        self.mock_accounts_col.insert_one.side_effect = Exception("MongoDB connection timeout")

        with self.assertRaises(HTTPException) as ctx:
            self.repo.upsert_account(
                google_email="user@gmail.com",
                google_user_id="g_101",
                user_id="user_101",
            )

        self.assertEqual(ctx.exception.status_code, 500)
        # Rollback call on users collection
        self.mock_users_col.update_one.assert_called_with(
            {"_id": "user_101"},
            {"$set": {"google_connected": False, "updated_at": unittest.mock.ANY}}
        )

    def test_case_7_invalid_current_user_id_falls_back_to_email_lookup(self):
        """Case 7: Stale current_user_id. Fall back to email lookup/creation without 404 error."""
        service = GoogleOAuthService(repo=self.repo)
        fake_id = ObjectId()
        self.mock_users_col.find_one.return_value = None  # Not found by ID or email
        self.mock_users_col.insert_one.return_value = MagicMock(inserted_id=fake_id)

        user_info = {"email": "stale_user@gmail.com", "sub": "g_stale"}
        with patch("app.db.mongodb.get_database", return_value=self.db_mock):
            res = service.find_or_create_user(user_info, current_user_id="deleted_user_id")

        self.assertEqual(res["email"], "stale_user@gmail.com")
        self.assertTrue(res["google_connected"])


    def test_case_8_duplicate_key_error_resolves_to_existing_account(self):
        """Case 8: Duplicate key error. Resolve by updating existing account cleanly."""
        existing_doc = {
            "_id": ObjectId(),
            "user_id": "user_101",
            "google_user_id": "g_101",
            "google_email": "duplicate@gmail.com",
        }
        # First call (before insert) returns None; fallback call (after DuplicateKeyError) returns existing_doc
        self.mock_accounts_col.find_one.side_effect = [None, existing_doc, existing_doc]
        self.mock_accounts_col.insert_one.side_effect = DuplicateKeyError("E11000 duplicate key error")

        result = self.repo.upsert_account(
            google_email="duplicate@gmail.com",
            google_user_id="g_101",
            user_id="user_101",
        )

        self.mock_accounts_col.update_one.assert_called()
        self.mock_users_col.update_one.assert_called_with(
            {"_id": "user_101"},
            {"$set": {"google_connected": True, "updated_at": unittest.mock.ANY}}
        )



if __name__ == "__main__":
    unittest.main()
