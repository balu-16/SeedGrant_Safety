"""Auth tests: register, login, refresh rotation, logout, unauthorized."""

from tests.conftest import auth_headers_for, login_user, register_user


async def test_register_login_refresh_flow(client):
    await register_user(client)
    tokens = await login_user(client)
    assert tokens["access_token"] and tokens["refresh_token"]

    r = await client.get("/api/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == "asha@example.com"

    # Refresh token must NOT work as access token
    r = await client.get("/api/users/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401

    # Rotate refresh
    r = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200, r.text
    new_tokens = r.json()
    assert new_tokens["access_token"] != tokens["access_token"]

    # Old refresh token is revoked (rotation)
    r = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401

    # Access token must NOT work at refresh endpoint
    r = await client.post("/api/auth/refresh", json={"refresh_token": new_tokens["access_token"]})
    assert r.status_code == 401


async def test_register_duplicate_email(client):
    await register_user(client)
    r = await client.post(
        "/api/auth/register",
        json={
            "name": "Asha",
            "email": "ASHA@example.com",
            "phone": "+919000000001",
            "password": "password123",
        },
    )
    assert r.status_code == 409


async def test_login_wrong_password(client):
    await register_user(client)
    r = await client.post("/api/auth/login", json={"email": "asha@example.com", "password": "wrongpass1"})
    assert r.status_code == 401


async def test_unauthorized_me(client):
    r = await client.get("/api/users/me")
    assert r.status_code == 401
    r = await client.get("/api/users/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401


async def test_logout_and_logout_all(client):
    await register_user(client)
    tokens = await login_user(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = await client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 204
    r = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401

    tokens2 = await login_user(client)
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}
    r = await client.post("/api/auth/logout-all", headers=headers2)
    assert r.status_code == 200
    assert r.json()["revoked"] >= 1
    r = await client.post("/api/auth/refresh", json={"refresh_token": tokens2["refresh_token"]})
    assert r.status_code == 401
    _ = headers  # silence unused in some runners


async def test_users_me_update(client):
    await register_user(client)
    headers = await auth_headers_for(client, "asha@example.com")
    r = await client.patch("/api/users/me", json={"name": "Asha Devi"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Asha Devi"
    # Password hash must never leak
    assert "password_hash" not in r.json()
