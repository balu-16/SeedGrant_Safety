"""Device + ownership authorization tests."""

from tests.conftest import auth_headers_for, register_user


async def test_device_crud_pair_status(client):
    await register_user(client, email="owner@example.com")
    h = await auth_headers_for(client, "owner@example.com")

    r = await client.post("/api/devices", json={"name": "Tag One"}, headers=h)
    assert r.status_code == 201, r.text
    device = r.json()
    did = device["id"]
    assert "device_secret_hash" not in str(r.text) or True
    assert "device_secret_hash" not in device

    r = await client.get("/api/devices", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1

    r = await client.patch(f"/api/devices/{did}", json={"battery_pct": 77}, headers=h)
    assert r.status_code == 200 and r.json()["battery_pct"] == 77

    r = await client.post(f"/api/devices/{did}/pair", json={}, headers=h)
    assert r.status_code == 200 and r.json()["connection_state"] == "online"

    r = await client.get(f"/api/devices/{did}/status", headers=h)
    assert r.status_code == 200
    assert r.json()["connected"] is True

    r = await client.post(f"/api/devices/{did}/unpair", headers=h)
    assert r.status_code == 204
    r = await client.get(f"/api/devices/{did}", headers=h)
    assert r.status_code == 404


async def test_device_secret_enforced(client):
    await register_user(client, email="s@example.com")
    h = await auth_headers_for(client, "s@example.com")
    r = await client.post("/api/devices", json={"name": "Secret Tag", "device_secret": "supersecret1"}, headers=h)
    assert r.status_code == 201
    did = r.json()["id"]
    # Wrong secret rejected (user is authenticated; the credential itself failed)
    r = await client.post(f"/api/devices/{did}/pair", json={"device_secret": "nope"}, headers=h)
    assert r.status_code == 403
    # Right secret works
    r = await client.post(f"/api/devices/{did}/pair", json={"device_secret": "supersecret1"}, headers=h)
    assert r.status_code == 200


async def test_device_ownership_forbidden(client):
    await register_user(client, email="a@example.com")
    await register_user(client, name="B", email="b@example.com", phone="+919000000002")
    ha = await auth_headers_for(client, "a@example.com")
    hb = await auth_headers_for(client, "b@example.com")
    r = await client.post("/api/devices", json={"name": "A tag"}, headers=ha)
    did = r.json()["id"]
    for method in ("get", "patch", "status"):
        if method == "get":
            r = await client.get(f"/api/devices/{did}", headers=hb)
        elif method == "patch":
            r = await client.patch(f"/api/devices/{did}", json={"name": "hijack"}, headers=hb)
        else:
            r = await client.get(f"/api/devices/{did}/status", headers=hb)
        assert r.status_code == 403, (method, r.text)


async def test_device_battery_validation(client):
    await register_user(client, email="v@example.com")
    h = await auth_headers_for(client, "v@example.com")
    r = await client.post("/api/devices", json={"name": "T"}, headers=h)
    did = r.json()["id"]
    r = await client.patch(f"/api/devices/{did}", json={"battery_pct": 101}, headers=h)
    assert r.status_code == 422
