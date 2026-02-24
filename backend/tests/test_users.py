"""Tests for user profile endpoints."""


def test_get_my_profile(client, auth_headers):
    res = client.get("/users/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert data["neighbourhood"] == "Testville"
    assert data["role"] == "member"


def test_update_my_profile(client, auth_headers):
    res = client.patch(
        "/users/me",
        headers=auth_headers,
        json={"display_name": "Updated Name"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["display_name"] == "Updated Name"
    assert data["neighbourhood"] == "Testville"


def test_profile_requires_auth(client):
    res = client.get("/users/me")
    assert res.status_code == 403
