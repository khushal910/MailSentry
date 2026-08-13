import unittest
from unittest.mock import patch, PropertyMock
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings


class TestMLServiceAPIRouter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {}
        if settings.API_KEY_SECRET:
            self.headers["X-Internal-Token"] = settings.API_KEY_SECRET

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertTrue(data.get("model_loaded"))
        self.assertIn("version", data)

    @patch("app.services.ml_engine.MLEngine.is_loaded", new_callable=PropertyMock)
    def test_health_endpoint_unhealthy_when_model_not_loaded(self, mock_is_loaded):
        mock_is_loaded.return_value = False
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data.get("status"), "unhealthy")
        self.assertFalse(data.get("model_loaded"))

    def test_ready_endpoint(self):
        response = self.client.get("/ready")
        self.assertIn(response.status_code, [200, 503])
        data = response.json()
        if response.status_code == 200:
            self.assertEqual(data.get("status"), "ready")
            self.assertIn("model_version", data)

    def test_ready_endpoint_alias_v1(self):
        response = self.client.get("/api/v1/ready")
        self.assertIn(response.status_code, [200, 503])

    def test_version_endpoint(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("model_version", data)
        self.assertIn("model_type", data)

    def test_predict_endpoint_success(self):
        payload = {
            "subject": "Account Security Alert",
            "body": "Your password has been compromised. Click http://verify.xyz to reset immediately."
        }
        response = self.client.post("/predict", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("predicted_label", data)
        self.assertIn("predicted_score", data)
        self.assertEqual(data.get("subject"), "Account Security Alert")

    def test_predict_endpoint_alias_v1(self):
        payload = {
            "subject": "Project Status Update",
            "body": "Meeting is scheduled for 3 PM tomorrow."
        }
        response = self.client.post("/api/v1/predict", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("predicted_label", data)

    def test_predict_endpoint_empty_payload(self):
        response = self.client.post("/predict", json={}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("predicted_label", data)

    def test_predict_endpoint_malformed_json(self):
        response = self.client.post(
            "/predict",
            headers={"Content-Type": "application/json", **self.headers},
            content="invalid json {"
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
