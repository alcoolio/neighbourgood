"""Tests for authentication endpoints."""


def test_register_success(client):
    res = client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "password": "Secret123",
            "display_name": "New User",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "Secret123",
        "display_name": "Dup User",
    }
    client.post("/auth/register", json=payload)
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 409


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "Mypassword1",
            "display_name": "Login User",
        },
    )
    res = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "Mypassword1"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "Correct123",
            "display_name": "Wrong Pass",
        },
    )
    res = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "Incorrect1"},
    )
    assert res.status_code == 401
