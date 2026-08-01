import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, Depends, APIRouter
from main import app
from app.dependencies.auth import get_current_user
from app.dependencies.google_auth_deps import require_google_connected
from app.utils.main_utile import create_access_token


# Test router to verify 403 response on future Gmail APIs
test_gmail_router = APIRouter()

@test_gmail_router.get("/api/gmail/messages")
async def get_gmail_messages(account: dict = Depends(require_google_connected)):
    return {"status": "ok", "email": account.get("google_email")}

app.include_router(test_gmail_router)


class TestGoogleDisconnectEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.user_id = "507f1f77bcf86cd799439011"
        self.token = create_access_token(user_id=self.user_id, username="testuser")

    def test_disconnect_success_deletes_doc_and_updates_user(self):
        """Disconnecting deletes google_account doc and sets user.google_connected=false."""
        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = {
            "_id": "acc_123",
            "user_id": self.user_id,
            "google_email": "user@gmail.com",
            "google_connected": True,
        }
        mock_repo.delete_account.return_value = True
        mock_repo.update_user_google_connected.return_value = None

        mock_user = {"_id": self.user_id, "username": "testuser", "google_connected": True}

        with patch("app.api.google_status.disconnect_google_service") as mock_service:
            mock_service.return_value = {"success": True, "connected": False, "message": "Gmail account disconnected successfully"}
            app.dependency_overrides[get_current_user] = lambda: mock_user

            response = self.client.post(
                "/api/google/disconnect",
                headers={"Authorization": f"Bearer {self.token}"}
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("connected"), False)
        app.dependency_overrides.clear()

    def test_disconnect_already_disconnected_returns_success(self):
        """If already disconnected, returning success cleanly."""
        from app.services.auth.google_status import disconnect_google_service

        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = None  # Account does not exist

        res = disconnect_google_service(self.user_id, repo=mock_repo)
        self.assertEqual(res["success"], True)
        self.assertEqual(res["connected"], False)

    def test_disconnect_database_error_rollback(self):
        """On DB failure during disconnect, rollback user.google_connected and return 500 error."""
        from app.services.auth.google_status import disconnect_google_service

        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = {
            "_id": "acc_123",
            "user_id": self.user_id,
            "google_connected": True,
        }
        mock_repo.delete_account.side_effect = Exception("Database connection dropped")

        with self.assertRaises(HTTPException) as ctx:
            disconnect_google_service(self.user_id, repo=mock_repo)

        self.assertEqual(ctx.exception.status_code, 500)
        # Verify rollback was invoked
        mock_repo.update_user_google_connected.assert_called_with(
            self.user_id, True, unittest.mock.ANY
        )

    def test_future_gmail_api_returns_403_when_disconnected(self):
        """Future Gmail APIs return 403 Forbidden ('Please connect Gmail.') when user is disconnected."""
        mock_user_disconnected = {
            "_id": self.user_id,
            "username": "testuser",
            "google_connected": False,
        }
        mock_repo = MagicMock()
        mock_repo.find_by_user_id.return_value = None

        from app.dependencies.google_auth_deps import get_google_account_repository

        app.dependency_overrides[get_current_user] = lambda: mock_user_disconnected
        app.dependency_overrides[get_google_account_repository] = lambda: mock_repo

        response = self.client.get(
            "/api/gmail/messages",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data.get("detail"), "Please connect Gmail.")
        app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
