"""Tests for reputation/trust score endpoints."""


def _register(client, email, name="User"):
    res = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": name,
        },
    )
    data = res.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


def _create_resource(client, headers, title="Shared Drill"):
    res = client.post(
        "/resources",
        headers=headers,
        json={"title": title, "category": "tool"},
    )
    return res.json()["id"]


# ── Basic reputation ───────────────────────────────────────────────


def test_newcomer_reputation(client, auth_headers):
    """Fresh user has zero score and Newcomer level."""
    res = client.get("/users/me/reputation", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["score"] == 0
    assert data["level"] == "Newcomer"
    assert data["breakdown"]["resources_shared"] == 0


def test_reputation_after_sharing_resource(client, auth_headers):
    """Sharing a resource earns 5 points."""
    client.post(
        "/resources",
        headers=auth_headers,
        json={"title": "Drill", "category": "tool"},
    )
    res = client.get("/users/me/reputation", headers=auth_headers)
    data = res.json()
    assert data["score"] == 5
    assert data["breakdown"]["resources_shared"] == 5


def test_reputation_after_offering_skill(client, auth_headers):
    """Offering a skill earns 5 points."""
    client.post(
        "/skills",
        headers=auth_headers,
        json={"title": "Python tutoring", "category": "tutoring", "skill_type": "offer"},
    )
    res = client.get("/users/me/reputation", headers=auth_headers)
    data = res.json()
    assert data["breakdown"]["skills_offered"] == 5


def test_reputation_after_requesting_skill(client, auth_headers):
    """Requesting a skill earns 2 points."""
    client.post(
        "/skills",
        headers=auth_headers,
        json={"title": "Need cooking help", "category": "cooking", "skill_type": "request"},
    )
    res = client.get("/users/me/reputation", headers=auth_headers)
    data = res.json()
    assert data["breakdown"]["skills_requested"] == 2


def test_reputation_level_progression(client, auth_headers):
    """Multiple activities push user to higher levels."""
    # 2 resources = 10 points → Neighbour
    client.post(
        "/resources", headers=auth_headers,
        json={"title": "Drill", "category": "tool"},
    )
    client.post(
        "/resources", headers=auth_headers,
        json={"title": "Ladder", "category": "tool"},
    )
    res = client.get("/users/me/reputation", headers=auth_headers)
    assert res.json()["level"] == "Neighbour"


def test_public_reputation_endpoint(client, auth_headers):
    """Public endpoint returns reputation for any user."""
    # Register returns user info – get the user ID
    me = client.get("/users/me", headers=auth_headers)
    user_id = me.json()["id"]

    res = client.get(f"/users/{user_id}/reputation")
    assert res.status_code == 200
    assert res.json()["user_id"] == user_id


def test_public_reputation_not_found(client):
    """Non-existent user returns 404."""
    res = client.get("/users/999/reputation")
    assert res.status_code == 404


def test_reputation_completed_booking(client, auth_headers):
    """Completed bookings earn points for both lender and borrower."""
    borrower_headers = _register(client, "borrower@test.com", "Borrower")
    resource_id = _create_resource(client, auth_headers)

    # Create and complete a booking
    booking = client.post(
        "/bookings",
        headers=borrower_headers,
        json={
            "resource_id": resource_id,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
        },
    )
    booking_id = booking.json()["id"]

    # Owner approves
    client.patch(
        f"/bookings/{booking_id}",
        headers=auth_headers,
        json={"status": "approved"},
    )
    # Borrower completes
    client.patch(
        f"/bookings/{booking_id}",
        headers=borrower_headers,
        json={"status": "completed"},
    )

    # Lender reputation: 5 (resource) + 10 (lending completed) = 15
    lender_rep = client.get("/users/me/reputation", headers=auth_headers)
    assert lender_rep.json()["breakdown"]["lending_completed"] == 10
    assert lender_rep.json()["score"] == 15

    # Borrower reputation: 3 (borrowing completed) = 3
    borrower_rep = client.get("/users/me/reputation", headers=borrower_headers)
    assert borrower_rep.json()["breakdown"]["borrowing_completed"] == 3


def test_reputation_requires_auth_for_me(client):
    """The /me/reputation endpoint requires authentication."""
    res = client.get("/users/me/reputation")
    assert res.status_code == 403
