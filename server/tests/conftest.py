"""Isolated test setup: in-memory fake repositories, no live database.

Never touches production Supabase. All API tests run against FastAPI ASGI app
with fake repos wired into app.state.
"""

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.deps import Repos
from app.main import create_app
from app.notifications.service import NotificationService


def _now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------- fakes ---


class FakeUsers:
    def __init__(self) -> None:
        self.by_id: dict[str, dict] = {}
        self.by_email: dict[str, dict] = {}

    async def create(self, *, email: str, name: str, phone: str, password_hash: str) -> dict:
        uid = str(uuid.uuid4())
        rec = {
            "id": uid,
            "email": email,
            "name": name,
            "phone": phone,
            "password_hash": password_hash,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.by_id[uid] = rec
        self.by_email[email.lower()] = rec
        return {k: rec[k] for k in ("id", "email", "name", "phone", "created_at", "updated_at")}

    async def get_by_id(self, user_id: str) -> dict | None:
        rec = self.by_id.get(str(user_id))
        if not rec:
            return None
        return {k: rec[k] for k in ("id", "email", "name", "phone", "created_at", "updated_at")}

    async def get_by_email(self, email: str) -> dict | None:
        return self.by_email.get(email.strip().lower())

    async def update(self, user_id: str, *, name: str | None, phone: str | None) -> dict | None:
        rec = self.by_id.get(str(user_id))
        if not rec:
            return None
        if name is not None:
            rec["name"] = name
        if phone is not None:
            rec["phone"] = phone
        rec["updated_at"] = _now()
        return await self.get_by_id(user_id)


class FakeRefresh:
    def __init__(self) -> None:
        self.by_jti: dict[str, dict] = {}

    async def create(self, *, user_id: str, jti_hash: str, expires_at: datetime) -> dict:
        rec = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "jti_hash": jti_hash,
            "expires_at": expires_at,
            "revoked_at": None,
            "created_at": _now(),
        }
        self.by_jti[jti_hash] = rec
        return rec

    async def get_by_jti_hash(self, jti_hash: str) -> dict | None:
        return self.by_jti.get(jti_hash)

    async def revoke_by_jti_hash(self, jti_hash: str) -> bool:
        rec = self.by_jti.get(jti_hash)
        if not rec or rec["revoked_at"] is not None:
            return False
        rec["revoked_at"] = _now()
        return True

    async def revoke_all_for_user(self, user_id: str) -> int:
        n = 0
        for rec in self.by_jti.values():
            if str(rec["user_id"]) == str(user_id) and rec["revoked_at"] is None:
                rec["revoked_at"] = _now()
                n += 1
        return n


