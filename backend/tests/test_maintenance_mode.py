import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings

client = TestClient(app)


class TestMaintenanceMode(unittest.TestCase):
    def test_maintenance_mode_disabled(self):
        """When MAINTENANCE_MODE is False, endpoints behave normally."""
        with patch.object(settings, "MAINTENANCE_MODE", False):
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)

            response = client.get("/api/maintenance/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertFalse(data["maintenance"])

    def test_maintenance_mode_enabled_public_endpoints(self):
        """When MAINTENANCE_MODE is True, public whitelisted endpoints remain accessible."""
        with patch.object(settings, "MAINTENANCE_MODE", True), patch.object(
            settings, "MAINTENANCE_END", "2026-08-09T18:00:00Z"
        ):
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)

            response = client.get("/api/maintenance/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertTrue(data["maintenance"])
            self.assertEqual(data["maintenance_end"], "2026-08-09T18:00:00Z")

    def test_maintenance_mode_enabled_protected_endpoints(self):
        """When MAINTENANCE_MODE is True, protected endpoints return HTTP 503 with maintenance payload."""
        with patch.object(settings, "MAINTENANCE_MODE", True), patch.object(
            settings, "MAINTENANCE_ADMIN_BYPASS", False
        ), patch.object(settings, "MAINTENANCE_END", "2026-08-09T18:00:00Z"):
            response = client.get("/api/emails")
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertFalse(data["success"])
            self.assertTrue(data["maintenance"])
            self.assertTrue(
                "maintenance" in data["message"].lower()
                or "scheduled" in data["message"].lower()
            )
            self.assertEqual(data["maintenance_end"], "2026-08-09T18:00:00Z")

            response = client.post(
                "/auth/login",
                json={"email": "user@example.com", "password": "password123"},
            )
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertTrue(data["maintenance"])

    def test_maintenance_admin_bypass(self):
        """When MAINTENANCE_ADMIN_BYPASS is True, admin emails bypass maintenance on login/requests."""
        with patch.object(settings, "MAINTENANCE_MODE", True), patch.object(
            settings, "MAINTENANCE_ADMIN_BYPASS", True
        ), patch.object(
            settings, "MAINTENANCE_ADMIN_EMAILS", ["admin@mailsentry.com"]
        ):
            response = client.post(
                "/auth/login",
                json={"email": "admin@mailsentry.com", "password": "wrongpassword"},
            )
            self.assertNotEqual(response.status_code, 503)

            response = client.post(
                "/auth/login",
                json={"email": "regular@example.com", "password": "password123"},
            )
            self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()

