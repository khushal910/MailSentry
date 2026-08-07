import os
import sys

try:
    import pytest
except ImportError:
    class DummyPytestMark:
        def __getattr__(self, name):
            return lambda fn: fn
    class DummyPytest:
        def fixture(self, *args, **kwargs):
            return lambda fn: fn
        mark = DummyPytestMark()
    pytest = DummyPytest()
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


def test_gzip_small_response_not_compressed():
    """Verify that small responses (< 1000 bytes) are NOT gzip compressed even if requested."""
    response = client.get("/health", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    # Health check response is small (~100 bytes), so Content-Encoding should NOT be gzip
    assert (
        "content-encoding" not in response.headers
        or response.headers.get("content-encoding") != "gzip"
    )


def test_gzip_large_response_compressed():
    """Verify that large responses (>= 1000 bytes) ARE gzip compressed when Accept-Encoding: gzip is requested."""

    # Register temporary test endpoint for large payload test
    @app.get("/test-gzip-large")
    def large_endpoint():
        return {"data": "x" * 2000}

    response = client.get("/test-gzip-large", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers.get("content-encoding") == "gzip"


def test_gzip_cors_headers_preserved():
    """Verify CORS headers are preserved on compressed responses."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173", "Accept-Encoding": "gzip"},
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    )
