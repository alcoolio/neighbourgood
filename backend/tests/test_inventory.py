"""Tests for resource inventory tracking (quantity fields and /inventory endpoint)."""


def _create_resource(client, headers, community_id, **kwargs):
    payload = {
        "title": "Test Resource",
        "category": "tool",
        "condition": "good",
        "community_id": community_id,
    }
    payload.update(kwargs)
    return client.post("/resources", headers=headers, json=payload)


# ── Creation with inventory fields ─────────────────────────────────


def test_create_resource_default_inventory(client, auth_headers, community_id):
    res = _create_resource(client, auth_headers, community_id)
    assert res.status_code == 201
    data = res.json()
    assert data["quantity_total"] == 1
    assert data["quantity_available"] == 1
    assert data["reorder_threshold"] is None
    assert data["low_stock"] is False


def test_create_resource_custom_quantity(client, auth_headers, community_id):
    res = _create_resource(
        client, auth_headers, community_id,
        quantity_total=5,
        reorder_threshold=2,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["quantity_total"] == 5
    assert data["quantity_available"] == 5  # starts fully stocked
    assert data["reorder_threshold"] == 2
    assert data["low_stock"] is False  # 5 > threshold 2


def test_create_resource_invalid_quantity(client, auth_headers, community_id):
    res = _create_resource(client, auth_headers, community_id, quantity_total=0)
    assert res.status_code == 422


# ── Inventory update endpoint ──────────────────────────────────────


def test_update_inventory_reduces_available(client, auth_headers, community_id):
    r = _create_resource(client, auth_headers, community_id, quantity_total=10)
    rid = r.json()["id"]

    res = client.patch(f"/resources/{rid}/inventory", headers=auth_headers, json={"quantity_available": 3})
    assert res.status_code == 200
    data = res.json()
    assert data["quantity_available"] == 3
    assert data["quantity_total"] == 10
    assert data["is_available"] is True


def test_update_inventory_zero_marks_unavailable(client, auth_headers, community_id):
    r = _create_resource(client, auth_headers, community_id, quantity_total=5)
    rid = r.json()["id"]

    res = client.patch(f"/resources/{rid}/inventory", headers=auth_headers, json={"quantity_available": 0})
    assert res.status_code == 200
    data = res.json()
    assert data["quantity_available"] == 0
    assert data["is_available"] is False


def test_update_inventory_restores_availability(client, auth_headers, community_id):
    r = _create_resource(client, auth_headers, community_id, quantity_total=5)
    rid = r.json()["id"]

    client.patch(f"/resources/{rid}/inventory", headers=auth_headers, json={"quantity_available": 0})
    res = client.patch(f"/resources/{rid}/inventory", headers=auth_headers, json={"quantity_available": 2})
    assert res.status_code == 200
    assert res.json()["is_available"] is True


def test_update_inventory_exceeds_total(client, auth_headers, community_id):
    r = _create_resource(client, auth_headers, community_id, quantity_total=3)
    rid = r.json()["id"]

    res = client.patch(f"/resources/{rid}/inventory", headers=auth_headers, json={"quantity_available": 10})
    assert res.status_code == 422


def test_update_inventory_not_owner(client, auth_headers, community_id):
    r = _create_resource(client, auth_headers, community_id)
    rid = r.json()["id"]

    # Register a second user and attempt to adjust inventory
    res2 = client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "Otherpass1", "display_name": "Other"},
    )
    other_headers = {"Authorization": f"Bearer {res2.json()['access_token']}"}

    res = client.patch(f"/resources/{rid}/inventory", headers=other_headers, json={"quantity_available": 0})
    assert res.status_code == 403


def test_update_inventory_not_found(client, auth_headers):
    res = client.patch("/resources/9999/inventory", headers=auth_headers, json={"quantity_available": 0})
    assert res.status_code == 404


# ── Low-stock flag ─────────────────────────────────────────────────


def test_low_stock_flag_triggered(client, auth_headers, community_id):
    r = _create_resource(
        client, auth_headers, community_id,
        quantity_total=10,
        reorder_threshold=3,
    )
    rid = r.json()["id"]

    # Reduce to exactly the threshold – should flag low stock
    res = client.patch(f"/resources/{rid}/inventory", headers=auth_headers, json={"quantity_available": 3})
    assert res.json()["low_stock"] is True


def test_low_stock_flag_not_triggered(client, auth_headers, community_id):
    r = _create_resource(
        client, auth_headers, community_id,
        quantity_total=10,
        reorder_threshold=3,
    )
    rid = r.json()["id"]

    res = client.patch(f"/resources/{rid}/inventory", headers=auth_headers, json={"quantity_available": 4})
    assert res.json()["low_stock"] is False


def test_inventory_fields_in_list(client, auth_headers, community_id):
    _create_resource(client, auth_headers, community_id, quantity_total=7)
    res = client.get("/resources")
    assert res.status_code == 200
    item = res.json()["items"][0]
    assert "quantity_total" in item
    assert "quantity_available" in item
    assert "low_stock" in item
