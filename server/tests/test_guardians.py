"""Guardian + guardian-authorization tests."""

from tests.conftest import auth_headers_for, register_user


async def test_guardian_invite_accept_flow(client, repos):
    await register_user(client, email="prot@example.com")
    await register_user(client, name="G", email="guard@example.com", phone="+919000000009")
    hp = await auth_headers_for(client, "prot@example.com")

    r = await client.post(
        "/api/guardians/invite",
        json={"guardian_email": "guard@example.com", "guardian_name": "G", "relation": "Friend"},
        headers=hp,
    )
    assert r.status_code == 201, r.text
    gid = r.json()["id"]
    assert r.json()["status"] == "pending"

    # Guardian user record should be linked automatically
    assert r.json()["guardian_user_id"] is not None

    r = await client.patch(f"/api/guardians/{gid}/status", json={"status": "accepted"}, headers=hp)
    assert r.status_code == 200 and r.json()["status"] == "accepted"

    # Invalid transition: accepted -> pending
    r = await client.patch(f"/api/guardians/{gid}/status", json={"status": "pending"}, headers=hp)
    assert r.status_code == 422

    r = await client.delete(f"/api/guardians/{gid}", headers=hp)
    assert r.status_code == 200 and r.json()["status"] == "removed"


async def test_guardian_duplicate_and_self(client):
    await register_user(client, email="p2@example.com")
    hp = await auth_headers_for(client, "p2@example.com")
    r = await client.post("/api/guardians/invite", json={"guardian_email": "x@example.com"}, headers=hp)
    assert r.status_code == 201
    r = await client.post("/api/guardians/invite", json={"guardian_email": "x@example.com"}, headers=hp)
    assert r.status_code == 409
    r = await client.post("/api/guardians/invite", json={"guardian_email": "p2@example.com"}, headers=hp)
    assert r.status_code == 422


async def test_guardian_can_read_location_and_emergency(client):
    await register_user(client, email="prot2@example.com")
    await register_user(client, name="G2", email="g2@example.com", phone="+919000000010")
    hp = await auth_headers_for(client, "prot2@example.com")
    hg = await auth_headers_for(client, "g2@example.com")

    # Protected posts location + emergency
    r = await client.post("/api/locations", json={"latitude": 19.0, "longitude": 72.8}, headers=hp)
    assert r.status_code == 201
    r = await client.post(
        "/api/emergencies",
        json={"trigger_type": "APP_BUTTON", "latitude": 19.0, "longitude": 72.8},
        headers=hp,
    )
    assert r.status_code == 201
    eid = r.json()["id"]

    # Stranger guardian cannot read yet
    r = await client.get("/api/locations/latest", headers=hg)
    # defaults to own location -> None (no 403 since own)
    assert r.status_code == 200

    # Need protected user id: fetch me
    me = (await client.get("/api/users/me", headers=hp)).json()
    r = await client.get("/api/locations/latest", params={"user_id": me["id"]}, headers=hg)
    assert r.status_code == 403
    r = await client.get(f"/api/emergencies/{eid}", headers=hg)
    assert r.status_code == 403

    # Invite + accept, then guardian can read
    r = await client.post("/api/guardians/invite", json={"guardian_email": "g2@example.com"}, headers=hp)
    gid = r.json()["id"]
    r = await client.patch(f"/api/guardians/{gid}/status", json={"status": "accepted"}, headers=hp)
    assert r.status_code == 200
    r = await client.get("/api/locations/latest", params={"user_id": me["id"]}, headers=hg)
    assert r.status_code == 200 and r.json() is not None
    r = await client.get(f"/api/emergencies/{eid}", headers=hg)
    assert r.status_code == 200
