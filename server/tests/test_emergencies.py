"""Emergency tests: create, transitions, authz, validation, events."""

from tests.conftest import auth_headers_for, register_user


async def test_emergency_create_and_transitions(client, test_app, emitted, repos):
    await register_user(client, email="sos@example.com")
    h = await auth_headers_for(client, "sos@example.com")

    r = await client.post(
        "/api/emergencies",
        json={"trigger_type": "TAG_BUTTON", "latitude": 19.0, "longitude": 72.0, "note": "help"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    assert r.json()["status"] == "active"
    # Audit event written
    assert len(repos.emergencies.events) == 1
    # Best-effort WS emit happened
    assert emitted and emitted[0][1]["type"] == "emergency-created"

    # Invalid trigger rejected
    r = await client.post("/api/emergencies", json={"trigger_type": "NOPE"}, headers=h)
    assert r.status_code == 422

    # active -> acknowledged
    r = await client.patch(f"/api/emergencies/{eid}/status", json={"status": "acknowledged"}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "acknowledged"

    # acknowledged -> active is illegal
    r = await client.patch(f"/api/emergencies/{eid}/status", json={"status": "active"}, headers=h)
    assert r.status_code == 422

    # resolve via convenience endpoint
    r = await client.post(f"/api/emergencies/{eid}/resolve", headers=h)
    assert r.status_code == 200 and r.json()["status"] == "resolved"
    assert r.json()["resolved_at"] is not None

    # terminal state cannot change
    r = await client.patch(f"/api/emergencies/{eid}/status", json={"status": "cancelled"}, headers=h)
    assert r.status_code == 422

    r = await client.get("/api/emergencies", headers=h)
    assert r.status_code == 200 and r.json()["total"] == 1


async def test_emergency_device_ownership(client):
    await register_user(client, email="e1@example.com")
    await register_user(client, name="E2", email="e2@example.com", phone="+919000000011")
    h1 = await auth_headers_for(client, "e1@example.com")
    h2 = await auth_headers_for(client, "e2@example.com")
    r = await client.post("/api/devices", json={"name": "T"}, headers=h2)
    other_device = r.json()["id"]
    r = await client.post(
        "/api/emergencies",
        json={"trigger_type": "APP_BUTTON", "device_id": other_device},
        headers=h1,
    )
    assert r.status_code == 403


async def test_emergency_requires_auth(client):
    r = await client.post("/api/emergencies", json={"trigger_type": "APP_BUTTON"})
    assert r.status_code == 401


async def test_all_trigger_types_accepted(client):
    await register_user(client, email="trig@example.com")
    h = await auth_headers_for(client, "trig@example.com")
    for t in ("TAG_BUTTON", "TAG_VOICE", "APP_BUTTON", "APP_VOICE", "FALL_DETECTION"):
        r = await client.post("/api/emergencies", json={"trigger_type": t}, headers=h)
        assert r.status_code == 201, t
