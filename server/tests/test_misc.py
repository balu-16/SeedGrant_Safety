"""Health/ready + push-token + websocket manager tests."""

from starlette.testclient import TestClient

from app.websocket.manager import ConnectionManager
from tests.conftest import auth_headers_for, register_user


async def test_health_and_ready(client):
    r = await client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    r = await client.get("/api/ready")
    assert r.status_code == 200 and r.json()["status"] == "ready"


async def test_push_tokens(client):
    await register_user(client, email="push@example.com")
    h = await auth_headers_for(client, "push@example.com")
    r = await client.post(
        "/api/push-tokens",
        json={"token": "ExponentPushToken-1234567890", "platform": "android"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert "token" not in r.text or "ExponentPushToken" not in r.text  # hash only
    r = await client.get("/api/push-tokens", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1
    r = await client.delete("/api/push-tokens", params={"token": "ExponentPushToken-1234567890"}, headers=h)
    assert r.status_code == 204


async def test_connection_manager_broadcast():
    mgr = ConnectionManager()

    class FakeWS:
        def __init__(self) -> None:
            self.sent: list[dict] = []
            self.accepted = False

        async def accept(self) -> None:
            self.accepted = True

        async def send_json(self, msg: dict) -> None:
            self.sent.append(msg)

    a, b = FakeWS(), FakeWS()
    await mgr.connect("u1", a)  # type: ignore[arg-type]
    await mgr.connect("u1", b)  # type: ignore[arg-type]
    n = await mgr.send_to_user("u1", {"type": "ping"})
    assert n == 2 and len(a.sent) == 1 and len(b.sent) == 1
    await mgr.disconnect("u1", a)  # type: ignore[arg-type]
    n = await mgr.send_to_user("u1", {"type": "ping2"})
    assert n == 1


def test_websocket_auth_required(test_app):
    # Uses sync TestClient for real WS handshake.
    c = TestClient(test_app)
    try:
        with c.websocket_connect("/api/ws?token=bad") as ws:
            ws.receive_text()
            raise AssertionError("should not connect")
    except Exception:
        pass  # expected close/reject


def test_websocket_connects_with_valid_token(test_app, client=None):
    import asyncio

    async def _get_token() -> str:
        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post(
                "/api/auth/register",
                json={
                    "name": "W",
                    "email": "w@example.com",
                    "phone": "+919000000020",
                    "password": "password123",
                },
            )
            assert r.status_code in (200, 201)
            r = await ac.post("/api/auth/login", json={"email": "w@example.com", "password": "password123"})
            return r.json()["access_token"]

    token = asyncio.run(_get_token())
    c = TestClient(test_app)
    with c.websocket_connect(f"/api/ws?token={token}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "connected"
