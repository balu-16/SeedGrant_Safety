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
            "role": "user",
            "disabled_at": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.by_id[uid] = rec
        self.by_email[email.lower()] = rec
        return {k: rec[k] for k in ("id", "email", "name", "phone", "role", "created_at", "updated_at")}

    @staticmethod
    def _public(rec: dict) -> dict:
        return {k: rec[k] for k in ("id", "email", "name", "phone", "role", "disabled_at", "created_at", "updated_at")}

    async def get_by_id(self, user_id: str) -> dict | None:
        rec = self.by_id.get(str(user_id))
        if not rec:
            return None
        return self._public(rec)

    async def get_by_email(self, email: str) -> dict | None:
        rec = self.by_email.get(email.strip().lower())
        return dict(rec) if rec else None

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

    async def list_all(
        self,
        *,
        q: str | None = None,
        role: str | None = None,
        disabled: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        def _match(rec: dict) -> bool:
            if q:
                needle = q.lower()
                if needle not in rec["email"].lower() and needle not in rec["name"].lower():
                    return False
            if role and rec["role"] != role:
                return False
            if disabled is not None and (rec["disabled_at"] is not None) != disabled:
                return False
            return True

        matched = sorted(
            (r for r in self.by_id.values() if _match(r)),
            key=lambda r: r["created_at"],
            reverse=True,
        )
        return ([self._public(r) for r in matched[offset : offset + limit]], len(matched))

    async def set_role(self, user_id: str, role: str) -> dict | None:
        rec = self.by_id.get(str(user_id))
        if not rec:
            return None
        rec["role"] = role
        rec["updated_at"] = _now()
        return await self.get_by_id(user_id)

    async def set_disabled(self, user_id: str, disabled: bool) -> dict | None:
        rec = self.by_id.get(str(user_id))
        if not rec:
            return None
        rec["disabled_at"] = _now() if disabled else None
        rec["updated_at"] = _now()
        return await self.get_by_id(user_id)

    async def set_password(self, user_id: str, password_hash: str) -> bool:
        rec = self.by_id.get(str(user_id))
        if not rec:
            return False
        rec["password_hash"] = password_hash
        return True

    async def delete(self, user_id: str) -> bool:
        rec = self.by_id.pop(str(user_id), None)
        if not rec:
            return False
        self.by_email.pop(rec["email"].lower(), None)
        return True

    async def promote_by_emails(self, emails: list[str]) -> int:
        promoted = 0
        for email in emails:
            rec = self.by_email.get(email.strip().lower())
            if rec and rec["role"] != "admin":
                rec["role"] = "admin"
                promoted += 1
        return promoted


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

    async def list_active_for_user(self, user_id: str) -> list[dict]:
        return [
            {k: r[k] for k in ("id", "expires_at", "revoked_at", "created_at")}
            for r in self.by_jti.values()
            if str(r["user_id"]) == str(user_id) and r["revoked_at"] is None and r["expires_at"] > _now()
        ]


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

    async def list_all_admin(
        self,
        *,
        connection_state: str | None = None,
        low_battery: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        def _match(r: dict) -> bool:
            if connection_state and r["connection_state"] != connection_state:
                return False
            if low_battery and (r["battery_pct"] is None or r["battery_pct"] >= 20):
                return False
            return True

        matched = sorted(
            (r for r in self.by_id.values() if _match(r)),
            key=lambda r: r["created_at"],
            reverse=True,
        )
        out = []
        for r in matched[offset : offset + limit]:
            d = await self.get_by_id(r["id"])
            out.append({**d, "owner_email": None, "owner_name": None})
        return (out, len(matched))


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

    async def delete(self, guardian_id: str) -> bool:
        return self.by_id.pop(str(guardian_id), None) is not None

    async def list_all_admin(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        matched = [r for r in self.by_id.values() if (status is None or r["status"] == status)]
        matched.sort(key=lambda r: r["created_at"], reverse=True)
        out = []
        for r in matched[offset : offset + limit]:
            d = dict(r)
            d["protected_email"] = None
            d["protected_name"] = None
            d["guardian_account_email"] = None
            out.append(d)
        return (out, len(matched))


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

    async def delete_for_user(self, user_id: str) -> int:
        before = len(self.items)
        self.items = [r for r in self.items if str(r["user_id"]) != str(user_id)]
        return before - len(self.items)


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

    async def list_events(self, emergency_id: str) -> list[dict]:
        return [
            dict(ev)
            for ev in sorted(
                (e for e in self.events if str(e["emergency_id"]) == str(emergency_id)),
                key=lambda e: e["created_at"],
            )
        ]

    async def list_all_admin(
        self,
        *,
        status: str | None = None,
        trigger_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        def _match(r: dict) -> bool:
            if status and r["status"] != status:
                return False
            if trigger_type and r["trigger_type"] != trigger_type:
                return False
            return True

        matched = sorted(
            (r for r in self.by_id.values() if _match(r)),
            key=lambda r: r["created_at"],
            reverse=True,
        )
        out = []
        for r in matched[offset : offset + limit]:
            d = dict(r)
            d["protected_email"] = None
            d["protected_name"] = None
            d["protected_phone"] = None
            out.append(d)
        return (out, len(matched))


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

    async def get_by_id(self, token_id: str) -> dict | None:
        for rec in self.by_hash.values():
            if str(rec["id"]) == str(token_id):
                return dict(rec)
        return None

    async def delete_by_id(self, token_id: str) -> bool:
        for token_hash, rec in list(self.by_hash.items()):
            if str(rec["id"]) == str(token_id):
                del self.by_hash[token_hash]
                return True
        return False

    async def count_all(self) -> int:
        return len(self.by_hash)


class FakeAudit:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def create(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        target_type: str,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> dict:
        rec = {
            "id": str(uuid.uuid4()),
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "created_at": _now(),
        }
        self.items.append(rec)
        return dict(rec)

    async def list_all(
        self,
        *,
        actor_id: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        def _match(r: dict) -> bool:
            if actor_id and str(r["actor_user_id"]) != str(actor_id):
                return False
            if action and r["action"] != action:
                return False
            if target_type and r["target_type"] != target_type:
                return False
            return True

        matched = sorted(
            (r for r in self.items if _match(r)),
            key=lambda r: r["created_at"],
            reverse=True,
        )
        out = []
        for r in matched[offset : offset + limit]:
            d = dict(r)
            d["actor_email"] = None
            d["actor_name"] = None
            out.append(d)
        return (out, len(matched))


class FakeAdmin:
    """Cross-domain aggregates computed from the other fakes."""

    def __init__(self, users: FakeUsers, devices: FakeDevices, guardians: FakeGuardians,
                 emergencies: FakeEmergencies, push_tokens: FakePushTokens) -> None:
        self._users = users
        self._devices = devices
        self._guardians = guardians
        self._emergencies = emergencies
        self._push = push_tokens

    def _within(self, dt, days: int) -> bool:
        return (_now() - dt).total_seconds() <= days * 86400

    async def stats(self) -> dict:
        users = list(self._users.by_id.values())
        devices = list(self._devices.by_id.values())
        guardians = list(self._guardians.by_id.values())
        emergencies = list(self._emergencies.by_id.values())
        return {
            "users_total": len(users),
            "users_new_7d": sum(1 for u in users if self._within(u["created_at"], 7)),
            "users_new_30d": sum(1 for u in users if self._within(u["created_at"], 30)),
            "devices_total": len(devices),
            "devices_online": sum(1 for d in devices if d["connection_state"] == "online"),
            "guardians_accepted": sum(1 for g in guardians if g["status"] == "accepted"),
            "guardians_pending": sum(1 for g in guardians if g["status"] == "pending"),
            "emergencies_open": sum(1 for e in emergencies if e["status"] in ("active", "acknowledged")),
            "emergencies_30d": sum(1 for e in emergencies if self._within(e["created_at"], 30)),
            "push_tokens_total": await self._push.count_all(),
        }

    async def series(self, *, days: int = 30) -> list[dict]:
        return [
            {"day": f"2026-01-{d:02d}", "signups": 0, "emergencies": 0}
            for d in range(1, days + 1)
        ]

    async def all_user_ids(self) -> list[str]:
        return list(self._users.by_id.keys())


# ---------------------------------------------------------------- app ---


def build_test_repos(settings: Settings) -> Repos:
    users = FakeUsers()
    devices = FakeDevices()
    guardians = FakeGuardians()
    emergencies = FakeEmergencies()
    push_tokens = FakePushTokens()
    return Repos(
        settings=settings,
        pool=None,
        users=users,  # type: ignore[arg-type]
        refresh_tokens=FakeRefresh(),  # type: ignore[arg-type]
        devices=devices,  # type: ignore[arg-type]
        guardians=guardians,  # type: ignore[arg-type]
        locations=FakeLocations(),  # type: ignore[arg-type]
        emergencies=emergencies,  # type: ignore[arg-type]
        push_tokens=push_tokens,  # type: ignore[arg-type]
        audit=FakeAudit(),  # type: ignore[arg-type]
        admin=FakeAdmin(users, devices, guardians, emergencies, push_tokens),  # type: ignore[arg-type]
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
def emitted_admins() -> list[dict]:
    return []


@pytest.fixture
def test_app(settings: Settings, repos: Repos, emitted: list, emitted_admins: list):
    app = create_app(settings)
    app.state.pool = None
    app.state.repos = repos
    app.state.notifications = NotificationService()

    async def _emit(user_ids: list[str], event: dict) -> None:
        emitted.append((list(user_ids), dict(event)))

    async def _emit_admins(event: dict) -> None:
        emitted_admins.append(dict(event))

    app.state.emit = _emit
    app.state.emit_admins = _emit_admins
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