class FakeDevices:
    def __init__(self) -> None:
        self.by_id: dict[str, dict] = {}

    async def create(self, *, owner_id: str, name: str, device_secret_hash: str | None = None) -> dict:
        did = str(uuid.uuid4())
        rec = {
            "id": did,
            "owner_id": str(owner_id),
            "name": name,
            "battery_pct": None,
            "connection_state": "offline",
            "last_seen_at": None,
            "device_secret_hash": device_secret_hash,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.by_id[did] = rec
        return {
            k: rec[k]
            for k in (
                "id",
                "owner_id",
                "name",
                "battery_pct",
                "connection_state",
                "last_seen_at",
                "created_at",
                "updated_at",
            )
        }

    async def list_by_owner(self, owner_id: str) -> list[dict]:
        return [
            {
                k: r[k]
                for k in (
                    "id",
                    "owner_id",
                    "name",
                    "battery_pct",
                    "connection_state",
                    "last_seen_at",
                    "created_at",
                    "updated_at",
                )
            }
            for r in self.by_id.values()
            if str(r["owner_id"]) == str(owner_id)
        ]

    async def get_by_id(self, device_id: str) -> dict | None:
        rec = self.by_id.get(str(device_id))
        if not rec:
            return None
        return {
            k: rec[k]
            for k in (
                "id",
                "owner_id",
                "name",
                "battery_pct",
                "connection_state",
                "last_seen_at",
                "created_at",
                "updated_at",
            )
        }

    async def get_secret_hash(self, device_id: str) -> str | None:
        rec = self.by_id.get(str(device_id))
        return rec["device_secret_hash"] if rec else None

    async def update(
        self,
        device_id: str,
        *,
        name=None,
        battery_pct=None,
        connection_state=None,
        last_seen: bool = False,
    ) -> dict | None:
        rec = self.by_id.get(str(device_id))
        if not rec:
            return None
        if name is not None:
            rec["name"] = name
        if battery_pct is not None:
            rec["battery_pct"] = battery_pct
        if connection_state is not None:
            rec["connection_state"] = connection_state
        if last_seen:
            rec["last_seen_at"] = _now()
        rec["updated_at"] = _now()
        return await self.get_by_id(device_id)

    async def delete(self, device_id: str) -> bool:
        return self.by_id.pop(str(device_id), None) is not None


class FakeGuardians:
    def __init__(self) -> None:
        self.by_id: dict[str, dict] = {}

    async def create(
        self,
        *,
        protected_user_id: str,
        guardian_email: str,
        guardian_name: str = "",
        relation: str = "",
        is_primary: bool = False,
        guardian_user_id: str | None = None,
    ) -> dict:
        gid = str(uuid.uuid4())
        rec = {
            "id": gid,
            "protected_user_id": str(protected_user_id),
            "guardian_user_id": str(guardian_user_id) if guardian_user_id else None,
            "guardian_email": guardian_email.strip().lower(),
            "guardian_name": guardian_name,
            "relation": relation,
            "status": "pending",
            "is_primary": is_primary,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.by_id[gid] = rec
        return dict(rec)

    async def get_by_id(self, guardian_id: str) -> dict | None:
        rec = self.by_id.get(str(guardian_id))
        return dict(rec) if rec else None

    async def find_by_protected_and_email(self, protected_user_id: str, email: str) -> dict | None:
        for rec in self.by_id.values():
            if (
                str(rec["protected_user_id"]) == str(protected_user_id)
                and rec["guardian_email"] == email.strip().lower()
            ):
                return dict(rec)
        return None

    async def list_for_protected(self, protected_user_id: str) -> list[dict]:
        out = [
            dict(r)
            for r in self.by_id.values()
            if str(r["protected_user_id"]) == str(protected_user_id) and r["status"] != "removed"
        ]
        out.sort(key=lambda r: r["created_at"])
        return out

    async def list_for_guardian_user(self, guardian_user_id: str, *, include_pending: bool = False) -> list[dict]:
        wanted = {"accepted", "pending"} if include_pending else {"accepted"}
        return [
            dict(r)
            for r in self.by_id.values()
            if r["guardian_user_id"] and str(r["guardian_user_id"]) == str(guardian_user_id) and r["status"] in wanted
        ]

    async def link_pending_for_email(self, email: str, guardian_user_id: str) -> int:
        linked = 0
        for rec in self.by_id.values():
            if (
                rec["guardian_email"] == email.strip().lower()
                and rec["status"] == "pending"
                and not rec["guardian_user_id"]
            ):
                rec["guardian_user_id"] = str(guardian_user_id)
                rec["updated_at"] = _now()
                linked += 1
        return linked

    async def is_accepted_guardian(self, protected_user_id: str, guardian_user_id: str) -> bool:
        return any(
            str(r["protected_user_id"]) == str(protected_user_id)
            and r["guardian_user_id"]
            and str(r["guardian_user_id"]) == str(guardian_user_id)
            and r["status"] == "accepted"
            for r in self.by_id.values()
        )

    async def accepted_guardian_user_ids(self, protected_user_id: str) -> list[str]:
        return [
            str(r["guardian_user_id"])
            for r in self.by_id.values()
            if str(r["protected_user_id"]) == str(protected_user_id)
            and r["status"] == "accepted"
            and r["guardian_user_id"]
        ]

    async def update_status(self, guardian_id: str, status: str) -> dict | None:
        rec = self.by_id.get(str(guardian_id))
        if not rec:
            return None
        rec["status"] = status
        rec["updated_at"] = _now()
        return dict(rec)

    async def link_user(self, guardian_id: str, guardian_user_id: str) -> dict | None:
        rec = self.by_id.get(str(guardian_id))
        if not rec:
            return None
        rec["guardian_user_id"] = str(guardian_user_id)
        rec["updated_at"] = _now()
        return dict(rec)


class FakeLocations:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def create(
        self,
        *,
        user_id: str,
        latitude: float,
        longitude: float,
        accuracy_m=None,
        source: str = "phone_gps",
        device_id: str | None = None,
        recorded_at=None,
    ) -> dict:
        rec = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "device_id": str(device_id) if device_id else None,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy_m": accuracy_m,
            "source": source,
            "recorded_at": recorded_at or _now(),
            "created_at": _now(),
        }
        self.items.append(rec)
        return dict(rec)

    async def latest_for_user(self, user_id: str) -> dict | None:
        mine = [r for r in self.items if str(r["user_id"]) == str(user_id)]
        if not mine:
            return None
        mine.sort(key=lambda r: r["recorded_at"], reverse=True)
        return dict(mine[0])

    async def history_for_user(self, user_id: str, *, limit: int, offset: int) -> tuple[list[dict], int]:
        mine = [r for r in self.items if str(r["user_id"]) == str(user_id)]
        mine.sort(key=lambda r: r["recorded_at"], reverse=True)
        return ([dict(r) for r in mine[offset : offset + limit]], len(mine))


class FakeEmergencies:
    def __init__(self) -> None:
        self.by_id: dict[str, dict] = {}
        self.events: list[dict] = []

    async def create(
        self,
        *,
        protected_user_id: str,
        trigger_type: str,
        device_id=None,
        latitude=None,
        longitude=None,
        note=None,
        conn=None,
    ) -> dict:
        eid = str(uuid.uuid4())
        rec = {
            "id": eid,
            "protected_user_id": str(protected_user_id),
            "device_id": str(device_id) if device_id else None,
            "trigger_type": trigger_type,
            "status": "active",
            "latitude": latitude,
            "longitude": longitude,
            "note": note,
            "created_at": _now(),
            "updated_at": _now(),
            "resolved_at": None,
        }
        self.by_id[eid] = rec
        return dict(rec)

    async def create_event(self, *, emergency_id: str, actor_user_id, from_status, to_status, conn=None) -> dict:
        ev = {
            "id": str(uuid.uuid4()),
            "emergency_id": str(emergency_id),
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "from_status": from_status,
            "to_status": to_status,
            "created_at": _now(),
        }
        self.events.append(ev)
        return dict(ev)

    async def get_by_id(self, emergency_id: str) -> dict | None:
        rec = self.by_id.get(str(emergency_id))
        return dict(rec) if rec else None

    async def list_for_user(
        self, protected_user_id: str, *, limit: int, offset: int, status: str | None = None
    ) -> tuple[list[dict], int]:
        mine = [
            r
            for r in self.by_id.values()
            if str(r["protected_user_id"]) == str(protected_user_id) and (status is None or r["status"] == status)
        ]
        mine.sort(key=lambda r: r["created_at"], reverse=True)
        return ([dict(r) for r in mine[offset : offset + limit]], len(mine))

    async def update_status(self, emergency_id: str, status: str, *, conn=None) -> dict | None:
        rec = self.by_id.get(str(emergency_id))
        if not rec:
            return None
        rec["status"] = status
        rec["updated_at"] = _now()
        if status in ("resolved", "cancelled"):
            rec["resolved_at"] = _now()
        return dict(rec)


class FakePushTokens:
    def __init__(self) -> None:
        self.by_hash: dict[str, dict] = {}

    async def upsert(self, *, user_id: str, token_hash: str, platform: str, token: str | None = None) -> dict:
        rec = self.by_hash.get(token_hash)
        if rec:
            rec["user_id"] = str(user_id)
            rec["platform"] = platform
            if token is not None:
                rec["token"] = token
            rec["last_seen_at"] = _now()
            return dict(rec)
        rec = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "token": token,
            "platform": platform,
            "created_at": _now(),
            "last_seen_at": _now(),
        }
        self.by_hash[token_hash] = rec
        return dict(rec)

    async def list_for_user(self, user_id: str) -> list[dict]:
        return [dict(r) for r in self.by_hash.values() if str(r["user_id"]) == str(user_id)]

    async def tokens_for_users(self, user_ids: list[str]) -> list[dict]:
        wanted = {str(u) for u in user_ids}
        return [
            {"user_id": r["user_id"], "token": r["token"], "platform": r["platform"]}
            for r in self.by_hash.values()
            if str(r["user_id"]) in wanted and r.get("token")
        ]

    async def delete_by_token_hash(self, token_hash: str) -> bool:
        return self.by_hash.pop(token_hash, None) is not None

    async def delete(self, user_id: str, token_hash: str) -> bool:
        rec = self.by_hash.get(token_hash)
        if rec and str(rec["user_id"]) == str(user_id):
            del self.by_hash[token_hash]
            return True
        return False


