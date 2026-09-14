"""Admin portal tests: RBAC guard, disable enforcement, audit trail, full control."""

import uuid

from starlette.testclient import TestClient

from tests.conftest import auth_headers_for, login_user, register_user


async def _make_admin(client, test_app, *, email="admin@example.com") -> str:
    """Register a user and promote them via the users repo (no self-service path)."""
    user = await register_user(client, email=email)
    await test_app.state.repos.users.set_role(user["id"], "admin")
    return user["id"]


# ------------------------------------------------------------------ guard ---


async def test_admin_routes_reject_anonymous(client):
    r = await client.get("/api/admin/stats")
    assert r.status_code == 401


async def test_admin_routes_reject_regular_user(client):
    await register_user(client, email="plain@example.com")
    h = await auth_headers_for(client, "plain@example.com")
    for path in ("/api/admin/stats", "/api/admin/users", "/api/admin/devices",
                 "/api/admin/guardians", "/api/admin/emergencies", "/api/admin/audit"):
        r = await client.get(path, headers=h)
        assert r.status_code == 403, path


async def test_admin_routes_allow_admin(client, test_app):
    await _make_admin(client, test_app)
    h = await auth_headers_for(client, "admin@example.com")
    r = await client.get("/api/admin/stats", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["totals"]["users_total"] == 1
    assert len(body["series"]) == 30


async def test_demoted_admin_loses_access_immediately(client, test_app):
    admin_id = await _make_admin(client, test_app)
    h = await auth_headers_for(client, "admin@example.com")
    await test_app.state.repos.users.set_role(admin_id, "user")
    r = await client.get("/api/admin/stats", headers=h)
    assert r.status_code == 403


# --------------------------------------------------------------- disabled ---


async def test_disabled_user_cannot_login(client, test_app):
    user = await register_user(client, email="dologin@example.com")
    await test_app.state.repos.users.set_disabled(user["id"], True)
    r = await client.post(
        "/api/auth/login", json={"email": "dologin@example.com", "password": "password123"}
    )
    assert r.status_code == 401


async def test_disable_kills_existing_session(client, test_app):
    await _make_admin(client, test_app, email="killer@example.com")
    user = await register_user(client, email="victim@example.com")
    h = await auth_headers_for(client, "victim@example.com")
    ha = await auth_headers_for(client, "killer@example.com")

    r = await client.post(f"/api/admin/users/{user['id']}/disable", headers=ha)
    assert r.status_code == 200
    # Existing access token dies on the next request (DB re-check per request).
    r = await client.get("/api/users/me", headers=h)
    assert r.status_code == 401
    # Login is blocked too.
    r = await client.post("/api/auth/login", json={"email": "victim@example.com", "password": "password123"})
    assert r.status_code == 401

    r = await client.post(f"/api/admin/users/{user['id']}/enable", headers=ha)
    assert r.status_code == 200
    tokens = await login_user(client, email="victim@example.com")
    assert tokens["access_token"]


async def test_cannot_disable_or_delete_self(client, test_app):
    admin_id = await _make_admin(client, test_app, email="selfguard@example.com")
    h = await auth_headers_for(client, "selfguard@example.com")
    r = await client.post(f"/api/admin/users/{admin_id}/disable", headers=h)
    assert r.status_code == 409
    r = await client.delete(f"/api/admin/users/{admin_id}", headers=h)
    assert r.status_code == 409
    r = await client.post(f"/api/admin/users/{admin_id}/demote", headers=h)
    assert r.status_code == 409


# ------------------------------------------------------------------ users ---


async def test_user_search_filter_pagination(client, test_app):
    await _make_admin(client, test_app, email="search-admin@example.com")
    for i in range(3):
        await register_user(client, name=f"Ravi {i}", email=f"ravi{i}@example.com", phone=f"+9190000001{i:02d}")
    h = await auth_headers_for(client, "search-admin@example.com")

    r = await client.get("/api/admin/users", params={"q": "ravi1"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1 and body["items"][0]["email"] == "ravi1@example.com"

    r = await client.get("/api/admin/users", params={"limit": 2, "offset": 0}, headers=h)
    assert len(r.json()["items"]) == 2 and r.json()["total"] == 4

    r = await client.get("/api/admin/users", params={"role": "admin"}, headers=h)
    assert r.json()["total"] == 1


async def test_user_detail_and_mutations_are_audited(client, test_app):
    await _make_admin(client, test_app, email="mutator@example.com")
    user = await register_user(client, email="target@example.com")
    h = await auth_headers_for(client, "mutator@example.com")

    r = await client.get(f"/api/admin/users/{user['id']}", headers=h)
    assert r.status_code == 200
    detail = r.json()
    assert detail["user"]["email"] == "target@example.com"
    for key in ("devices", "guardians", "emergencies", "push_tokens", "active_sessions"):
        assert key in detail

    r = await client.patch(f"/api/admin/users/{user['id']}", json={"name": "Renamed"}, headers=h)
    assert r.status_code == 200 and r.json()["name"] == "Renamed"

    r = await client.post(f"/api/admin/users/{user['id']}/force-logout", headers=h)
    assert r.status_code == 200

    r = await client.post(f"/api/admin/users/{user['id']}/reset-password", headers=h)
    assert r.status_code == 200
    temp = r.json()["temp_password"]
    assert len(temp) >= 12
    # Temp password works, and previous sessions were revoked by the reset.
    r = await client.post("/api/auth/login", json={"email": "target@example.com", "password": temp})
    assert r.status_code == 200

    r = await client.post(f"/api/admin/users/{user['id']}/promote", headers=h)
    assert r.status_code == 200 and r.json()["role"] == "admin"
    r = await client.post(f"/api/admin/users/{user['id']}/demote", headers=h)
    assert r.status_code == 200 and r.json()["role"] == "user"

    r = await client.get("/api/admin/audit", params={"action": "user.update"}, headers=h)
    assert r.json()["total"] >= 1


async def test_user_delete_cascades(client, test_app):
    await _make_admin(client, test_app, email="deleter@example.com")
    user = await register_user(client, email="gone@example.com")
    hd = await auth_headers_for(client, "gone@example.com")
    await client.post("/api/devices", json={"name": "Tag"}, headers=hd)
    ha = await auth_headers_for(client, "deleter@example.com")

    r = await client.delete(f"/api/admin/users/{user['id']}", headers=ha)
    assert r.status_code == 204
    assert not await test_app.state.repos.users.get_by_id(user["id"])
    # Devices cascade in Postgres (ON DELETE CASCADE); fakes don't model that,
    # so only the user row + audit entry are asserted here.
    r = await client.get("/api/admin/audit", params={"action": "user.delete"}, headers=ha)
    assert r.json()["total"] == 1


# ---------------------------------------------------------------- devices ---


async def test_device_admin_flow(client, test_app):
    await _make_admin(client, test_app, email="devadmin@example.com")
    await register_user(client, email="devowner@example.com")
    h = await auth_headers_for(client, "devowner@example.com")
    ha = await auth_headers_for(client, "devadmin@example.com")
    r = await client.post("/api/devices", json={"name": "Priya Tag"}, headers=h)
    device_id = r.json()["id"]

    r = await client.get("/api/admin/devices", headers=ha)
    assert r.status_code == 200 and r.json()["total"] == 1

    r = await client.patch(f"/api/admin/devices/{device_id}", json={"name": "Renamed Tag"}, headers=ha)
    assert r.status_code == 200 and r.json()["name"] == "Renamed Tag"

    r = await client.post(f"/api/admin/devices/{device_id}/force-offline", headers=ha)
    assert r.status_code == 200 and r.json()["connection_state"] == "offline"

    r = await client.delete(f"/api/admin/devices/{device_id}", headers=ha)
    assert r.status_code == 204
    assert await test_app.state.repos.devices.get_by_id(device_id) is None


# -------------------------------------------------------------- guardians ---


async def test_guardian_force_status_and_delete(client, test_app):
    await _make_admin(client, test_app, email="gadmin@example.com")
    await register_user(client, email="gowner@example.com")
    ho = await auth_headers_for(client, "gowner@example.com")
    ha = await auth_headers_for(client, "gadmin@example.com")
    r = await client.post("/api/guardians/invite", json={"guardian_email": "stuck@example.com"}, headers=ho)
    gid = r.json()["id"]

    r = await client.get("/api/admin/guardians", params={"status": "pending"}, headers=ha)
    assert r.status_code == 200 and r.json()["total"] == 1

    # Admin resolves the stuck invite without the invited user's action.
    r = await client.patch(f"/api/admin/guardians/{gid}/status", json={"status": "removed"}, headers=ha)
    assert r.status_code == 200 and r.json()["status"] == "removed"

    r = await client.delete(f"/api/admin/guardians/{gid}", headers=ha)
    assert r.status_code == 204


# ------------------------------------------------------------ emergencies ---


async def test_emergency_admin_list_detail_transitions(client, test_app, emitted_admins):
    await _make_admin(client, test_app, email="eadmin@example.com")
    await register_user(client, email="esos@example.com")
    hu = await auth_headers_for(client, "esos@example.com")
    ha = await auth_headers_for(client, "eadmin@example.com")

    r = await client.post("/api/emergencies", json={"trigger_type": "APP_BUTTON"}, headers=hu)
    assert r.status_code == 201
    eid = r.json()["id"]

    r = await client.get("/api/admin/emergencies", params={"status": "active"}, headers=ha)
    assert r.json()["total"] == 1

    r = await client.get(f"/api/admin/emergencies/{eid}", headers=ha)
    assert r.status_code == 200
    detail = r.json()
    assert detail["emergency"]["id"] == eid
    assert [e["to_status"] for e in detail["events"]] == ["active"]

    r = await client.post(f"/api/admin/emergencies/{eid}/ack", headers=ha)
    assert r.status_code == 200 and r.json()["status"] == "acknowledged"
    r = await client.post(f"/api/admin/emergencies/{eid}/resolve", headers=ha)
    assert r.status_code == 200 and r.json()["status"] == "resolved"
    # FSM still applies to admins: resolved is terminal.
    r = await client.post(f"/api/admin/emergencies/{eid}/cancel", headers=ha)
    assert r.status_code == 422

    # Admin channel received every event (live SOS monitor): create + ack + resolve.
    assert [e["type"] for e in emitted_admins] == [
        "emergency-created",
        "emergency-updated",
        "emergency-updated",
    ]


# -------------------------------------------------------------- locations ---


async def test_location_latest_history_purge(client, test_app):
    await _make_admin(client, test_app, email="ladmin@example.com")
    user = await register_user(client, email="luser@example.com")
    h = await auth_headers_for(client, "luser@example.com")
    ha = await auth_headers_for(client, "ladmin@example.com")
    for i in range(3):
        r = await client.post(
            "/api/locations", json={"latitude": 19.0 + i, "longitude": 72.8}, headers=h
        )
        assert r.status_code == 201

    r = await client.get("/api/admin/locations/latest", params={"user_id": user["id"]}, headers=ha)
    assert r.status_code == 200 and r.json()["latitude"] == 21.0

    r = await client.get("/api/admin/locations/history", params={"user_id": user["id"]}, headers=ha)
    assert r.json()["total"] == 3

    r = await client.delete("/api/admin/locations", params={"user_id": user["id"]}, headers=ha)
    assert r.status_code == 200 and r.json()["deleted"] == 3
    r = await client.get("/api/admin/locations/history", params={"user_id": user["id"]}, headers=ha)
    assert r.json()["total"] == 0


# ------------------------------------------------------------------- push ---


async def test_push_tokens_and_broadcast(client, test_app):
    await _make_admin(client, test_app, email="padmin@example.com")
    user = await register_user(client, email="puser@example.com")
    h = await auth_headers_for(client, "puser@example.com")
    ha = await auth_headers_for(client, "padmin@example.com")
    await client.post(
        "/api/push-tokens",
        json={"token": "ExponentPushToken[fake]", "platform": "android"},
        headers=h,
    )

    r = await client.get("/api/admin/push-tokens", params={"user_id": user["id"]}, headers=ha)
    assert r.status_code == 200 and len(r.json()) == 1
    token_id = r.json()[0]["id"]

    r = await client.delete(f"/api/admin/push-tokens/{token_id}", headers=ha)
    assert r.status_code == 204

    r = await client.post(
        "/api/admin/push/send",
        json={"title": "Maintenance", "body": "Back at 2am", "all_users": True},
        headers=ha,
    )
    assert r.status_code == 200
    assert r.json()["audience_size"] == 2

    r = await client.post(
        "/api/admin/push/send",
        json={"title": "Hi", "body": "One user", "user_ids": [user["id"]]},
        headers=ha,
    )
    assert r.status_code == 200 and r.json()["audience_size"] == 1

    r = await client.post(
        "/api/admin/push/send", json={"title": "Hi", "body": "Nobody"}, headers=ha
    )
    assert r.status_code == 409


# ------------------------------------------------------------------ audit ---


async def test_audit_filters(client, test_app):
    admin_id = await _make_admin(client, test_app, email="aadmin@example.com")
    user = await register_user(client, email="aauser@example.com")
    h = await auth_headers_for(client, "aadmin@example.com")
    await client.post(f"/api/admin/users/{user['id']}/force-logout", headers=h)
    await client.post(f"/api/admin/users/{user['id']}/promote", headers=h)

    r = await client.get("/api/admin/audit", headers=h)
    assert r.json()["total"] >= 2
    r = await client.get("/api/admin/audit", params={"actor_id": admin_id}, headers=h)
    assert r.json()["total"] >= 2
    r = await client.get("/api/admin/audit", params={"action": "user.promote"}, headers=h)
    assert r.json()["total"] == 1
    r = await client.get("/api/admin/audit", params={"actor_id": str(uuid.uuid4())}, headers=h)
    assert r.json()["total"] == 0


# --------------------------------------------------------------------- ws ---


def test_admin_websocket_connects_with_admin_flag(test_app):
    import anyio

    from app.core.security import create_access_token

    async def _seed() -> dict:
        user = await test_app.state.repos.users.create(
            email="wsadmin@example.com",
            name="WS Admin",
            phone="+919000000777",
            password_hash="not-used-for-ws",
        )
        await test_app.state.repos.users.set_role(user["id"], "admin")
        return user

    user = anyio.run(_seed)
    settings = test_app.state.settings
    access, _ = create_access_token(
        user_id=str(user["id"]),
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expires_minutes=15,
    )
    c = TestClient(test_app)
    with c.websocket_connect(f"/api/ws?token={access}") as ws:
        msg = ws.receive_text()
        assert '"is_admin":true' in msg.replace(" ", "")


def test_regular_websocket_has_no_admin_flag(test_app):
    import anyio

    from app.core.security import create_access_token

    async def _seed() -> dict:
        return await test_app.state.repos.users.create(
            email="plainflag@example.com",
            name="Plain",
            phone="+919000000779",
            password_hash="not-used-for-ws",
        )

    user = anyio.run(_seed)
    settings = test_app.state.settings
    access, _ = create_access_token(
        user_id=str(user["id"]),
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expires_minutes=15,
    )
    c = TestClient(test_app)
    with c.websocket_connect(f"/api/ws?token={access}") as ws:
        msg = ws.receive_text()
        assert '"is_admin":false' in msg.replace(" ", "")
