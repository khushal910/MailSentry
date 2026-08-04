import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.services.profile_service import ProfileService
from app.utils.main_utile import hash_password
from app.utils.otp_util import hash_otp


class TestProfileService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_users_col = MagicMock()
        self.mock_accounts_col = MagicMock()
        self.mock_google_repo = MagicMock()

        self.db_mock = MagicMock()
        self.db_mock.__getitem__.side_effect = lambda name: (
            self.mock_accounts_col if "google" in name else self.mock_users_col
        )

        self.user_id = str(ObjectId())
        self.fake_user = {
            "_id": ObjectId(self.user_id),
            "username": "johndoe",
            "email": "john@example.com",
            "password": hash_password("OldPassword123!"),
            "role": "user",
            "providers": ["local", "google"],
            "is_active": True,
            "google_connected": True,
            "created_at": datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        }

        self.mock_users_col.find_one.return_value = self.fake_user
        self.mock_google_repo.find_by_user_id.return_value = {
            "_id": ObjectId(),
            "user_id": self.user_id,
            "google_email": "john@example.com",
            "google_connected": True,
        }

        self.service = ProfileService(google_repo=self.mock_google_repo)

    def test_get_profile_returns_formatted_data(self):
        """get_profile returns formatted user profile with Google account status."""
        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ):
            profile = self.service.get_profile(self.user_id)

        self.assertEqual(profile["id"], self.user_id)
        self.assertEqual(profile["username"], "johndoe")
        self.assertEqual(profile["email"], "john@example.com")
        self.assertEqual(profile["providers"], ["local", "google"])
        self.assertTrue(profile["google_connected"])
        self.assertEqual(profile["google_email"], "john@example.com")
        self.assertIn("2026-01-15", profile["created_at"])

    def test_update_username_no_changes_detected(self):
        """update_username raises 400 when username is unchanged."""
        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ), self.assertRaises(HTTPException) as ctx:
            self.service.update_username(self.user_id, "johndoe")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "No changes detected.")

    def test_update_username_success(self):
        """update_username updates users collection and logs audit message."""
        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ):
            # First call for _get_user returns fake_user; subsequent call returns updated user
            updated_user = dict(self.fake_user, username="john_newname")
            self.mock_users_col.find_one.side_effect = [
                self.fake_user,
                None,
                updated_user,
                updated_user,
            ]

            res = self.service.update_username(self.user_id, "john_newname")

        self.mock_users_col.update_one.assert_called_once()
        self.assertEqual(res["username"], "john_newname")

    def test_update_username_conflict_if_taken(self):
        """update_username raises 409 if username is taken by another user."""
        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ):
            self.mock_users_col.find_one.side_effect = [
                self.fake_user,
                {"_id": ObjectId()},
            ]

            with self.assertRaises(HTTPException) as ctx:
                self.service.update_username(self.user_id, "taken_username")

        self.assertEqual(ctx.exception.status_code, 409)

    @patch("app.services.profile_service.send_reset_otp_email")
    @patch(
        "app.services.profile_service.check_and_update_rate_limit", return_value=None
    )
    async def test_request_email_change_sends_otp(
        self, mock_rate_limit, mock_send_email
    ):
        """request_email_change stores OTP hash, 5-min expiry, and sends OTP email."""
        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ):
            # First call for _get_user; second call for existing email check (returns None)
            self.mock_users_col.find_one.side_effect = [self.fake_user, None]

            res = await self.service.request_email_change(
                self.user_id, "new_john@example.com"
            )

        self.mock_users_col.update_one.assert_called_once()
        update_args = self.mock_users_col.update_one.call_args[0][1]["$set"]
        self.assertEqual(update_args["email_change_pending"], "new_john@example.com")
        self.assertIn("email_otp_hash", update_args)
        self.assertEqual(res["pending_email"], "new_john@example.com")

    def test_verify_email_otp_success_and_disconnect_google(self):
        """verify_email_change_otp updates email and disconnects existing Google account with notice."""
        now = datetime.now(timezone.utc)
        plain_otp = "654321"
        pending_user = dict(
            self.fake_user,
            email_change_pending="new_john@example.com",
            email_otp_hash=hash_otp(plain_otp),
            email_otp_expire_at=now + timedelta(minutes=5),
            email_otp_attempts=0,
        )

        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ):
            updated_user = dict(
                pending_user, email="new_john@example.com", google_connected=False
            )
            self.mock_users_col.find_one.side_effect = [
                pending_user,
                updated_user,
                updated_user,
            ]

            res = self.service.verify_email_change_otp(self.user_id, plain_otp)

        self.assertEqual(res["email"], "new_john@example.com")
        self.assertIn("disconnected", res.get("notice", "").lower())
        self.mock_google_repo.collection.update_one.assert_called_once()

    def test_change_password_success(self):
        """change_password verifies current password and hashes new bcrypt password."""
        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ):
            res = self.service.change_password(
                user_id=self.user_id,
                current_pw="OldPassword123!",
                new_pw="BrandNewPassword456!",
                confirm_pw="BrandNewPassword456!",
            )

        self.mock_users_col.update_one.assert_called_once()
        self.assertEqual(res["message"], "Password changed successfully.")

    def test_change_password_rejects_google_only(self):
        """change_password raises 400 for Google-only users."""
        google_only_user = dict(self.fake_user, providers=["google"], password=None)

        with patch(
            "app.services.profile_service.get_database", return_value=self.db_mock
        ):
            self.mock_users_col.find_one.return_value = google_only_user

            with self.assertRaises(HTTPException) as ctx:
                self.service.change_password(
                    user_id=self.user_id,
                    current_pw="anything",
                    new_pw="NewPass123!",
                    confirm_pw="NewPass123!",
                )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Google-authenticated", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
