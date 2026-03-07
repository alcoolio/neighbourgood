"""Tests for decentralized instance data sync endpoints."""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.federation import KnownInstance
from app.models.sync import FederatedResource, FederatedSkill, InstanceSyncLog


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_admin(client):
    """Register a user and promote them to admin; return auth headers."""
    res = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "Adminpass1",
            "display_name": "Admin User",
            "neighbourhood": "Adminville",
        },
    )
    assert res.status_code == 201, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_admin_in_db(client, db):
    """Register a user and flip their role to admin in the DB."""
    from app.models.user import User

    headers = _make_admin(client)
    user = db.query(User).filter(User.email == "admin@example.com").first()
    user.role = "admin"
    db.commit()
    return headers


def _seed_known_instance(db, url="https://remote.example.com", name="Remote NG") -> KnownInstance:
    inst = KnownInstance(
        url=url,
        name=name,
        description="A remote instance",
        region="EU",
        version="1.4.0",
        platform_mode="blue",
        admin_contact="admin@remote.example.com",
        community_count=2,
        user_count=10,
        is_reachable=True,
        last_seen_at=datetime.datetime.utcnow(),
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def _seed_federated_resource(db, instance_id: int, remote_id: int = 1) -> FederatedResource:
    fr = FederatedResource(
        source_instance_id=instance_id,
        remote_id=remote_id,
        title="Remote Drill",
        description="A drill from a remote instance",
        category="tools",
        condition="good",
        community_name="Remote Community",
        owner_display_name="Remote Alice",
        is_available=True,
        synced_at=datetime.datetime.utcnow(),
    )
    db.add(fr)
    db.commit()
    db.refresh(fr)
    return fr


def _seed_federated_skill(db, instance_id: int, remote_id: int = 1) -> FederatedSkill:
    fs = FederatedSkill(
        source_instance_id=instance_id,
        remote_id=remote_id,
        title="Remote Python tutoring",
        description="Python help from afar",
        category="education",
        skill_type="offer",
        community_name="Remote Community",
        owner_display_name="Remote Bob",
        synced_at=datetime.datetime.utcnow(),
    )
    db.add(fs)
    db.commit()
    db.refresh(fs)
    return fs


# ── GET /federation/sync/snapshot ────────────────────────────────────────────


class TestSnapshotEndpoint:
    def test_snapshot_returns_empty_when_no_data(self, client):
        res = client.get("/federation/sync/snapshot")
        assert res.status_code == 200
        data = res.json()
        assert data["resources"] == []
        assert data["skills"] == []
        assert "snapshot_at" in data

    def test_snapshot_includes_local_available_resource(self, client, auth_headers, community_id):
        # Create a resource
        resp = client.post(
            "/resources",
            headers=auth_headers,
            json={
                "title": "Power Drill",
                "description": "A nice drill",
                "category": "tool",
                "condition": "good",
                "community_id": community_id,
            },
        )
        assert resp.status_code == 201, resp.text
        res = client.get("/federation/sync/snapshot")
        assert res.status_code == 200
        data = res.json()
        assert len(data["resources"]) == 1
        r = data["resources"][0]
        assert r["title"] == "Power Drill"
        assert r["category"] == "tool"
        assert r["is_available"] is True
        assert "remote_id" in r

    def test_snapshot_excludes_unavailable_resources(self, client, auth_headers, community_id, db):
        from app.models.resource import Resource

        client.post(
            "/resources",
            headers=auth_headers,
            json={"title": "Old Saw", "description": "", "category": "tool", "condition": "worn", "community_id": community_id},
        )
        # Mark it unavailable directly in DB
        db.query(Resource).filter(Resource.title == "Old Saw").update({"is_available": False})
        db.commit()

        res = client.get("/federation/sync/snapshot")
        assert res.status_code == 200
        assert res.json()["resources"] == []

    def test_snapshot_includes_skills(self, client, auth_headers, community_id):
        client.post(
            "/skills",
            headers=auth_headers,
            json={
                "title": "Carpentry",
                "description": "I can build things",
                "category": "crafts",
                "skill_type": "offer",
                "community_id": community_id,
            },
        )
        res = client.get("/federation/sync/snapshot")
        assert res.status_code == 200
        skills = res.json()["skills"]
        assert len(skills) == 1
        assert skills[0]["title"] == "Carpentry"
        assert skills[0]["skill_type"] == "offer"

    def test_snapshot_since_filter_excludes_older_items(self, client, auth_headers, community_id, db):
        from app.models.resource import Resource

        client.post(
            "/resources",
            headers=auth_headers,
            json={"title": "Old Drill", "description": "", "category": "tool", "condition": "fair", "community_id": community_id},
        )
        # Back-date the resource
        future = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
        res = client.get(f"/federation/sync/snapshot?since={future}")
        assert res.status_code == 200
        assert res.json()["resources"] == []

    def test_snapshot_since_filter_invalid_value(self, client):
        res = client.get("/federation/sync/snapshot?since=not-a-date")
        assert res.status_code == 422

    def test_snapshot_is_public_no_auth_required(self, client):
        res = client.get("/federation/sync/snapshot")
        assert res.status_code == 200


# ── POST /federation/sync/pull ───────────────────────────────────────────────


class TestPullEndpoint:
    def test_pull_requires_auth(self, client):
        res = client.post("/federation/sync/pull")
        assert res.status_code == 403

    def test_pull_requires_admin(self, client, auth_headers):
        res = client.post("/federation/sync/pull", headers=auth_headers)
        assert res.status_code == 403

    def test_pull_with_no_instances_returns_zero_counts(self, client, db):
        admin_headers = _make_admin_in_db(client, db)
        res = client.post("/federation/sync/pull", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["instances_attempted"] == 0
        assert data["instances_ok"] == 0
        assert data["instances_failed"] == 0
        assert data["total_resources_synced"] == 0
        assert data["total_skills_synced"] == 0

    def test_pull_syncs_resources_and_skills_from_remote(self, client, db):
        admin_headers = _make_admin_in_db(client, db)
        inst = _seed_known_instance(db)

        snapshot_payload = {
            "instance_url": inst.url,
            "instance_name": inst.name,
            "snapshot_at": datetime.datetime.utcnow().isoformat(),
            "resources": [
                {
                    "remote_id": 42,
                    "title": "Remote Ladder",
                    "description": "A tall ladder",
                    "category": "tools",
                    "condition": "good",
                    "community_name": "Remote Village",
                    "owner_display_name": "Bob Remote",
                    "is_available": True,
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
            ],
            "skills": [
                {
                    "remote_id": 7,
                    "title": "Remote Plumbing",
                    "description": "Fix your pipes",
                    "category": "trades",
                    "skill_type": "offer",
                    "community_name": "Remote Village",
                    "owner_display_name": "Alice Remote",
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
            ],
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = snapshot_payload
        mock_resp.raise_for_status = MagicMock()

        with patch("app.routers.federation_sync.httpx.get", return_value=mock_resp):
            res = client.post("/federation/sync/pull", headers=admin_headers)

        assert res.status_code == 200
        data = res.json()
        assert data["instances_attempted"] == 1
        assert data["instances_ok"] == 1
        assert data["total_resources_synced"] == 1
        assert data["total_skills_synced"] == 1

        fr = db.query(FederatedResource).filter(FederatedResource.remote_id == 42).first()
        assert fr is not None
        assert fr.title == "Remote Ladder"
        assert fr.source_instance_id == inst.id

        fs = db.query(FederatedSkill).filter(FederatedSkill.remote_id == 7).first()
        assert fs is not None
        assert fs.title == "Remote Plumbing"

    def test_pull_records_sync_log(self, client, db):
        admin_headers = _make_admin_in_db(client, db)
        inst = _seed_known_instance(db)

        snapshot_payload = {
            "instance_url": inst.url,
            "instance_name": inst.name,
            "snapshot_at": datetime.datetime.utcnow().isoformat(),
            "resources": [],
            "skills": [],
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = snapshot_payload
        mock_resp.raise_for_status = MagicMock()

        with patch("app.routers.federation_sync.httpx.get", return_value=mock_resp):
            client.post("/federation/sync/pull", headers=admin_headers)

        log = db.query(InstanceSyncLog).filter(InstanceSyncLog.instance_id == inst.id).first()
        assert log is not None
        assert log.status == "ok"

    def test_pull_records_error_log_on_failure(self, client, db):
        admin_headers = _make_admin_in_db(client, db)
        inst = _seed_known_instance(db)

        with patch(
            "app.routers.federation_sync.httpx.get",
            side_effect=Exception("Connection refused"),
        ):
            res = client.post("/federation/sync/pull", headers=admin_headers)

        assert res.status_code == 200
        data = res.json()
        assert data["instances_failed"] == 1
        assert data["instances_ok"] == 0

        log = db.query(InstanceSyncLog).filter(InstanceSyncLog.instance_id == inst.id).first()
        assert log is not None
        assert log.status == "error"
        assert "Connection refused" in log.error_message

    def test_pull_upserts_existing_resource(self, client, db):
        admin_headers = _make_admin_in_db(client, db)
        inst = _seed_known_instance(db)
        _seed_federated_resource(db, inst.id, remote_id=99)

        snapshot_payload = {
            "instance_url": inst.url,
            "instance_name": inst.name,
            "snapshot_at": datetime.datetime.utcnow().isoformat(),
            "resources": [
                {
                    "remote_id": 99,
                    "title": "Updated Title",
                    "description": "Updated desc",
                    "category": "tools",
                    "condition": "excellent",
                    "community_name": "Remote Community",
                    "owner_display_name": "Remote Alice",
                    "is_available": True,
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
            ],
            "skills": [],
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = snapshot_payload
        mock_resp.raise_for_status = MagicMock()

        with patch("app.routers.federation_sync.httpx.get", return_value=mock_resp):
            client.post("/federation/sync/pull", headers=admin_headers)

        rows = db.query(FederatedResource).filter(FederatedResource.remote_id == 99).all()
        assert len(rows) == 1  # no duplicate
        assert rows[0].title == "Updated Title"

    def test_pull_skips_unreachable_instances(self, client, db):
        admin_headers = _make_admin_in_db(client, db)
        inst = _seed_known_instance(db)
        inst.is_reachable = False
        db.commit()

        res = client.post("/federation/sync/pull", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["instances_attempted"] == 0

    def test_pull_uses_since_cursor_from_last_ok_log(self, client, db):
        admin_headers = _make_admin_in_db(client, db)
        inst = _seed_known_instance(db)

        # Seed a previous successful sync log
        since_time = datetime.datetime(2026, 3, 1, 12, 0, 0)
        log = InstanceSyncLog(
            instance_id=inst.id,
            synced_at=since_time,
            resources_synced=3,
            skills_synced=1,
            status="ok",
            error_message="",
        )
        db.add(log)
        db.commit()

        captured_params = {}

        def mock_get(url, params=None, timeout=None):
            captured_params.update(params or {})
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "instance_url": inst.url,
                "instance_name": inst.name,
                "snapshot_at": datetime.datetime.utcnow().isoformat(),
                "resources": [],
                "skills": [],
            }
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch("app.routers.federation_sync.httpx.get", side_effect=mock_get):
            client.post("/federation/sync/pull", headers=admin_headers)

        assert "since" in captured_params
        assert "2026-03-01" in captured_params["since"]


# ── GET /federation/sync/status ──────────────────────────────────────────────


class TestSyncStatusEndpoint:
    def test_status_requires_auth(self, client):
        res = client.get("/federation/sync/status")
        assert res.status_code == 403

    def test_status_empty_when_no_instances(self, client, auth_headers):
        res = client.get("/federation/sync/status", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_status_shows_never_for_unsynced_instance(self, client, auth_headers, db):
        _seed_known_instance(db)
        res = client.get("/federation/sync/status", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["status"] == "never"
        assert data[0]["last_synced_at"] is None

    def test_status_shows_last_sync_result(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        log = InstanceSyncLog(
            instance_id=inst.id,
            synced_at=datetime.datetime.utcnow(),
            resources_synced=5,
            skills_synced=2,
            status="ok",
            error_message="",
        )
        db.add(log)
        db.commit()

        res = client.get("/federation/sync/status", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["status"] == "ok"
        assert data[0]["resources_synced"] == 5
        assert data[0]["skills_synced"] == 2
        assert data[0]["instance_url"] == inst.url


# ── GET /federation/federated-resources ──────────────────────────────────────


class TestFederatedResourcesEndpoint:
    def test_requires_auth(self, client):
        res = client.get("/federation/federated-resources")
        assert res.status_code == 403

    def test_empty_when_no_federated_data(self, client, auth_headers):
        res = client.get("/federation/federated-resources", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_federated_resources(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        _seed_federated_resource(db, inst.id)

        res = client.get("/federation/federated-resources", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Remote Drill"
        assert data[0]["source_instance_url"] == inst.url
        assert data[0]["source_instance_name"] == inst.name

    def test_filters_by_category(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        _seed_federated_resource(db, inst.id, remote_id=1)
        fr2 = FederatedResource(
            source_instance_id=inst.id,
            remote_id=2,
            title="Remote Bike",
            description="",
            category="vehicles",
            condition="good",
            community_name="",
            owner_display_name="",
            is_available=True,
            synced_at=datetime.datetime.utcnow(),
        )
        db.add(fr2)
        db.commit()

        res = client.get("/federation/federated-resources?category=vehicles", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["category"] == "vehicles"

    def test_filters_unavailable_by_default(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        fr = _seed_federated_resource(db, inst.id)
        fr.is_available = False
        db.commit()

        res = client.get("/federation/federated-resources", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_available_only_false_shows_unavailable(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        fr = _seed_federated_resource(db, inst.id)
        fr.is_available = False
        db.commit()

        res = client.get(
            "/federation/federated-resources?available_only=false", headers=auth_headers
        )
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_filters_by_instance_id(self, client, auth_headers, db):
        inst1 = _seed_known_instance(db, url="https://inst1.example.com", name="Inst1")
        inst2 = _seed_known_instance(db, url="https://inst2.example.com", name="Inst2")
        _seed_federated_resource(db, inst1.id, remote_id=1)
        fr2 = FederatedResource(
            source_instance_id=inst2.id,
            remote_id=2,
            title="Inst2 Resource",
            description="",
            category="tools",
            condition="",
            community_name="",
            owner_display_name="",
            is_available=True,
            synced_at=datetime.datetime.utcnow(),
        )
        db.add(fr2)
        db.commit()

        res = client.get(
            f"/federation/federated-resources?instance_id={inst2.id}", headers=auth_headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Inst2 Resource"


# ── GET /federation/federated-skills ─────────────────────────────────────────


class TestFederatedSkillsEndpoint:
    def test_requires_auth(self, client):
        res = client.get("/federation/federated-skills")
        assert res.status_code == 403

    def test_empty_when_no_data(self, client, auth_headers):
        res = client.get("/federation/federated-skills", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_federated_skills(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        _seed_federated_skill(db, inst.id)

        res = client.get("/federation/federated-skills", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Remote Python tutoring"
        assert data[0]["source_instance_url"] == inst.url

    def test_filters_by_skill_type(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        _seed_federated_skill(db, inst.id, remote_id=1)
        fs2 = FederatedSkill(
            source_instance_id=inst.id,
            remote_id=2,
            title="Remote Spanish Lessons Wanted",
            description="",
            category="languages",
            skill_type="request",
            community_name="",
            owner_display_name="",
            synced_at=datetime.datetime.utcnow(),
        )
        db.add(fs2)
        db.commit()

        res = client.get(
            "/federation/federated-skills?skill_type=request", headers=auth_headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["skill_type"] == "request"

    def test_filters_by_category(self, client, auth_headers, db):
        inst = _seed_known_instance(db)
        _seed_federated_skill(db, inst.id, remote_id=1)

        res = client.get(
            "/federation/federated-skills?category=education", headers=auth_headers
        )
        assert res.status_code == 200
        assert len(res.json()) == 1

        res2 = client.get(
            "/federation/federated-skills?category=cooking", headers=auth_headers
        )
        assert res2.status_code == 200
        assert res2.json() == []

    def test_filters_by_instance_id(self, client, auth_headers, db):
        inst1 = _seed_known_instance(db, url="https://s1.example.com", name="S1")
        inst2 = _seed_known_instance(db, url="https://s2.example.com", name="S2")
        _seed_federated_skill(db, inst1.id, remote_id=1)

        res = client.get(
            f"/federation/federated-skills?instance_id={inst2.id}", headers=auth_headers
        )
        assert res.status_code == 200
        assert res.json() == []
