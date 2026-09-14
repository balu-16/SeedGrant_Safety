"""Admin service — platform-wide control with an audit entry on every mutation.

Self-protection guardrails: admins cannot disable, demote, or delete their own
account from the portal (prevents last-admin lockout). Everything else is fair
game and recorded in admin_audit_log.
"""

import secrets

from app.admin.repository import AdminAuditRepository, AdminRepository
from app.auth.repository import RefreshTokensRepository
from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.devices.repository import DevicesRepository
from app.emergencies.repository import EmergenciesRepository
from app.emergencies.service import EmergenciesService
from app.guardians.repository import GuardiansRepository
from app.locations.repository import LocationsRepository
from app.notifications.service import NotificationService
from app.push_tokens.repository import PushTokensRepository
from app.users.repository import UsersRepository

log = get_logger(__name__)

_RESOLVE_MAP = {"ack": "acknowledged", "resolve": "resolved", "cancel": "cancelled"}


def _clamp(limit: int, offset: int, *, max_limit: int = 100) -> tuple[int, int]:
    return max(1, min(limit, max_limit)), max(0, offset)


def _user_public(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != "password_hash"}


class AdminService:
    def __init__(
        self,
        *,
        users: UsersRepository,
        refresh_tokens: RefreshTokensRepository,
        devices: DevicesRepository,
        guardians: GuardiansRepository,
        locations: LocationsRepository,
        emergencies: EmergenciesRepository,
        push_tokens: PushTokensRepository,
        audit: AdminAuditRepository,
        admin: AdminRepository,
        notifications: NotificationService,
        emergencies_service: EmergenciesService | None = None,
    ) -> None:
        self._users = users
        self._refresh = refresh_tokens
        self._devices = devices
        self._guardians = guardians
        self._locations = locations
        self._emergencies = emergencies
        self._push_tokens = push_tokens
        self._audit_repo = audit
        self._admin = admin
        self._notifications = notifications
        self._emergencies_service = emergencies_service

    async def _audit(
        self,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        try:
            await self._audit_repo.create(
                actor_user_id=actor_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
            )
        except Exception as e:
            # Audit must never break the operation, but it must be loud.
            log.error("Admin audit write failed (%s): %s", action, e)

    # ------------------------------------------------------------- stats ---

    async def stats(self) -> dict:
        return {
            "totals": await self._admin.stats(),
            "series": await self._admin.series(days=30),
        }

    async def health(self, *, settings, pool) -> dict:
        database = "not_configured"
        if pool is not None and hasattr(pool, "acquire"):
            try:
                async with pool.acquire() as conn:  # type: ignore[attr-defined]
                    await conn.fetchval("SELECT 1")
                database = "up"
            except Exception:
                database = "down"
        elif settings.testing:
            database = "fake"
        return {
            "status": "ok" if database in ("up", "fake") else "degraded",
            "env": settings.env,
            "database": database,
            "push_provider": settings.push_provider,
            "fcm_configured": bool(settings.fcm_project_id),
            "admin_bootstrap_emails": len(settings.admin_emails),
        }

    # -------------------------------------------------------------- users ---

    async def list_users(
        self, *, q: str | None, role: str | None, disabled: bool | None, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        limit, offset = _clamp(limit, offset)
        return await self._users.list_all(q=q, role=role, disabled=disabled, limit=limit, offset=offset)

    async def user_detail(self, user_id: str) -> dict:
        user = await self._users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return {
            "user": _user_public(user),
            "devices": await self._devices.list_by_owner(user_id),
            "guardians": await self._guardians.list_for_protected(user_id),
            "emergencies": (await self._emergencies.list_for_user(user_id, limit=10, offset=0, status=None))[0],
            "push_tokens": await self._push_tokens.list_for_user(user_id),
            "active_sessions": await self._refresh.list_active_for_user(user_id),
        }

    async def update_user(self, actor_id: str, user_id: str, *, name: str | None, phone: str | None) -> dict:
        updated = await self._users.update(user_id, name=name, phone=phone)
        if not updated:
            raise NotFoundError("User not found")
        touched = {"name": name is not None, "phone": phone is not None}
        await self._audit(actor_id, "user.update", "user", user_id, touched)
        return updated

    async def set_disabled(self, actor_id: str, user_id: str, disabled: bool) -> dict:
        if str(actor_id) == str(user_id):
            raise ConflictError("You cannot disable your own account")
        target = await self._users.get_by_id(user_id)
        if not target:
            raise NotFoundError("User not found")
        updated = await self._users.set_disabled(user_id, disabled)
        if not updated:
            raise NotFoundError("User not found")
        if disabled:
            await self._refresh.revoke_all_for_user(user_id)
        await self._audit(actor_id, "user.disable" if disabled else "user.enable", "user", user_id)
        return updated

    async def force_logout(self, actor_id: str, user_id: str) -> int:
        target = await self._users.get_by_id(user_id)
        if not target:
            raise NotFoundError("User not found")
        revoked = await self._refresh.revoke_all_for_user(user_id)
        await self._audit(actor_id, "user.force_logout", "user", user_id, {"revoked": revoked})
        return revoked

    async def reset_password(self, actor_id: str, user_id: str) -> str:
        target = await self._users.get_by_id(user_id)
        if not target:
            raise NotFoundError("User not found")
        temp_password = secrets.token_urlsafe(12)
        from app.core.security import hash_password

        await self._users.set_password(user_id, hash_password(temp_password))
        await self._refresh.revoke_all_for_user(user_id)
        await self._audit(actor_id, "user.reset_password", "user", user_id)
        # Shown once to the admin in the response; there is no email channel.
        return temp_password

    async def set_role(self, actor_id: str, user_id: str, role: str) -> dict:
        if role == "admin" and str(actor_id) == str(user_id):
            raise ConflictError("You already are an admin")
        if role == "user" and str(actor_id) == str(user_id):
            raise ConflictError("You cannot demote your own account")
        target = await self._users.get_by_id(user_id)
        if not target:
            raise NotFoundError("User not found")
        updated = await self._users.set_role(user_id, role)
        if not updated:
            raise NotFoundError("User not found")
        await self._audit(actor_id, "user.promote" if role == "admin" else "user.demote", "user", user_id)
        return updated

    async def delete_user(self, actor_id: str, user_id: str) -> None:
        if str(actor_id) == str(user_id):
            raise ConflictError("You cannot delete your own account")
        target = await self._users.get_by_id(user_id)
        if not target:
            raise NotFoundError("User not found")
        await self._refresh.revoke_all_for_user(user_id)
        deleted = await self._users.delete(user_id)
        if not deleted:
            raise NotFoundError("User not found")
        await self._audit(actor_id, "user.delete", "user", user_id, {"email": str(target.get("email", ""))})

    # ------------------------------------------------------------ devices ---

    async def list_devices(
        self, *, connection_state: str | None, low_battery: bool, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        limit, offset = _clamp(limit, offset)
        return await self._devices.list_all_admin(
            connection_state=connection_state, low_battery=low_battery, limit=limit, offset=offset
        )

    async def update_device(self, actor_id: str, device_id: str, *, name: str) -> dict:
        updated = await self._devices.update(device_id, name=name)
        if not updated:
            raise NotFoundError("Device not found")
        await self._audit(actor_id, "device.update", "device", device_id, {"name": name})
        return updated

    async def force_offline(self, actor_id: str, device_id: str) -> dict:
        updated = await self._devices.update(device_id, connection_state="offline")
        if not updated:
            raise NotFoundError("Device not found")
        await self._audit(actor_id, "device.force_offline", "device", device_id)
        return updated

    async def delete_device(self, actor_id: str, device_id: str) -> None:
        deleted = await self._devices.delete(device_id)
        if not deleted:
            raise NotFoundError("Device not found")
        await self._audit(actor_id, "device.delete", "device", device_id)

    # ----------------------------------------------------------- guardians ---

    async def list_guardians(self, *, status: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
        limit, offset = _clamp(limit, offset)
        return await self._guardians.list_all_admin(status=status, limit=limit, offset=offset)

    async def force_guardian_status(self, actor_id: str, guardian_id: str, status: str) -> dict:
        link = await self._guardians.get_by_id(guardian_id)
        if not link:
            raise NotFoundError("Guardian link not found")
        updated = await self._guardians.update_status(guardian_id, status)
        if not updated:
            raise NotFoundError("Guardian link not found")
        await self._audit(
            actor_id,
            "guardian.force_status",
            "guardian",
            guardian_id,
            {"from": str(link["status"]), "to": status},
        )
        return updated

    async def delete_guardian(self, actor_id: str, guardian_id: str) -> None:
        deleted = await self._guardians.delete(guardian_id)
        if not deleted:
            raise NotFoundError("Guardian link not found")
        await self._audit(actor_id, "guardian.delete", "guardian", guardian_id)

    # --------------------------------------------------------- emergencies ---

    async def list_emergencies(
        self, *, status: str | None, trigger_type: str | None, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        limit, offset = _clamp(limit, offset)
        return await self._emergencies.list_all_admin(
            status=status, trigger_type=trigger_type, limit=limit, offset=offset
        )

    async def emergency_detail(self, emergency_id: str) -> dict:
        emergency = await self._emergencies.get_by_id(emergency_id)
        if not emergency:
            raise NotFoundError("Emergency not found")
        events = await self._emergencies.list_events(emergency_id)
        enriched = dict(emergency)
        user = await self._users.get_by_id(str(emergency["protected_user_id"]))
        if user:
            enriched["protected_email"] = user["email"]
            enriched["protected_name"] = user["name"]
            enriched["protected_phone"] = user["phone"]
        return {"emergency": enriched, "events": events}

    async def emergency_transition(self, actor_id: str, emergency_id: str, action: str) -> dict:
        if self._emergencies_service is None:
            raise ConflictError("Emergency service unavailable")
        status = _RESOLVE_MAP.get(action)
        if status is None:
            raise ConflictError(f"Unknown emergency action: {action}")
        updated = await self._emergencies_service.update_status(
            actor_id, emergency_id, status, actor_is_admin=True
        )
        await self._audit(actor_id, f"emergency.{action}", "emergency", emergency_id, {"to": status})
        return updated

    # ----------------------------------------------------------- locations ---

    async def latest_location(self, user_id: str) -> dict | None:
        return await self._locations.latest_for_user(user_id)

    async def location_history(self, user_id: str, *, limit: int, offset: int) -> tuple[list[dict], int]:
        limit, offset = _clamp(limit, offset)
        return await self._locations.history_for_user(user_id, limit=limit, offset=offset)

    async def purge_locations(self, actor_id: str, user_id: str) -> int:
        deleted = await self._locations.delete_for_user(user_id)
        await self._audit(actor_id, "location.purge", "user", user_id, {"deleted": deleted})
        return deleted

    # ---------------------------------------------------------------- push ---

    async def list_push_tokens(self, user_id: str) -> list[dict]:
        return await self._push_tokens.list_for_user(user_id)

    async def delete_push_token(self, actor_id: str, token_id: str) -> None:
        deleted = await self._push_tokens.delete_by_id(token_id)
        if not deleted:
            raise NotFoundError("Push token not found")
        await self._audit(actor_id, "push.delete_token", "push_token", token_id)

    async def send_push(
        self, actor_id: str, *, title: str, body: str, user_ids: list[str] | None, all_users: bool
    ) -> dict:
        if all_users:
            audience = await self._admin.all_user_ids()
        elif user_ids:
            audience = [str(u) for u in user_ids]
        else:
            raise ConflictError("Provide user_ids or all_users=true")
        result = await self._notifications.send_to_users(
            user_ids=audience, title=title, body=body, data={"kind": "admin-broadcast"}
        )
        await self._audit(
            actor_id,
            "push.send",
            "user",
            None,
            {"audience_size": len(audience), "all_users": all_users, "title": title},
        )
        return {
            "provider": result.provider,
            "message_id": result.message_id,
            "delivered_to": result.delivered_to,
            "audience_size": len(audience),
        }

    # --------------------------------------------------------------- audit ---

    async def list_audit(
        self, *, actor_id: str | None, action: str | None, target_type: str | None, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        limit, offset = _clamp(limit, offset)
        return await self._audit_repo.list_all(
            actor_id=actor_id, action=action, target_type=target_type, limit=limit, offset=offset
        )
