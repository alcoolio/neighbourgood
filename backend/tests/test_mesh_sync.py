"""Tests for the BLE mesh sync endpoint."""

import uuid


def _mesh_msg(msg_type="emergency_ticket", community_id=1, data=None):
    """Helper to build a mesh message payload."""
    return {
        "ng": 1,
        "type": msg_type,
        "community_id": community_id,
        "sender_name": "Test User",
        "ts": 1709337600000,
        "id": str(uuid.uuid4()),
        "data": data or {},
    }


# ── Auth required ─────────────────────────────────────────────────


def test_sync_requires_auth(client):
    res = client.post("/mesh/sync", json={"messages": []})
    assert res.status_code == 403


# ── Empty sync ────────────────────────────────────────────────────


def test_sync_empty_messages(client, auth_headers):
    res = client.post("/mesh/sync", json={"messages": []}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["synced"] == 0
    assert data["duplicates"] == 0
    assert data["errors"] == 0


# ── Sync emergency ticket ────────────────────────────────────────


def test_sync_emergency_ticket(client, auth_headers, community_id):
    msg = _mesh_msg(
        community_id=community_id,
        data={
            "title": "Need water supplies",
            "description": "Flooding in sector 4",
            "ticket_type": "request",
            "urgency": "high",
        },
    )
    res = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["synced"] == 1
    assert data["duplicates"] == 0
    assert data["errors"] == 0

    # Verify ticket was created
    tickets_res = client.get(
        f"/communities/{community_id}/tickets", headers=auth_headers
    )
    assert tickets_res.status_code == 200
    items = tickets_res.json()["items"]
    assert any(t["title"] == "Need water supplies" for t in items)


# ── Deduplication ─────────────────────────────────────────────────


def test_sync_deduplication(client, auth_headers, community_id):
    msg = _mesh_msg(
        community_id=community_id,
        data={
            "title": "Duplicate test",
            "ticket_type": "offer",
            "urgency": "low",
        },
    )
    # First sync
    res1 = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    assert res1.json()["synced"] == 1

    # Second sync with same message ID
    res2 = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    data2 = res2.json()
    assert data2["synced"] == 0
    assert data2["duplicates"] == 1


# ── Crisis vote sync ─────────────────────────────────────────────


def test_sync_crisis_vote(client, auth_headers, community_id):
    msg = _mesh_msg(
        msg_type="crisis_vote",
        community_id=community_id,
        data={"vote_type": "activate"},
    )
    res = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["synced"] == 1

    # Verify vote was recorded
    status_res = client.get(f"/communities/{community_id}/crisis/status")
    assert status_res.status_code == 200
    assert status_res.json()["votes_to_activate"] >= 1


# ── Non-member community ─────────────────────────────────────────


def test_sync_non_member_community(client, auth_headers):
    """Messages for communities the user isn't a member of should error."""
    msg = _mesh_msg(
        community_id=99999,
        data={"title": "Test", "ticket_type": "request", "urgency": "low"},
    )
    res = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["errors"] == 1
    assert res.json()["synced"] == 0


# ── Invalid message type ─────────────────────────────────────────


def test_sync_invalid_message_type(client, auth_headers):
    msg = _mesh_msg()
    msg["type"] = "invalid_type"
    res = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    assert res.status_code == 422  # Pydantic validation error


# ── Heartbeat acknowledged but not persisted ─────────────────────


def test_sync_heartbeat_acknowledged(client, auth_headers, community_id):
    msg = _mesh_msg(msg_type="heartbeat", community_id=community_id)
    res = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["synced"] == 1


# ── Missing ticket title ─────────────────────────────────────────


def test_sync_ticket_missing_title(client, auth_headers, community_id):
    msg = _mesh_msg(
        community_id=community_id,
        data={"ticket_type": "request", "urgency": "low"},
    )
    res = client.post(
        "/mesh/sync", json={"messages": [msg]}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["errors"] == 1


# ── Multiple messages batch ──────────────────────────────────────


def test_sync_batch_messages(client, auth_headers, community_id):
    msgs = [
        _mesh_msg(
            community_id=community_id,
            data={
                "title": f"Batch ticket {i}",
                "ticket_type": "request",
                "urgency": "medium",
            },
        )
        for i in range(5)
    ]
    res = client.post(
        "/mesh/sync", json={"messages": msgs}, headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["synced"] == 5
    assert data["duplicates"] == 0
    assert data["errors"] == 0
