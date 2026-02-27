"""Tests for generic outbound webhook CRUD endpoints."""

import json


def test_list_webhooks_empty(client, auth_headers):
    res = client.get("/webhooks", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_create_webhook(client, auth_headers):
    res = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/hook",
            "secret": "supersecret123",
            "event_types": ["message.new", "booking.created"],
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["url"] == "https://example.com/hook"
    assert "message.new" in data["event_types"]
    assert "booking.created" in data["event_types"]
    assert data["is_active"] is True
    assert "id" in data


def test_list_webhooks_after_create(client, auth_headers):
    client.post(
        "/webhooks",
        json={
            "url": "https://example.com/hook",
            "secret": "supersecret123",
            "event_types": ["resource.shared"],
        },
        headers=auth_headers,
    )
    res = client.get("/webhooks", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_create_webhook_invalid_event_type(client, auth_headers):
    res = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/hook",
            "secret": "supersecret123",
            "event_types": ["not.a.real.event"],
        },
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_create_webhook_empty_event_types(client, auth_headers):
    res = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/hook",
            "secret": "supersecret123",
            "event_types": [],
        },
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_delete_webhook(client, auth_headers):
    create_res = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/hook",
            "secret": "supersecret123",
            "event_types": ["message.new"],
        },
        headers=auth_headers,
    )
    webhook_id = create_res.json()["id"]

    del_res = client.delete(f"/webhooks/{webhook_id}", headers=auth_headers)
    assert del_res.status_code == 204

    list_res = client.get("/webhooks", headers=auth_headers)
    assert list_res.json() == []


def test_delete_webhook_not_found(client, auth_headers):
    res = client.delete("/webhooks/99999", headers=auth_headers)
    assert res.status_code == 404


def test_delete_webhook_other_user(client, auth_headers):
    create_res = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/hook",
            "secret": "supersecret123",
            "event_types": ["message.new"],
        },
        headers=auth_headers,
    )
    webhook_id = create_res.json()["id"]

    # Register a second user
    client.post(
        "/auth/register",
        json={
            "email": "other@example.com",
            "password": "Otherpass123",
            "display_name": "Other User",
        },
    )
    login = client.post("/auth/login", json={"email": "other@example.com", "password": "Otherpass123"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    res = client.delete(f"/webhooks/{webhook_id}", headers=other_headers)
    assert res.status_code == 403


def test_webhooks_unauthenticated(client):
    res = client.get("/webhooks")
    assert res.status_code == 403
