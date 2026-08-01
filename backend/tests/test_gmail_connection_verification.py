import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from app.dependencies.auth import get_current_user
from app.dependencies.google_auth_deps import get_google_account_repository
from app.utils.main_utile import create_access_token


class TestGmailConnectionVerification(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.user_id = "507f1f77bcf86cd799439011"
        self.token = create_access_token(user_id=self.user_id, username="testuser")

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_gmail_account_missing_returns_403_please_connect(self):
        """If google_account missing, return 403 Forbidden ('Please connect Gmail.')."""
        mock_user = {"_id": self.user_id, "username": "testuser", "google_connected": False}
        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = None

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_google_account_repository] = lambda: mock_repo

        for endpoint in ["/api/gmail/fetch", "/api/gmail/classify", "/api/gmail/summarize", "/api/gmail/schedule-meeting"]:
            response = self.client.post(endpoint, headers={"Authorization": f"Bearer {self.token}"})
            self.assertEqual(response.status_code, 403)
            self.assertIn("Please connect Gmail.", response.json().get("detail", ""))

    def test_auto_fix_user_google_connected_if_account_missing(self):
        """If user.google_connected=true but google_account missing, auto-fix user.google_connected=false and return 403."""
        mock_user_desynced = {"_id": self.user_id, "username": "testuser", "google_connected": True}
        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = None  # Document missing

        app.dependency_overrides[get_current_user] = lambda: mock_user_desynced
        app.dependency_overrides[get_google_account_repository] = lambda: mock_repo

        response = self.client.post("/api/gmail/fetch", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 403)

        # Verify auto-fix was called
        mock_repo.update_user_google_connected.assert_called_with(
            self.user_id, False, unittest.mock.ANY
        )

    def test_missing_refresh_token_returns_403_reconnect_gmail(self):
        """If google_account exists but refresh_token missing or empty, return 403 ('Reconnect Gmail.')."""
        mock_user = {"_id": self.user_id, "username": "testuser", "google_connected": True}
        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = {
            "_id": "acc_123",
            "user_id": self.user_id,
            "google_email": "user@gmail.com",
            "refresh_token": "",  # Empty refresh token
            "google_connected": True,
        }

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_google_account_repository] = lambda: mock_repo

        response = self.client.post("/api/gmail/fetch", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get("detail"), "Reconnect Gmail.")

    def test_valid_connection_and_refresh_token_succeeds(self):
        """If valid google_account with refresh_token exists, operations succeed with 200 OK."""
        mock_user = {"_id": self.user_id, "username": "testuser", "google_connected": True}
        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = {
            "_id": "acc_123",
            "user_id": self.user_id,
            "google_email": "user@gmail.com",
            "refresh_token": "valid_encrypted_rt",
            "google_connected": True,
        }

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_google_account_repository] = lambda: mock_repo

        for endpoint in ["/api/gmail/fetch", "/api/gmail/classify", "/api/gmail/summarize", "/api/gmail/schedule-meeting"]:
            response = self.client.post(endpoint, headers={"Authorization": f"Bearer {self.token}"})
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
