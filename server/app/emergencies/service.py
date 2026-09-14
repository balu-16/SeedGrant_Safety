"""Emergencies service — transactional create, guarded status transitions."""

from collections.abc import Awaitable, Callable

from fastapi import BackgroundTasks

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.devices.repository import DevicesRepository
from app.emergencies.repository import EmergenciesRepository
from app.emergencies.schemas import EmergencyStatus, TriggerType
from app.guardians.repository import GuardiansRepository
from app.notifications.service import NotificationService

log = get_logger(__name__)

_ALLOWED: dict[str, set[str]] = {
    EmergencyStatus.ACTIVE.value: {
        EmergencyStatus.ACKNOWLEDGED.value,
        EmergencyStatus.RESOLVED.value,
        EmergencyStatus.CANCELLED.value,
    },
    EmergencyStatus.ACKNOWLEDGED.value: {
        EmergencyStatus.RESOLVED.value,
        EmergencyStatus.CANCELLED.value,
    },
    EmergencyStatus.RESOLVED.value: set(),
    EmergencyStatus.CANCELLED.value: set(),
}


class EmergenciesService:
    def __init__(
        self,
        emergencies: EmergenciesRepository,
        guardians: GuardiansRepository,
        devices: DevicesRepository,
        notifications: NotificationService,
        *,
        emit: Callable[[list[str], dict], Awaitable[None]] | None = None,
        emit_admins: Callable[[dict], Awaitable[None]] | None = None,
        pool: object | None = None,
        background: BackgroundTasks | None = None,
    ) -> None:
        self._emergencies = emergencies
        self._guardians = guardians
        self._devices = devices
        self._notifications = notifications
        self._emit = emit
        self._emit_admins = emit_admins
        self._pool = pool
        self._background = background

    async def _assert_can_read(self, reader_id: str, protected_id: str) -> None:
        if str(reader_id) == str(protected_id):
            return
        ok = await self._guardians.is_accepted_guardian(protected_id, reader_id)
        if not ok:
            raise ForbiddenError("Not authorized for this emergency")

    async def _assert_can_write_status(self, actor_id: str, protected_id: str) -> None:
        # Owner and accepted guardians may ack/resolve/cancel.
        await self._assert_can_read(actor_id, protected_id)

    async def create(
        self,
        protected_user_id: str,
        *,
        trigger_type: TriggerType,
        device_id: str | None,
        latitude: float | None,
        longitude: float | None,
        note: str | None,
    ) -> dict:
        if device_id:
            device = await self._devices.get_by_id(device_id)
            if not device or str(device["owner_id"]) != str(protected_user_id):
                raise ForbiddenError("Device does not belong to you")

        # Transactional when a real pool is available; fakes run without it.
        pool = self._pool
        if pool is not None and hasattr(pool, "acquire"):
            async with pool.acquire() as conn:  # type: ignore[attr-defined]
                async with conn.transaction():
                    emergency = await self._emergencies.create(
                        protected_user_id=protected_user_id,
                        trigger_type=trigger_type.value,
                        device_id=device_id,
                        latitude=latitude,
                        longitude=longitude,
                        note=note,
                        conn=conn,
                    )
                    await self._emergencies.create_event(
                        emergency_id=str(emergency["id"]),
                        actor_user_id=protected_user_id,
                        from_status=None,
                        to_status="active",
                        conn=conn,
                    )
        else:
            emergency = await self._emergencies.create(
                protected_user_id=protected_user_id,
                trigger_type=trigger_type.value,
                device_id=device_id,
                latitude=latitude,
                longitude=longitude,
                note=note,
            )
            await self._emergencies.create_event(
                emergency_id=str(emergency["id"]),
                actor_user_id=protected_user_id,
                from_status=None,
                to_status="active",
            )

        # Push fan-out is slow (sequential FCM HTTP calls, seconds per token),
        # so it runs after the response; the WS emit stays inline because it is
        # local and tests assert on it synchronously.
        await self._dispatch_delivery(self._deliver_created(emergency))
        await self._emit_event([str(emergency["protected_user_id"])], "emergency-created", emergency)
        return emergency

    async def _dispatch_delivery(self, coro: Awaitable[None]) -> None:
        if self._background is not None:
            self._background.add_task(self._await_delivery, coro)
        else:
            await self._await_delivery(coro)

    @staticmethod
    async def _await_delivery(coro: Awaitable[None]) -> None:
        try:
            await coro
        except Exception as e:
            log.warning("Emergency delivery task failed: %s", e)

    async def _deliver_created(self, emergency: dict) -> None:
        try:
            await self._notifications.notify_emergency_created(
                protected_user_id=str(emergency["protected_user_id"]),
                emergency_id=str(emergency["id"]),
                trigger_type=str(emergency["trigger_type"]),
            )
        except Exception as e:
            log.warning("Emergency push delivery failed: %s", e)

    async def _emit_event(self, user_ids: list[str], event_type: str, emergency: dict) -> None:
        # Owners/guardians get it on their channel; admins also get every
        # event for the live SOS monitor.
        if self._emit is not None:
            try:
                await self._emit(user_ids, {"type": event_type, "emergency": _jsonable(emergency)})
            except Exception:
                pass
        if self._emit_admins is not None:
            try:
                await self._emit_admins({"type": event_type, "emergency": _jsonable(emergency)})
            except Exception:
                pass

    async def get(self, reader_id: str, emergency_id: str) -> dict:
        emergency = await self._emergencies.get_by_id(emergency_id)
        if not emergency:
            raise NotFoundError("Emergency not found")
        await self._assert_can_read(reader_id, str(emergency["protected_user_id"]))
        return emergency

    async def list_for(
        self, reader_id: str, protected_id: str, *, limit: int, offset: int, status: str | None
    ) -> tuple[list[dict], int]:
        await self._assert_can_read(reader_id, protected_id)
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return await self._emergencies.list_for_user(protected_id, limit=limit, offset=offset, status=status)

    async def update_status(
        self, actor_id: str, emergency_id: str, status: str, *, actor_is_admin: bool = False
    ) -> dict:
        emergency = await self._emergencies.get_by_id(emergency_id)
        if not emergency:
            raise NotFoundError("Emergency not found")
        if not actor_is_admin:
            await self._assert_can_write_status(actor_id, str(emergency["protected_user_id"]))
        current = str(emergency["status"])
        if status == current:
            return emergency
        if status not in _ALLOWED.get(current, set()):
            raise ValidationAppError(f"Cannot move emergency from {current} to {status}")
        # Status change and its audit event commit together, mirroring create.
        pool = self._pool
        if pool is not None and hasattr(pool, "acquire"):
            async with pool.acquire() as conn:  # type: ignore[attr-defined]
                async with conn.transaction():
                    updated = await self._emergencies.update_status(emergency_id, status, conn=conn)
                    if not updated:
                        raise NotFoundError("Emergency not found")
                    await self._emergencies.create_event(
                        emergency_id=emergency_id,
                        actor_user_id=actor_id,
                        from_status=current,
                        to_status=status,
                        conn=conn,
                    )
        else:
            updated = await self._emergencies.update_status(emergency_id, status)
            if not updated:
                raise NotFoundError("Emergency not found")
            await self._emergencies.create_event(
                emergency_id=emergency_id,
                actor_user_id=actor_id,
                from_status=current,
                to_status=status,
            )
        await self._dispatch_delivery(self._deliver_updated(updated, status))
        await self._emit_event([str(updated["protected_user_id"])], "emergency-updated", updated)
        return updated

    async def _deliver_updated(self, updated: dict, status: str) -> None:
        try:
            await self._notifications.notify_emergency_updated(
                protected_user_id=str(updated["protected_user_id"]),
                emergency_id=str(updated["id"]),
                status=status,
            )
        except Exception as e:
            log.warning("Emergency update push delivery failed: %s", e)


def _jsonable(emergency: dict) -> dict:
    out = dict(emergency)
    for k, v in list(out.items()):
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif not isinstance(v, (str, int, float, bool, type(None))):
            out[k] = str(v)
    return out
