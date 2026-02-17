"""Tests for the /status endpoint."""


def test_status_returns_ok(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["mode"] in ("blue", "red")
