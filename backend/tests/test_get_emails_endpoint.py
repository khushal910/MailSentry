import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from app.dependencies.auth import get_current_user
from app.utils.main_utile import create_access_token


USER_ID = "507f1f77bcf86cd799439011"

MOCK_EMAILS = [
    {
        "_id": "doc_1",
        "user_id": USER_ID,
        "message_id": "msg_001",
        "thread_id": "thread_001",
        "subject": "Limited time offer!",
        "snippet": "Click here to claim your prize",
        "predicted_label": "spam",
        "predicted_score": 0.97,
        "fetch_time": datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
        "classified_at": datetime(2026, 8, 1, 10, 1, 0, tzinfo=timezone.utc),
        "refresh_token": "SENSITIVE_TOKEN_SHOULD_NOT_APPEAR",
    },
    {
        "_id": "doc_2",
        "user_id": USER_ID,
        "message_id": "msg_002",
        "thread_id": None,
        "subject": "Team standup notes",
        "snippet": "Please find today's notes attached",
        "predicted_label": "important",
        "predicted_score": 0.88,
        "fetch_time": datetime(2026, 8, 1, 9, 0, 0, tzinfo=timezone.utc),
        "classified_at": datetime(2026, 8, 1, 9, 1, 0, tzinfo=timezone.utc),
    },
]


class TestGetEmailsEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.token = create_access_token(user_id=USER_ID, username="testuser")
        self.mock_user = {"_id": USER_ID, "username": "testuser"}

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_emails_unauthorized_without_jwt(self):
        """Returns 401 Unauthorized when no JWT token is provided."""
        response = self.client.get("/api/emails")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication required", response.json().get("detail", ""))

    @patch("app.api.emails.EmailRepository")
    def test_get_emails_returns_list_when_emails_exist(self, MockRepo):
        """Returns 200 OK with emails list when emails exist for user."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        MockRepo.return_value.get_user_emails.return_value = MOCK_EMAILS

        response = self.client.get(
            "/api/emails",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["message"], "Emails retrieved successfully")
        emails = body["data"]["emails"]
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails[0]["message_id"], "msg_001")
        self.assertEqual(emails[0]["predicted_label"], "spam")

    @patch("app.api.emails.EmailRepository")
    def test_get_emails_strips_sensitive_fields(self, MockRepo):
        """Response MUST NOT include sensitive fields like refresh_token, user_id, _id."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        MockRepo.return_value.get_user_emails.return_value = MOCK_EMAILS

        response = self.client.get(
            "/api/emails",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        emails = response.json()["data"]["emails"]
        for email in emails:
            self.assertNotIn("refresh_token", email)
            self.assertNotIn("_id", email)
            self.assertNotIn("user_id", email)
            self.assertNotIn("body", email)

    @patch("app.api.emails.EmailRepository")
    def test_get_emails_returns_empty_array_when_no_emails(self, MockRepo):
        """Returns empty list [] when no emails found for user."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        MockRepo.return_value.get_user_emails.return_value = []

        response = self.client.get(
            "/api/emails",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["emails"], [])

    def test_get_emails_invalid_limit_too_low_returns_400(self):
        """Returns 422 for invalid limit (0 or negative)."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        response = self.client.get(
            "/api/emails?limit=0",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertIn(response.status_code, [400, 422])

    def test_get_emails_invalid_page_returns_400(self):
        """Returns 422 for invalid page (0 or negative)."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        response = self.client.get(
            "/api/emails?page=0",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertIn(response.status_code, [400, 422])

    def test_get_emails_limit_exceeds_max_returns_400(self):
        """Returns 422 when limit exceeds max of 100."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        response = self.client.get(
            "/api/emails?limit=200",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertIn(response.status_code, [400, 422])

    @patch("app.api.emails.EmailRepository")
    def test_get_emails_pagination_parameters_forwarded(self, MockRepo):
        """Verifies correct skip and limit are passed to the repository."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        MockRepo.return_value.get_user_emails.return_value = []

        response = self.client.get(
            "/api/emails?limit=5&page=3",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(response.status_code, 200)
        MockRepo.return_value.get_user_emails.assert_called_once_with(
            user_id=USER_ID,
            predicted_label=None,
            limit=5,
            skip=10  # (page-1) * limit = 2 * 5 = 10
        )

    @patch("app.api.emails.EmailRepository")
    def test_get_emails_filter_by_label(self, MockRepo):
        """Verifies label filter is passed to the repository."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        MockRepo.return_value.get_user_emails.return_value = [MOCK_EMAILS[0]]

        response = self.client.get(
            "/api/emails?label=spam",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(response.status_code, 200)
        MockRepo.return_value.get_user_emails.assert_called_once_with(
            user_id=USER_ID,
            predicted_label="spam",
            limit=20,
            skip=0
        )


    @patch("app.api.emails.EmailRepository")
    def test_get_emails_returns_total_count(self, MockRepo):
        """Verifies total_count is returned in response data for correct multi-page pagination."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        MockRepo.return_value.get_user_emails.return_value = [MOCK_EMAILS[0]]
        MockRepo.return_value.count_user_emails.return_value = 50

        response = self.client.get(
            "/api/emails?limit=10&page=1",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["total_count"], 50)
        self.assertEqual(data["total"], 50)

    @patch("app.api.emails.EmailRepository")
    def test_get_emails_search_parameter_forwarded(self, MockRepo):
        """Verifies search parameter is forwarded to repository."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        MockRepo.return_value.get_user_emails.return_value = [MOCK_EMAILS[0]]
        MockRepo.return_value.count_user_emails.return_value = 1

        response = self.client.get(
            "/api/emails?search=khushal",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(response.status_code, 200)
        MockRepo.return_value.get_user_emails.assert_called_once_with(
            user_id=USER_ID,
            predicted_label=None,
            search="khushal",
            limit=20,
            skip=0
        )
        MockRepo.return_value.count_user_emails.assert_called_once_with(
            user_id=USER_ID,
            predicted_label=None,
            search="khushal"
        )


if __name__ == "__main__":
    unittest.main()
