"""Devices service — ownership validation lives here, never in routers."""

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import hash_password as hash_secret
from app.core.security import verify_password
from app.devices.repository import DevicesRepository


class DevicesService:
    def __init__(self, devices: DevicesRepository) -> None:
        self._devices = devices

    async def _get_owned(self, user_id: str, device_id: str) -> dict:
        device = await self._devices.get_by_id(device_id)
        if not device:
            raise NotFoundError("Device not found")
        if str(device["owner_id"]) != str(user_id):
            raise ForbiddenError("Not your device")
        return device

    async def register(self, user_id: str, *, name: str, device_secret: str | None) -> dict:
        secret_hash = hash_secret(device_secret) if device_secret else None
        return await self._devices.create(owner_id=user_id, name=name, device_secret_hash=secret_hash)

    async def list_mine(self, user_id: str) -> list[dict]:
        return await self._devices.list_by_owner(user_id)

    async def get_mine(self, user_id: str, device_id: str) -> dict:
        return await self._get_owned(user_id, device_id)

    async def update_mine(
        self,
        user_id: str,
        device_id: str,
        *,
        name: str | None,
        battery_pct: int | None,
        connection_state: str | None,
    ) -> dict:
        await self._get_owned(user_id, device_id)
        # A profile edit is not a liveness signal — only pair() stamps last_seen.
        updated = await self._devices.update(
            device_id,
            name=name,
            battery_pct=battery_pct,
            connection_state=connection_state,
        )
        if not updated:
            raise NotFoundError("Device not found")
        return updated

    async def pair(self, user_id: str, device_id: str, *, device_secret: str | None) -> dict:
        device = await self._get_owned(user_id, device_id)
        stored = await self._devices.get_secret_hash(device_id)
        if stored:
            if not device_secret or not verify_password(device_secret, stored):
                # The user is authenticated; only the device credential failed.
                raise ForbiddenError("Invalid device secret")
        updated = await self._devices.update(device_id, connection_state="online", last_seen=True)
        return updated or device

    async def unpair(self, user_id: str, device_id: str) -> None:
        await self._get_owned(user_id, device_id)
        ok = await self._devices.delete(device_id)
        if not ok:
            raise NotFoundError("Device not found")

    async def status(self, user_id: str, device_id: str) -> dict:
        device = await self._get_owned(user_id, device_id)
        return {
            "id": device["id"],
            "name": device["name"],
            "connected": device["connection_state"] == "online",
            "battery_pct": device["battery_pct"],
            "connection_state": device["connection_state"],
            "last_seen_at": device["last_seen_at"],
        }
