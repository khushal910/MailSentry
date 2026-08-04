import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.dependencies.google_auth_deps import get_google_oauth_service
from app.services.auth.google_oauth_service import GoogleOAuthService
from main import app


class TestGoogleCallbackValidation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_callback_no_code(self):
        """No authorization code -> 400 Bad Request"""
        response = self.client.get("/auth/google/callback?format=json")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)

    def test_callback_invalid_code(self):
        """Invalid authorization code -> 400 Bad Request"""
        mock_service = MagicMock(spec=GoogleOAuthService)
        mock_service.validate_csrf_state = MagicMock(return_value=None)

        async def mock_exchange(code):
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        mock_service.exchange_code_for_tokens = mock_exchange
        app.dependency_overrides[get_google_oauth_service] = lambda: mock_service

        response = self.client.get(
            "/auth/google/callback?code=invalid_code_123&format=json"
        )
        self.assertEqual(response.status_code, 400)

    def test_callback_invalid_id_token(self):
        """Invalid ID token -> 401 Unauthorized"""
        mock_service = MagicMock(spec=GoogleOAuthService)
        mock_service.validate_csrf_state = MagicMock(return_value=None)

        async def mock_exchange(code):
            return {"id_token": "invalid_id_token", "access_token": "at_123"}

        mock_service.exchange_code_for_tokens = mock_exchange
        mock_service.verify_id_token.side_effect = HTTPException(
            status_code=401, detail="Invalid Google ID Token"
        )
        app.dependency_overrides[get_google_oauth_service] = lambda: mock_service

        response = self.client.get("/auth/google/callback?code=valid_code&format=json")
        self.assertEqual(response.status_code, 401)

    def test_callback_missing_email(self):
        """Email missing from ID token -> 400 Bad Request"""
        mock_service = MagicMock(spec=GoogleOAuthService)
        mock_service.validate_csrf_state = MagicMock(return_value=None)

        async def mock_exchange(code):
            return {"id_token": "valid_id_token", "access_token": "at_123"}

        mock_service.exchange_code_for_tokens = mock_exchange
        mock_service.verify_id_token.side_effect = HTTPException(
            status_code=400, detail="Email missing from Google ID token payload."
        )
        app.dependency_overrides[get_google_oauth_service] = lambda: mock_service

        response = self.client.get("/auth/google/callback?code=valid_code&format=json")
        self.assertEqual(response.status_code, 400)

    def test_callback_google_server_error(self):
        """Google server error -> 500 Internal Server Error"""
        mock_service = MagicMock(spec=GoogleOAuthService)
        mock_service.validate_csrf_state = MagicMock(return_value=None)

        async def mock_exchange(code):
            raise HTTPException(status_code=500, detail="Google server error")

        mock_service.exchange_code_for_tokens = mock_exchange
        app.dependency_overrides[get_google_oauth_service] = lambda: mock_service

        response = self.client.get("/auth/google/callback?code=valid_code&format=json")
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
