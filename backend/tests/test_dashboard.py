import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService
from app.utils.main_utile import create_access_token
from main import app

USER_ID_A = "507f1f77bcf86cd799439011"
USER_ID_B = "507f1f77bcf86cd799439022"


class TestDashboardRepository(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_col = MagicMock()
        self.mock_db.__getitem__.return_value = self.mock_col
        self.repo = DashboardRepository(db=self.mock_db)

    def test_ensure_indexes(self):
        """Verifies indexes are created on collection."""
        self.repo.ensure_indexes()
        self.assertGreaterEqual(self.mock_col.create_index.call_count, 3)

    def test_get_user_stats_empty_collection(self):
        """Returns default zero stats when user has no predictions."""
        self.mock_col.aggregate.return_value = []
        stats = self.repo.get_user_stats(USER_ID_A)

        self.assertEqual(stats["total_predictions"], 0)
        self.assertEqual(stats["spam_emails"], 0)
        self.assertEqual(stats["safe_emails"], 0)
        self.assertEqual(stats["spam_percentage"], 0.0)
        self.assertEqual(stats["safe_percentage"], 0.0)
        self.assertEqual(stats["average_confidence"], 0.0)
        self.assertEqual(stats["growth_percentage"], 0.0)

    def test_get_user_stats_with_data(self):
        """Verifies aggregation pipeline calculations for totals, percentages, confidence, and growth."""
        facet_mock_result = [
            {
                "totals": [{"total": 100, "spam": 30, "safe": 70, "avg_score": 0.95}],
                "today": [{"count": 10}],
                "this_week": [{"count": 40}],
                "last_week": [{"count": 20}],
            }
        ]
        self.mock_col.aggregate.return_value = facet_mock_result

        stats = self.repo.get_user_stats(USER_ID_A)

        self.assertEqual(stats["total_predictions"], 100)
        self.assertEqual(stats["spam_emails"], 30)
        self.assertEqual(stats["safe_emails"], 70)
        self.assertEqual(stats["spam_percentage"], 30.0)
        self.assertEqual(stats["safe_percentage"], 70.0)
        self.assertEqual(stats["average_confidence"], 95.0)
        self.assertEqual(stats["today_predictions"], 10)
        self.assertEqual(stats["this_week_predictions"], 40)
        self.assertEqual(stats["last_week_predictions"], 20)
        self.assertEqual(stats["growth_percentage"], 100.0)  # ((40 - 20) / 20) * 100

    def test_get_user_stats_zero_last_week(self):
        """When last_week_predictions is 0, growth_percentage should be None."""
        facet_mock_result = [
            {
                "totals": [{"total": 10, "spam": 2, "safe": 8, "avg_score": 0.90}],
                "today": [{"count": 2}],
                "this_week": [{"count": 10}],
                "last_week": [],
            }
        ]
        self.mock_col.aggregate.return_value = facet_mock_result

        stats = self.repo.get_user_stats(USER_ID_A)

        self.assertEqual(stats["total_predictions"], 10)
        self.assertEqual(stats["this_week_predictions"], 10)
        self.assertEqual(stats["last_week_predictions"], 0)
        self.assertIsNone(stats["growth_percentage"])


class TestDashboardService(unittest.TestCase):

    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = DashboardService(repo=self.mock_repo)

    def test_get_dashboard_stats(self):
        self.mock_repo.get_user_stats.return_value = {
            "total_predictions": 50,
            "spam_emails": 10,
            "safe_emails": 40,
            "accuracy": None,
            "average_confidence": 92.5,
            "today_predictions": 5,
            "last_week_predictions": 15,
            "this_week_predictions": 25,
            "spam_percentage": 20.0,
            "safe_percentage": 80.0,
            "growth_percentage": 66.7,
        }

        res = self.service.get_dashboard_stats(USER_ID_A)
        self.assertEqual(res.total_predictions, 50)
        self.assertEqual(res.spam_emails, 10)
        self.assertEqual(res.safe_emails, 40)
        self.assertEqual(res.average_confidence, 92.5)
        self.assertEqual(res.spam_percentage, 20.0)
        self.assertEqual(res.safe_percentage, 80.0)


class TestDashboardApiEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.token = create_access_token(user_id=USER_ID_A, username="user_a")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_stats_unauthorized(self):
        """Returns 401 Unauthorized when no JWT token is provided."""
        res = self.client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 401)

    @patch("app.api.dashboard_routes.DashboardService")
    def test_get_stats_success(self, MockServiceClass):
        """Returns 200 OK with formatted stats data for authenticated user."""
        app.dependency_overrides[get_current_user] = lambda: {
            "_id": USER_ID_A,
            "username": "user_a",
        }

        mock_service_instance = MagicMock()
        MockServiceClass.return_value = mock_service_instance

        from app.schemas.dashboard import DashboardStatsResponse

        mock_stats = DashboardStatsResponse(
            total_predictions=1284,
            spam_emails=317,
            safe_emails=967,
            accuracy=None,
            average_confidence=98.4,
            today_predictions=18,
            last_week_predictions=1142,
            this_week_predictions=1284,
            spam_percentage=24.7,
            safe_percentage=75.3,
            growth_percentage=12.4,
        )
        mock_service_instance.get_dashboard_stats.return_value = mock_stats

        res = self.client.get("/api/dashboard/stats", headers=self.headers)
        self.assertEqual(res.status_code, 200)

        json_resp = res.json()
        self.assertTrue(json_resp.get("success"))
        data = json_resp.get("data")
        self.assertEqual(data["total_predictions"], 1284)
        self.assertEqual(data["spam_emails"], 317)
        self.assertEqual(data["safe_emails"], 967)
        self.assertEqual(data["average_confidence"], 98.4)
        self.assertEqual(data["spam_percentage"], 24.7)
        self.assertEqual(data["safe_percentage"], 75.3)
        self.assertEqual(data["growth_percentage"], 12.4)
        MockServiceClass.return_value.get_dashboard_stats.assert_called_once_with(
            USER_ID_A
        )


if __name__ == "__main__":
    unittest.main()
