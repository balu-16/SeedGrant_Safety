"""Hardening tests: rate limits, input validation, FCM prune policy, WS auth, consent."""

import pytest
from starlette.testclient import TestClient

from app.auth.service import AuthService
from app.core.exceptions import UnauthorizedError
from app.main import create_app
from tests.conftest import auth_headers_for, login_user, register_user


async def test_register_rejects_whitespace_only_fields(client):
    r = await client.post(
        "/api/auth/register",
        json={"name": "   ", "email": "blank@example.com", "phone": "+919000000030", "password": "password123"},
    )
    assert r.status_code == 422
    r = await client.post(
        "/api/auth/register",
        json={"name": "Asha", "email": "blank2@example.com", "phone": "       ", "password": "password123"},
    )
    assert r.status_code == 422


async def test_users_me_rejects_blank_name(client):
    await register_user(client, email="blankname@example.com")
    h = await auth_headers_for(client, "blankname@example.com")
    r = await client.patch("/api/users/me", json={"name": "  "}, headers=h)
    assert r.status_code == 422


async def test_rate_limit_on_register(client, test_app):
    for i in range(5):
        r = await client.post(
            "/api/auth/register",
            json={
                "name": f"U{i}",
                "email": f"u{i}@example.com",
                "phone": f"+9190000004{i:02d}",
                "password": "password123",
            },
        )
        assert r.status_code == 201, r.text
    r = await client.post(
        "/api/auth/register",
        json={"name": "Over", "email": "over@example.com", "phone": "+919000000099", "password": "password123"},
    )
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited"


async def test_rate_limiters_are_per_app(client, test_app, settings, repos):
    await register_user(client, email="iso@example.com")
    assert getattr(test_app.state, "rate_limiters", {})
    fresh = create_app(settings)
    fresh.state.pool = None
    fresh.state.repos = repos
    assert not getattr(fresh.state, "rate_limiters", {})


async def test_refresh_rejects_when_revoke_loses_race(client, test_app, repos, settings):
    await register_user(client, email="race@example.com")
    tokens = await login_user(client, email="race@example.com")

    class RacyRefresh(type(repos.refresh_tokens)):
        """Simulates a concurrent rotation winning the revoke."""

        def __init__(self, inner) -> None:
            self._inner = inner

        async def get_by_jti_hash(self, jti):
            return await self._inner.get_by_jti_hash(jti)

        async def revoke_by_jti_hash(self, jti):
            await self._inner.revoke_by_jti_hash(jti)
            return False

    svc = AuthService(repos.users, RacyRefresh(repos.refresh_tokens), settings)  # type: ignore[arg-type]
    with pytest.raises(UnauthorizedError):
        await svc.refresh(refresh_token=tokens["refresh_token"])


async def test_location_rejects_future_recorded_at(client):
    await register_user(client, email="future@example.com")
    h = await auth_headers_for(client, "future@example.com")
    r = await client.post(
        "/api/locations",
        json={"latitude": 19.0, "longitude": 72.8, "recorded_at": "2100-01-01T00:00:00Z"},
        headers=h,
    )
    assert r.status_code == 422
    # Naive timestamps are coerced to UTC and accepted
    r = await client.post(
        "/api/locations",
        json={"latitude": 19.0, "longitude": 72.8, "recorded_at": "2020-01-01T00:00:00"},
        headers=h,
    )
    assert r.status_code == 201


def test_websocket_auth_close_code_delivered(test_app):
    from fastapi import WebSocketDisconnect

    c = TestClient(test_app)
    # accept() before close() means the client actually receives the 4401 code
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with c.websocket_connect("/api/ws?token=bad") as ws:
            ws.receive_text()
    assert exc_info.value.code == 4401


async def test_pending_invite_links_on_register(client):
    await register_user(client, email="late-owner@example.com")
    hp = await auth_headers_for(client, "late-owner@example.com")
    r = await client.post("/api/guardians/invite", json={"guardian_email": "late@example.com"}, headers=hp)
    assert r.status_code == 201
    assert r.json()["guardian_user_id"] is None

    # The invited person registers afterwards — invite links to their account
    await register_user(client, name="Late", email="late@example.com", phone="+919000000070")
    hg = await auth_headers_for(client, "late@example.com")
    r = await client.get("/api/guardians/protecting", params={"include_pending": "true"}, headers=hg)
    assert r.status_code == 200 and len(r.json()) == 1
    gid = r.json()[0]["id"]
    r = await client.patch(f"/api/guardians/{gid}/status", json={"status": "accepted"}, headers=hg)
    assert r.status_code == 200
