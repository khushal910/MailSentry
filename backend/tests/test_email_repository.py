import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from bson import ObjectId

from app.repositories.email_repository import EmailRepository
from app.schemas.email import EmailCreateSchema


class MockDatabase:
    """Mock Database implementation for testing EmailRepository."""
    def __init__(self, emails_col, users_col, google_col):
        self.emails_col = emails_col
        self.users_col = users_col
        self.google_col = google_col

    def __getitem__(self, name):
        if "email" in name.lower():
            return self.emails_col
        elif "user" in name.lower():
            return self.users_col
        elif "google" in name.lower():
            return self.google_col
        return MagicMock()


class TestEmailRepository(unittest.TestCase):

    def setUp(self):
        self.mock_emails_col = MagicMock()
        self.mock_users_col = MagicMock()
        self.mock_google_col = MagicMock()

        self.db_mock = MockDatabase(
            emails_col=self.mock_emails_col,
            users_col=self.mock_users_col,
            google_col=self.mock_google_col
        )
        self.repo = EmailRepository(db=self.db_mock)

    def test_ensure_indexes(self):
        """Verifies index creation including compound unique index on (user_id, message_id)."""
        self.repo.ensure_indexes()
        calls = self.mock_emails_col.create_index.call_args_list
        self.assertTrue(len(calls) >= 4)
        
        # Check compound unique index call
        compound_call = calls[0]
        index_spec = compound_call[0][0]
        kwargs = compound_call[1]
        self.assertEqual(index_spec, [("user_id", 1), ("message_id", 1)])
        self.assertTrue(kwargs.get("unique"))

    def test_verify_user_exists(self):
        """Verifies checking user existence in users collection."""
        user_id = str(ObjectId())
        self.mock_users_col.find_one.return_value = {"_id": ObjectId(user_id), "username": "testuser"}
        
        exists = self.repo.verify_user_exists(user_id)
        self.assertTrue(exists)

        self.mock_users_col.find_one.return_value = None
        exists = self.repo.verify_user_exists("non_existent_id")
        self.assertFalse(exists)

    def test_verify_user_access(self):
        """Verifies security check: only allow operations if user exists and has granted access."""
        user_id = str(ObjectId())
        
        # Case 1: User does not exist
        self.mock_users_col.find_one.return_value = None
        self.assertFalse(self.repo.verify_user_access(user_id))

        # Case 2: User exists, but no google connection
        self.mock_users_col.find_one.return_value = {"_id": ObjectId(user_id)}
        self.mock_google_col.find_one.return_value = None
        self.assertFalse(self.repo.verify_user_access(user_id))

        # Case 3: User exists and has active google connection
        self.mock_google_col.find_one.return_value = {
            "user_id": user_id,
            "google_connected": True,
            "refresh_token": "valid_token"
        }
        self.assertTrue(self.repo.verify_user_access(user_id))

    def test_reject_if_user_does_not_exist(self):
        """Should raise ValueError if user_id does not exist in users collection."""
        user_id = "invalid_user"
        self.mock_users_col.find_one.return_value = None

        email_data = {
            "user_id": user_id,
            "message_id": "msg_001",
            "subject": "Test Email",
            "predicted_label": "spam"
        }

        with self.assertRaises(ValueError) as ctx:
            self.repo.save_email(email_data, check_access=False)
        self.assertIn("does not exist", str(ctx.exception))

    def test_reject_if_user_has_not_granted_access(self):
        """Should raise PermissionError if user exists but has not granted access (check_access=True)."""
        user_id = str(ObjectId())
        # User exists in users collection
        self.mock_users_col.find_one.return_value = {"_id": ObjectId(user_id), "google_connected": False}
        # Google account collection missing or not connected
        self.mock_google_col.find_one.return_value = None

        email_data = {
            "user_id": user_id,
            "message_id": "msg_002",
            "subject": "Test Security",
            "predicted_label": "important"
        }

        with self.assertRaises(PermissionError) as ctx:
            self.repo.save_email(email_data, check_access=True)
        self.assertIn("has not granted access", str(ctx.exception))

    def test_save_email_upsert_duplicate_message_id(self):
        """Upsert logic: updating existing email if (user_id, message_id) already exists."""
        user_id = str(ObjectId())
        message_id = "msg_12345"

        self.mock_users_col.find_one.return_value = {"_id": ObjectId(user_id), "google_connected": True}
        self.mock_google_col.find_one.return_value = {
            "user_id": user_id,
            "google_connected": True,
            "refresh_token": "token"
        }

        saved_doc = {
            "user_id": user_id,
            "message_id": message_id,
            "subject": "Updated Subject",
            "predicted_label": "important",
            "predicted_score": 0.95
        }
        self.mock_emails_col.find_one.return_value = saved_doc

        email_payload = {
            "user_id": user_id,
            "message_id": message_id,
            "subject": "Updated Subject",
            "predicted_label": "important",
            "predicted_score": 0.95,
            "fetch_time": datetime.now(timezone.utc),
            "classified_at": datetime.now(timezone.utc)
        }

        res = self.repo.save_email(email_payload, check_access=True)

        self.mock_emails_col.update_one.assert_called_once()
        query_used = self.mock_emails_col.update_one.call_args[0][0]
        upsert_flag = self.mock_emails_col.update_one.call_args[1].get("upsert")

        self.assertEqual(query_used, {"user_id": user_id, "message_id": message_id})
        self.assertTrue(upsert_flag)
        self.assertEqual(res["subject"], "Updated Subject")

    def test_subject_length_validation_and_truncation(self):
        """Enforces subject <= 255 chars validation."""
        user_id = str(ObjectId())
        self.mock_users_col.find_one.return_value = {"_id": ObjectId(user_id)}

        long_subject = "A" * 300
        email_data = {
            "user_id": user_id,
            "message_id": "msg_long",
            "subject": long_subject,
            "predicted_label": "spam"
        }

        sanitized = self.repo.sanitize_email_data(email_data)
        self.assertEqual(len(sanitized["subject"]), 255)
        self.assertEqual(sanitized["subject"], "A" * 255)

    def test_minimal_fields_no_body_or_attachments(self):
        """Sanitizer strips extra fields like full body or attachments to preserve privacy and minimal storage."""
        user_id = str(ObjectId())
        email_data = {
            "user_id": user_id,
            "message_id": "msg_privacy",
            "subject": "Private Email",
            "snippet": "Short snippet content for UI",
            "body": "SUPER SECRET FULL EMAIL BODY CONTENT THAT SHOULD NOT BE STORED",
            "attachments": [{"filename": "secret.pdf", "data": "binary"}],
            "predicted_label": "promotions",
            "predicted_score": 0.82
        }

        sanitized = self.repo.sanitize_email_data(email_data)
        self.assertNotIn("body", sanitized)
        self.assertNotIn("attachments", sanitized)
        self.assertEqual(sanitized["snippet"], "Short snippet content for UI")
        self.assertEqual(sanitized["predicted_score"], 0.82)


if __name__ == "__main__":
    unittest.main()