# ---------------------------------------------------------------- app ---


def build_test_repos(settings: Settings) -> Repos:
    return Repos(
        settings=settings,
        pool=None,
        users=FakeUsers(),  # type: ignore[arg-type]
        refresh_tokens=FakeRefresh(),  # type: ignore[arg-type]
        devices=FakeDevices(),  # type: ignore[arg-type]
        guardians=FakeGuardians(),  # type: ignore[arg-type]
        locations=FakeLocations(),  # type: ignore[arg-type]
        emergencies=FakeEmergencies(),  # type: ignore[arg-type]
        push_tokens=FakePushTokens(),  # type: ignore[arg-type]
    )


@pytest.fixture
def settings() -> Settings:
    # _env_file=None keeps the developer's real .env out of test settings.
    return Settings(
        _env_file=None,
        env="test",
        database_url="",
        jwt_secret="test-secret-that-is-long-enough-for-tests-123",
        jwt_algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
        cors_origins=["*"],
        testing=True,
    )


@pytest.fixture
def repos(settings: Settings) -> Repos:
    return build_test_repos(settings)


@pytest.fixture
def emitted() -> list[tuple[list[str], dict]]:
    return []


@pytest.fixture
def test_app(settings: Settings, repos: Repos, emitted: list):
    app = create_app(settings)
    app.state.pool = None
    app.state.repos = repos
    app.state.notifications = NotificationService()

    async def _emit(user_ids: list[str], event: dict) -> None:
        emitted.append((list(user_ids), dict(event)))

    app.state.emit = _emit
    return app


@pytest_asyncio.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_user(
    client: AsyncClient,
    *,
    name="Asha",
    email="asha@example.com",
    phone="+919000000001",
    password="password123",
) -> dict:
    r = await client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "phone": phone, "password": password},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def login_user(client: AsyncClient, *, email="asha@example.com", password="password123") -> dict:
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


async def auth_headers_for(client: AsyncClient, email: str, password: str = "password123") -> dict[str, str]:
    tokens = await login_user(client, email=email, password=password)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
