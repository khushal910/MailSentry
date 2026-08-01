import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId
from jose import jwt

from main import app
from app.core.config import settings
from app.utils.main_utile import create_access_token


class TestGoogleStatusEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def generate_expired_token(self, user_id: str, username: str = "testuser") -> str:
        expire = datetime.now(timezone.utc) - timedelta(minutes=10)
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.now(timezone.utc) - timedelta(minutes=20),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def test_google_status_connected(self):
        user_id = str(ObjectId())
        now = datetime.now(timezone.utc)
        user_doc = {
            "_id": ObjectId(user_id),
            "username": "testuser",
            "email": "testuser@example.com",
        }
        google_account_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "google_user_id": "google_123456789",
            "google_email": "testuser@gmail.com",
            "refresh_token": "gser_encrypted_secret_token",
            "google_connected": True,
            "created_at": now,
            "updated_at": now,
        }

        mock_db = MagicMock()
        mock_users_col = MagicMock()
        mock_users_col.find_one.return_value = user_doc

        mock_google_col = MagicMock()
        mock_google_col.find_one.return_value = google_account_doc

        def get_col(name):
            if name == settings.USER_COLLECTION_NAME:
                return mock_users_col
            elif name == settings.GOOGLE_ACCOUNT_COLLECTION_NAME:
                return mock_google_col
            return MagicMock()

        mock_db.__getitem__.side_effect = get_col

        token = create_access_token(user_id=user_id, username="testuser")

        with patch("app.dependencies.auth.get_database", return_value=mock_db), \
             patch("app.repositories.google_account_repository.get_database", return_value=mock_db):
            response = self.client.get(
                "/api/google/status",
                headers={"Authorization": f"Bearer {token}"}
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["connected"])
        self.assertEqual(data["google_email"], "testuser@gmail.com")
        self.assertIn("connected_at", data)
        self.assertIn("last_updated", data)
        self.assertNotIn("refresh_token", data)
        self.assertNotIn("google_user_id", data)
        self.assertNotIn("google_id", data)

    def test_google_status_not_connected(self):
        user_id = str(ObjectId())
        user_doc = {
            "_id": ObjectId(user_id),
            "username": "testuser",
            "email": "testuser@example.com",
        }

        mock_db = MagicMock()
        mock_users_col = MagicMock()
        mock_users_col.find_one.return_value = user_doc

        mock_google_col = MagicMock()
        mock_google_col.find_one.return_value = None

        def get_col(name):
            if name == settings.USER_COLLECTION_NAME:
                return mock_users_col
            elif name == settings.GOOGLE_ACCOUNT_COLLECTION_NAME:
                return mock_google_col
            return MagicMock()

        mock_db.__getitem__.side_effect = get_col

        token = create_access_token(user_id=user_id, username="testuser")

        with patch("app.dependencies.auth.get_database", return_value=mock_db), \
             patch("app.repositories.google_account_repository.get_database", return_value=mock_db):
            response = self.client.get(
                "/api/google/status",
                cookies={"access_token": token}
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, {"connected": False})

    def test_google_status_missing_jwt(self):
        response = self.client.get("/api/google/status")
        self.assertEqual(response.status_code, 401)

    def test_google_status_invalid_jwt(self):
        response = self.client.get(
            "/api/google/status",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        self.assertEqual(response.status_code, 401)

    def test_google_status_expired_jwt(self):
        user_id = str(ObjectId())
        expired_token = self.generate_expired_token(user_id=user_id)
        response = self.client.get(
            "/api/google/status",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        self.assertEqual(response.status_code, 401)

    def test_google_status_user_deleted(self):
        user_id = str(ObjectId())

        mock_db = MagicMock()
        mock_users_col = MagicMock()
        mock_users_col.find_one.return_value = None

        mock_db.__getitem__.return_value = mock_users_col

        token = create_access_token(user_id=user_id, username="deleteduser")

        with patch("app.dependencies.auth.get_database", return_value=mock_db):
            response = self.client.get(
                "/api/google/status",
                headers={"Authorization": f"Bearer {token}"}
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")


if __name__ == "__main__":
    unittest.main()
