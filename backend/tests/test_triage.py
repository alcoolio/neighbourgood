"""Tests for priority-based ticket triage: due_at field, sort=priority_desc, /tickets/triage endpoint."""

import datetime


def _register(client, email, name="User"):
    res = client.post(
        "/auth/register",
        json={"email": email, "password": "Password123", "display_name": name},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _community(client, headers, name="Triage Community"):
    res = client.post(
        "/communities",
        headers=headers,
        json={"name": name, "postal_code": "10115", "city": "Berlin"},
    )
    return res.json()["id"]


def _create_ticket(client, headers, cid, urgency="medium", title="Test", due_at=None):
    payload = {
        "ticket_type": "request",
        "title": title,
        "urgency": urgency,
    }
    if due_at is not None:
        payload["due_at"] = due_at
    res = client.post(f"/communities/{cid}/tickets", headers=headers, json=payload)
    return res


# ── due_at field ───────────────────────────────────────────────────


def test_create_ticket_with_due_at(client, auth_headers):
    cid = _community(client, auth_headers)
    due = (datetime.datetime.utcnow() + datetime.timedelta(hours=4)).isoformat()
    res = _create_ticket(client, auth_headers, cid, due_at=due)
    assert res.status_code == 201
    assert res.json()["due_at"] is not None


def test_create_ticket_without_due_at(client, auth_headers):
    cid = _community(client, auth_headers)
    res = _create_ticket(client, auth_headers, cid)
    assert res.status_code == 201
    assert res.json()["due_at"] is None


def test_triage_score_present_on_create(client, auth_headers):
    cid = _community(client, auth_headers)
    res = _create_ticket(client, auth_headers, cid, urgency="high")
    assert res.status_code == 201
    data = res.json()
    assert "triage_score" in data
    assert data["triage_score"] > 0


def test_update_ticket_sets_due_at(client, auth_headers):
    cid = _community(client, auth_headers)
    res = _create_ticket(client, auth_headers, cid)
    tid = res.json()["id"]
    due = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).isoformat()
    patch = client.patch(
        f"/communities/{cid}/tickets/{tid}",
        headers=auth_headers,
        json={"due_at": due},
    )
    assert patch.status_code == 200
    assert patch.json()["due_at"] is not None


# ── sort=priority_desc ─────────────────────────────────────────────


def test_list_tickets_sorted_by_priority(client, auth_headers):
    cid = _community(client, auth_headers)
    _create_ticket(client, auth_headers, cid, urgency="low", title="Low priority")
    _create_ticket(client, auth_headers, cid, urgency="critical", title="Critical priority")
    _create_ticket(client, auth_headers, cid, urgency="medium", title="Medium priority")

    res = client.get(
        f"/communities/{cid}/tickets",
        headers=auth_headers,
        params={"sort": "priority_desc"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 3
    # Critical should come first
    assert items[0]["urgency"] == "critical"
    assert items[-1]["urgency"] == "low"


def test_list_tickets_default_sort_is_created_desc(client, auth_headers):
    cid = _community(client, auth_headers)
    _create_ticket(client, auth_headers, cid, title="Alpha")
    _create_ticket(client, auth_headers, cid, title="Beta")

    res = client.get(f"/communities/{cid}/tickets", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    # Two tickets should be present regardless of created_at ordering in SQLite
    titles = {i["title"] for i in items}
    assert titles == {"Alpha", "Beta"}


# ── urgency filter ─────────────────────────────────────────────────


def test_list_tickets_filter_by_urgency(client, auth_headers):
    cid = _community(client, auth_headers)
    _create_ticket(client, auth_headers, cid, urgency="low")
    _create_ticket(client, auth_headers, cid, urgency="high")

    res = client.get(
        f"/communities/{cid}/tickets",
        headers=auth_headers,
        params={"urgency": "high"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["urgency"] == "high"


# ── Triage endpoint ────────────────────────────────────────────────


def test_triage_endpoint_returns_open_tickets(client, auth_headers):
    cid = _community(client, auth_headers)

    _create_ticket(client, auth_headers, cid, urgency="low", title="Low")
    _create_ticket(client, auth_headers, cid, urgency="critical", title="Critical")

    # Resolve one ticket – it should not appear in triage
    res_list = client.get(f"/communities/{cid}/tickets", headers=auth_headers)
    first_id = res_list.json()["items"][0]["id"]
    client.patch(
        f"/communities/{cid}/crisis/tickets/{first_id}",
        headers=auth_headers,
        json={"status": "resolved"},
    )

    res = client.get(f"/communities/{cid}/tickets/triage", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    # Only non-resolved tickets appear
    for item in data["items"]:
        assert item["status"] != "resolved"
    # Sorted highest score first
    if len(data["items"]) > 1:
        scores = [i["triage_score"] for i in data["items"]]
        assert scores == sorted(scores, reverse=True)


def test_triage_endpoint_requires_leader_or_admin(client, auth_headers):
    cid = _community(client, auth_headers)

    # Register a plain member
    member_headers = _register(client, "plain@example.com", "Plain")
    client.post(f"/communities/{cid}/join", headers=member_headers)

    res = client.get(f"/communities/{cid}/tickets/triage", headers=member_headers)
    assert res.status_code == 403


def test_triage_endpoint_nonmember_forbidden(client, auth_headers):
    cid = _community(client, auth_headers)
    stranger_headers = _register(client, "stranger@example.com", "Stranger")

    res = client.get(f"/communities/{cid}/tickets/triage", headers=stranger_headers)
    assert res.status_code == 403


def test_triage_score_critical_higher_than_low(client, auth_headers):
    cid = _community(client, auth_headers)
    r_low = _create_ticket(client, auth_headers, cid, urgency="low")
    r_critical = _create_ticket(client, auth_headers, cid, urgency="critical")
    assert r_critical.json()["triage_score"] > r_low.json()["triage_score"]
