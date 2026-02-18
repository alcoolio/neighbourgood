"""Tests for community endpoints: CRUD, membership, search, merge, suggestions."""


def _register(client, email, name="User"):
    """Helper: register a user and return auth headers."""
    res = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": name,
        },
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_community(client, headers, name="Nachbarschaft Mitte", plz="10115", city="Berlin"):
    """Helper: create a community and return its data."""
    res = client.post(
        "/communities",
        headers=headers,
        json={
            "name": name,
            "description": f"Community in {city}",
            "postal_code": plz,
            "city": city,
        },
    )
    return res.json()


# ── Create ─────────────────────────────────────────────────────────


def test_create_community(client, auth_headers):
    res = client.post(
        "/communities",
        headers=auth_headers,
        json={
            "name": "Kiez Kreuzberg",
            "description": "Sharing in Kreuzberg",
            "postal_code": "10999",
            "city": "Berlin",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Kiez Kreuzberg"
    assert data["postal_code"] == "10999"
    assert data["city"] == "Berlin"
    assert data["is_active"] is True
    assert data["member_count"] == 1  # Creator is auto-member


def test_create_community_requires_auth(client):
    res = client.post(
        "/communities",
        json={"name": "Test", "postal_code": "12345", "city": "Berlin"},
    )
    assert res.status_code == 403


# ── Get ────────────────────────────────────────────────────────────


def test_get_community(client, auth_headers):
    created = _create_community(client, auth_headers)
    res = client.get(f"/communities/{created['id']}")
    assert res.status_code == 200
    assert res.json()["name"] == "Nachbarschaft Mitte"


def test_get_community_not_found(client):
    res = client.get("/communities/9999")
    assert res.status_code == 404


# ── Update ─────────────────────────────────────────────────────────


def test_update_community_as_admin(client, auth_headers):
    created = _create_community(client, auth_headers)
    res = client.patch(
        f"/communities/{created['id']}",
        headers=auth_headers,
        json={"name": "Nachbarschaft Mitte (updated)"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Nachbarschaft Mitte (updated)"


def test_update_community_non_admin_forbidden(client, auth_headers):
    created = _create_community(client, auth_headers)
    other = _register(client, "other@test.com", "Other")

    # Join as member
    client.post(f"/communities/{created['id']}/join", headers=other)

    # Try to update as non-admin
    res = client.patch(
        f"/communities/{created['id']}",
        headers=other,
        json={"name": "Hijacked"},
    )
    assert res.status_code == 403


# ── Membership ─────────────────────────────────────────────────────


def test_join_community(client, auth_headers):
    created = _create_community(client, auth_headers)
    other = _register(client, "joiner@test.com", "Joiner")

    res = client.post(f"/communities/{created['id']}/join", headers=other)
    assert res.status_code == 200
    assert res.json()["role"] == "member"


def test_join_community_already_member(client, auth_headers):
    created = _create_community(client, auth_headers)
    other = _register(client, "joiner@test.com", "Joiner")

    client.post(f"/communities/{created['id']}/join", headers=other)
    res = client.post(f"/communities/{created['id']}/join", headers=other)
    assert res.status_code == 409
    assert "Already a member" in res.json()["detail"]


def test_leave_community(client, auth_headers):
    created = _create_community(client, auth_headers)
    other = _register(client, "leaver@test.com", "Leaver")

    client.post(f"/communities/{created['id']}/join", headers=other)
    res = client.delete(f"/communities/{created['id']}/leave", headers=other)
    assert res.status_code == 204


def test_leave_community_not_member(client, auth_headers):
    created = _create_community(client, auth_headers)
    other = _register(client, "stranger@test.com", "Stranger")

    res = client.delete(f"/communities/{created['id']}/leave", headers=other)
    assert res.status_code == 404


def test_list_members(client, auth_headers):
    created = _create_community(client, auth_headers)
    other = _register(client, "member@test.com", "Member")
    client.post(f"/communities/{created['id']}/join", headers=other)

    res = client.get(f"/communities/{created['id']}/members")
    assert res.status_code == 200
    members = res.json()
    assert len(members) == 2
    roles = {m["role"] for m in members}
    assert "admin" in roles
    assert "member" in roles


def test_my_communities(client, auth_headers):
    _create_community(client, auth_headers, name="Group A", plz="10115")
    _create_community(client, auth_headers, name="Group B", plz="10999")

    res = client.get("/communities/my/memberships", headers=auth_headers)
    assert res.status_code == 200
    names = {c["name"] for c in res.json()}
    assert "Group A" in names
    assert "Group B" in names


# ── Search ─────────────────────────────────────────────────────────


def test_search_communities_by_name(client, auth_headers):
    _create_community(client, auth_headers, name="Kiez Kreuzberg", plz="10999", city="Berlin")
    _create_community(client, auth_headers, name="Dorf Gemeinschaft", plz="01234", city="Dresden")

    res = client.get("/communities/search?q=kreuzberg")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Kiez Kreuzberg"


def test_search_communities_by_postal_code(client, auth_headers):
    _create_community(client, auth_headers, name="Group A", plz="10115", city="Berlin")
    _create_community(client, auth_headers, name="Group B", plz="10999", city="Berlin")

    res = client.get("/communities/search?postal_code=10115")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["postal_code"] == "10115"


def test_search_communities_by_city(client, auth_headers):
    _create_community(client, auth_headers, name="Group A", plz="10115", city="Berlin")
    _create_community(client, auth_headers, name="Group B", plz="01234", city="Dresden")

    res = client.get("/communities/search?city=Berlin")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["city"] == "Berlin"


def test_search_all_communities(client, auth_headers):
    _create_community(client, auth_headers, name="Group A", plz="10115", city="Berlin")
    _create_community(client, auth_headers, name="Group B", plz="01234", city="Dresden")

    res = client.get("/communities/search")
    assert res.status_code == 200
    assert res.json()["total"] == 2


# ── Merge ──────────────────────────────────────────────────────────


def test_merge_communities(client, auth_headers):
    source = _create_community(client, auth_headers, name="Small Group", plz="10115", city="Berlin")
    target = _create_community(client, auth_headers, name="Big Group", plz="10115", city="Berlin")

    # Add a unique member to source
    other = _register(client, "source_member@test.com", "SourceMember")
    client.post(f"/communities/{source['id']}/join", headers=other)

    res = client.post(
        "/communities/merge",
        headers=auth_headers,
        json={"source_id": source["id"], "target_id": target["id"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == target["id"]
    # Target should now have: creator (already in both) + source_member = at least 2
    assert data["member_count"] >= 2

    # Source should be inactive and merged
    source_res = client.get(f"/communities/{source['id']}")
    assert source_res.json()["is_active"] is False
    assert source_res.json()["merged_into_id"] == target["id"]


def test_merge_self_fails(client, auth_headers):
    community = _create_community(client, auth_headers)
    res = client.post(
        "/communities/merge",
        headers=auth_headers,
        json={"source_id": community["id"], "target_id": community["id"]},
    )
    assert res.status_code == 422


def test_merge_already_merged_fails(client, auth_headers):
    a = _create_community(client, auth_headers, name="A", plz="10115", city="Berlin")
    b = _create_community(client, auth_headers, name="B", plz="10115", city="Berlin")
    c = _create_community(client, auth_headers, name="C", plz="10115", city="Berlin")

    # Merge A into B
    client.post(
        "/communities/merge",
        headers=auth_headers,
        json={"source_id": a["id"], "target_id": b["id"]},
    )

    # Try to merge A into C (already merged)
    res = client.post(
        "/communities/merge",
        headers=auth_headers,
        json={"source_id": a["id"], "target_id": c["id"]},
    )
    assert res.status_code == 409


def test_merge_non_admin_forbidden(client, auth_headers):
    source = _create_community(client, auth_headers, name="Source", plz="10115", city="Berlin")
    other = _register(client, "nonadmin@test.com", "NonAdmin")
    target = _create_community(client, other, name="Target", plz="10115", city="Berlin")

    # Other is admin of target but not of source
    res = client.post(
        "/communities/merge",
        headers=other,
        json={"source_id": source["id"], "target_id": target["id"]},
    )
    assert res.status_code == 403


def test_join_merged_community_redirects(client, auth_headers):
    source = _create_community(client, auth_headers, name="Old Group", plz="10115", city="Berlin")
    target = _create_community(client, auth_headers, name="New Group", plz="10115", city="Berlin")

    client.post(
        "/communities/merge",
        headers=auth_headers,
        json={"source_id": source["id"], "target_id": target["id"]},
    )

    other = _register(client, "newbie@test.com", "Newbie")
    res = client.post(f"/communities/{source['id']}/join", headers=other)
    assert res.status_code == 409
    assert str(target["id"]) in res.json()["detail"]


# ── Merge Suggestions ──────────────────────────────────────────────


def test_merge_suggestions_same_plz(client, auth_headers):
    a = _create_community(client, auth_headers, name="Group A", plz="10115", city="Berlin")
    _create_community(client, auth_headers, name="Group B", plz="10115", city="Berlin")
    _create_community(client, auth_headers, name="Group C", plz="99999", city="Hamburg")

    res = client.get(
        f"/communities/merge/suggestions?community_id={a['id']}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    suggestions = res.json()
    assert len(suggestions) == 1
    assert suggestions[0]["reason"].startswith("Same postal code")


def test_merge_suggestions_same_city(client, auth_headers):
    a = _create_community(client, auth_headers, name="Group A", plz="10115", city="Berlin")
    _create_community(client, auth_headers, name="Group B", plz="10999", city="Berlin")

    res = client.get(
        f"/communities/merge/suggestions?community_id={a['id']}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    suggestions = res.json()
    assert len(suggestions) == 1
    assert suggestions[0]["reason"].startswith("Same city")


def test_search_excludes_merged(client, auth_headers):
    source = _create_community(client, auth_headers, name="Old", plz="10115", city="Berlin")
    target = _create_community(client, auth_headers, name="New", plz="10115", city="Berlin")

    client.post(
        "/communities/merge",
        headers=auth_headers,
        json={"source_id": source["id"], "target_id": target["id"]},
    )

    res = client.get("/communities/search?postal_code=10115")
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "New"
