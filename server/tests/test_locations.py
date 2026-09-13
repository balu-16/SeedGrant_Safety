"""Location tests: validation, latest, history pagination."""

from tests.conftest import auth_headers_for, register_user


async def test_location_submit_latest_history(client):
    await register_user(client, email="loc@example.com")
    h = await auth_headers_for(client, "loc@example.com")

    r = await client.post(
        "/api/locations",
        json={"latitude": 19.07, "longitude": 72.87, "accuracy_m": 12, "source": "phone_gps"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    r = await client.post("/api/locations", json={"latitude": 19.08, "longitude": 72.88}, headers=h)
    assert r.status_code == 201

    r = await client.get("/api/locations/latest", headers=h)
    assert r.status_code == 200
    assert r.json()["latitude"] == 19.08

    r = await client.get("/api/locations/history", params={"limit": 1, "offset": 0}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2 and len(body["items"]) == 1
    r = await client.get("/api/locations/history", params={"limit": 10, "offset": 1}, headers=h)
    assert len(r.json()["items"]) == 1


async def test_location_validation(client):
    await register_user(client, email="lv@example.com")
    h = await auth_headers_for(client, "lv@example.com")
    for bad in (
        {"latitude": 91, "longitude": 0},
        {"latitude": 0, "longitude": 200},
        {"latitude": "x", "longitude": 0},
    ):
        r = await client.post("/api/locations", json=bad, headers=h)
        assert r.status_code == 422, bad
    r = await client.post("/api/locations", json={"latitude": 0, "longitude": 0}, headers={})
    assert r.status_code == 401
