import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.utils.main_utile import create_access_token
from main import app


class TestClassifyEmailEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.user_id = "507f1f77bcf86cd799439011"
        self.token = create_access_token(user_id=self.user_id, username="testuser")

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_classify_email_unauthorized_without_jwt(self):
        """Should return 401 Unauthorized if JWT token is missing."""
        response = self.client.post(
            "/api/classify-email", json={"subject": "Hello", "body": "How are you?"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication required", response.json().get("detail", ""))

    @patch("app.services.ml_model_service.MLModelService.classify_text")
    def test_classify_email_success_with_jwt(self, mock_classify):
        """Should return 200 OK with classification result when valid JWT and model exist."""
        mock_user = {"_id": self.user_id, "username": "testuser"}
        app.dependency_overrides[get_current_user] = lambda: mock_user

        mock_classify.return_value = {
            "subject": "Claim your reward",
            "predicted_label": "spam",
            "predicted_score": 0.96,
            "classified_at": "2026-08-01T10:00:00Z",
        }

        response = self.client.post(
            "/api/classify-email",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"subject": "Claim your reward", "body": "Click here to win $1000"},
        )

        self.assertEqual(response.status_code, 200)
        json_resp = response.json()
        self.assertEqual(json_resp.get("status_code"), 200)
        self.assertEqual(json_resp.get("message"), "Email classified successfully")

        data = json_resp.get("data", {})
        self.assertEqual(data.get("predicted_label"), "spam")
        self.assertEqual(data.get("predicted_score"), 0.96)

    @patch("app.services.ml_model_service.MLModelService.load_latest_model")
    def test_classify_email_model_missing_returns_500(self, mock_load_model):
        """Should return 500 Internal Server Error if ML classification model is missing or corrupted."""
        mock_user = {"_id": self.user_id, "username": "testuser"}
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Simulate missing/corrupted model returning None
        mock_load_model.return_value = None

        response = self.client.post(
            "/api/classify-email",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"subject": "Test Email", "body": "Some body"},
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "ML classification model is not available",
            response.json().get("detail", ""),
        )


if __name__ == "__main__":
    unittest.main()
