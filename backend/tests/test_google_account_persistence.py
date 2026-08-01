import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from bson import ObjectId
from app.repositories.google_account_repository import GoogleAccountRepository


class TestGoogleAccountPersistence(unittest.TestCase):

    def setUp(self):
        self.mock_db = {}
        self.mock_accounts_col = MagicMock()
        self.mock_users_col = MagicMock()

        self.db_mock = MagicMock()
        self.db_mock.__getitem__.side_effect = lambda name: (
            self.mock_accounts_col if "account" in name else self.mock_users_col
        )
        self.repo = GoogleAccountRepository(db=self.db_mock)

    def test_insert_new_google_account(self):
        """If google_account does not exist, insert doc with all required fields and update user."""
        self.mock_accounts_col.find_one.return_value = None
        fake_id = ObjectId()
        self.mock_accounts_col.insert_one.return_value = MagicMock(inserted_id=fake_id)

        now = datetime.now(timezone.utc)
        result = self.repo.upsert_account(
            google_email="user@gmail.com",
            google_user_id="g_12345",
            user_id="user_6789",
            encrypted_refresh_token="encrypted_rt_sec_123",
            access_token_expiry=now + timedelta(hours=1),
        )

        self.mock_accounts_col.insert_one.assert_called_once()
        inserted_doc = self.mock_accounts_col.insert_one.call_args[0][0]

        self.assertEqual(inserted_doc["user_id"], "user_6789")
        self.assertEqual(inserted_doc["google_user_id"], "g_12345")
        self.assertEqual(inserted_doc["google_email"], "user@gmail.com")
        self.assertEqual(inserted_doc["refresh_token"], "encrypted_rt_sec_123")
        self.assertTrue(inserted_doc["google_connected"])
        self.assertIsNotNone(inserted_doc["created_at"])
        self.assertIsNotNone(inserted_doc["updated_at"])
        self.assertEqual(inserted_doc["created_at"].tzinfo, timezone.utc)

        # Check user update
        self.mock_users_col.update_one.assert_called_once()

    def test_update_existing_google_account_do_not_duplicate(self):
        """If google_account exists, update refresh_token, email, expiry, updated_at without duplicating."""
        existing_doc = {
            "_id": ObjectId(),
            "user_id": "user_6789",
            "google_user_id": "g_12345",
            "google_email": "user@gmail.com",
            "refresh_token": "old_encrypted_rt",
            "google_connected": True,
        }
        self.mock_accounts_col.find_one.return_value = existing_doc

        now = datetime.now(timezone.utc)
        new_expiry = now + timedelta(hours=2)

        self.repo.upsert_account(
            google_email="user_updated@gmail.com",
            google_user_id="g_12345",
            user_id="user_6789",
            encrypted_refresh_token="new_encrypted_rt",
            access_token_expiry=new_expiry,
        )

        self.mock_accounts_col.insert_one.assert_not_called()
        self.mock_accounts_col.update_one.assert_called_once()

        query, update = self.mock_accounts_col.update_one.call_args[0]
        self.assertEqual(query["_id"], existing_doc["_id"])
        set_fields = update["$set"]
        self.assertEqual(set_fields["google_email"], "user_updated@gmail.com")
        self.assertEqual(set_fields["refresh_token"], "new_encrypted_rt")
        self.assertEqual(set_fields["access_token_expiry"], new_expiry)

    def test_preserve_old_refresh_token_if_empty(self):
        """If new refresh token is empty or None, keep old refresh token and never overwrite with null."""
        existing_doc = {
            "_id": ObjectId(),
            "user_id": "user_6789",
            "google_user_id": "g_12345",
            "google_email": "user@gmail.com",
            "refresh_token": "existing_valid_encrypted_rt",
            "google_connected": True,
        }
        self.mock_accounts_col.find_one.return_value = existing_doc

        # Pass None or empty string for encrypted_refresh_token
        self.repo.upsert_account(
            google_email="user@gmail.com",
            google_user_id="g_12345",
            user_id="user_6789",
            encrypted_refresh_token="",
            access_token_expiry=datetime.now(timezone.utc),
        )

        query, update = self.mock_accounts_col.update_one.call_args[0]
        set_fields = update["$set"]
        # refresh_token should NOT be in $set if empty
        self.assertNotIn("refresh_token", set_fields)

    def test_ensure_unique_indexes(self):
        """Ensure unique indexes on user_id, google_user_id, and google_email."""
        self.repo.ensure_indexes()
        calls = self.mock_accounts_col.create_index.call_args_list
        index_names = [call[0][0] for call in calls]
        self.assertIn("user_id", index_names)
        self.assertIn("google_user_id", index_names)
        self.assertIn("google_email", index_names)


if __name__ == "__main__":
    unittest.main()
