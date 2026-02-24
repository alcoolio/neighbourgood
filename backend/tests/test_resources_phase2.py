"""Tests for Phase 2 resource features: search, categories, image upload."""

import io


def test_search_by_title(client, auth_headers, community_id):
    client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Electric Drill", "category": "tool", "community_id": community_id},
    )
    client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Camping Table", "category": "furniture", "community_id": community_id},
    )

    res = client.get("/resources?q=drill")
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Electric Drill"


def test_search_by_description(client, auth_headers, community_id):
    client.post(
        "/resources",
        headers=auth_headers,
        json={
            "title": "Power Tool",
            "description": "Great for drilling holes in concrete",
            "category": "tool",
            "community_id": community_id,
        },
    )
    client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Sofa", "description": "Comfy blue sofa", "category": "furniture", "community_id": community_id},
    )

    res = client.get("/resources?q=concrete")
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Power Tool"


def test_search_case_insensitive(client, auth_headers, community_id):
    client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "LOUD SPEAKER", "category": "electronics", "community_id": community_id},
    )

    res = client.get("/resources?q=loud")
    assert res.json()["total"] == 1

    res = client.get("/resources?q=LOUD")
    assert res.json()["total"] == 1


def test_search_no_results(client, auth_headers, community_id):
    client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Hammer", "category": "tool", "community_id": community_id},
    )

    res = client.get("/resources?q=spaceship")
    assert res.json()["total"] == 0


def test_list_categories(client):
    res = client.get("/resources/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 8
    values = [c["value"] for c in data]
    assert "tool" in values
    assert "furniture" in values
    assert all("label" in c and "icon" in c for c in data)


def test_filter_available(client, auth_headers, community_id):
    # Create one available and one unavailable resource
    r1 = client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Available Item", "category": "tool", "community_id": community_id},
    )
    r2 = client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Unavailable Item", "category": "tool", "community_id": community_id},
    )
    # Mark second as unavailable
    client.patch(
        f"/resources/{r2.json()['id']}",
        headers=auth_headers,
        json={"is_available": False},
    )

    res = client.get("/resources?available=true")
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "Available Item"

    res = client.get("/resources?available=false")
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "Unavailable Item"


def test_upload_image(client, auth_headers, community_id, tmp_path):
    r = client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Photo Item", "category": "electronics", "community_id": community_id},
    )
    resource_id = r.json()["id"]

    # Upload a fake JPEG image
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    res = client.post(
        f"/resources/{resource_id}/image",
        headers=auth_headers,
        files={"file": ("photo.jpg", fake_image, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["image_url"] is not None
    assert f"/resources/{resource_id}/image" in data["image_url"]


def test_upload_image_invalid_type(client, auth_headers, community_id):
    r = client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Doc Item", "category": "other", "community_id": community_id},
    )
    resource_id = r.json()["id"]

    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    res = client.post(
        f"/resources/{resource_id}/image",
        headers=auth_headers,
        files={"file": ("doc.pdf", fake_pdf, "application/pdf")},
    )
    assert res.status_code == 422


def test_upload_image_not_owner(client, auth_headers, community_id):
    # Create resource as first user
    r = client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Owned Item", "category": "tool", "community_id": community_id},
    )
    resource_id = r.json()["id"]

    # Register a second user
    reg = client.post(
        "/auth/register",
        json={
            "email": "other@example.com",
            "password": "Otherpass123",
            "display_name": "Other User",
        },
    )
    other_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    res = client.post(
        f"/resources/{resource_id}/image",
        headers=other_headers,
        files={"file": ("photo.jpg", fake_image, "image/jpeg")},
    )
    assert res.status_code == 403


def test_get_image_no_image(client, auth_headers, community_id):
    r = client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "No Image", "category": "tool", "community_id": community_id},
    )
    resource_id = r.json()["id"]

    res = client.get(f"/resources/{resource_id}/image")
    assert res.status_code == 404


def test_resource_out_has_image_url_null_by_default(client, auth_headers, community_id):
    r = client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Plain Item", "category": "tool", "community_id": community_id},
    )
    assert r.json()["image_url"] is None
