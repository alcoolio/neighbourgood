"""Tests for the /status endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_status_returns_ok():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["mode"] in ("blue", "red")
