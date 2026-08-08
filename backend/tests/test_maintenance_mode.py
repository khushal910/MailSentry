import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings

client = TestClient(app)


def test_maintenance_mode_disabled(monkeypatch):
    """When MAINTENANCE_MODE is False, endpoints behave normally."""
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", False)

    # Health check endpoint
    response = client.get("/health")
    assert response.status_code == 200

    # Maintenance status endpoint
    response = client.get("/api/maintenance/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["maintenance"] is False


def test_maintenance_mode_enabled_public_endpoints(monkeypatch):
    """When MAINTENANCE_MODE is True, public whitelisted endpoints remain accessible."""
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    monkeypatch.setattr(settings, "MAINTENANCE_END", "2026-08-09T18:00:00Z")

    response = client.get("/health")
    assert response.status_code == 200

    response = client.get("/api/maintenance/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["maintenance"] is True
    assert data["maintenance_end"] == "2026-08-09T18:00:00Z"


def test_maintenance_mode_enabled_protected_endpoints(monkeypatch):
    """When MAINTENANCE_MODE is True, protected endpoints return HTTP 503 with maintenance payload."""
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    monkeypatch.setattr(settings, "MAINTENANCE_ADMIN_BYPASS", False)
    monkeypatch.setattr(settings, "MAINTENANCE_END", "2026-08-09T18:00:00Z")

    # Protected endpoint attempt
    response = client.get("/api/emails")
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert data["maintenance"] is True
    assert "maintenance" in data["message"].lower() or "scheduled" in data["message"].lower()
    assert data["maintenance_end"] == "2026-08-09T18:00:00Z"

    # Login endpoint attempt during maintenance
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert response.status_code == 503
    data = response.json()
    assert data["maintenance"] is True


def test_maintenance_admin_bypass(monkeypatch):
    """When MAINTENANCE_ADMIN_BYPASS is True, admin emails bypass maintenance on login/requests."""
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    monkeypatch.setattr(settings, "MAINTENANCE_ADMIN_BYPASS", True)
    monkeypatch.setattr(settings, "MAINTENANCE_ADMIN_EMAILS", ["admin@mailsentry.com"])

    # Admin email attempt on login endpoint
    response = client.post("/auth/login", json={"email": "admin@mailsentry.com", "password": "wrongpassword"})
    # Should proceed past maintenance middleware to controller (returning 401 for invalid credentials rather than 503 maintenance)
    assert response.status_code != 503

    # Regular user email attempt on login endpoint
    response = client.post("/auth/login", json={"email": "regular@example.com", "password": "password123"})
    assert response.status_code == 503
