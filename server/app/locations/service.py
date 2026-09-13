"""Locations service — owner/guardian authorization + device ownership checks."""

from datetime import datetime

from app.core.exceptions import ForbiddenError
from app.devices.repository import DevicesRepository
from app.guardians.repository import GuardiansRepository
from app.locations.repository import LocationsRepository


class LocationsService:
    def __init__(
        self,
        locations: LocationsRepository,
        guardians: GuardiansRepository,
        devices: DevicesRepository,
    ) -> None:
        self._locations = locations
        self._guardians = guardians
        self._devices = devices

    async def _assert_can_write(self, user_id: str, device_id: str | None) -> None:
        if not device_id:
            return
        device = await self._devices.get_by_id(device_id)
        if not device or str(device["owner_id"]) != str(user_id):
            raise ForbiddenError("Device does not belong to you")

    async def _assert_can_read(self, reader_id: str, protected_id: str) -> None:
        if str(reader_id) == str(protected_id):
            return
        ok = await self._guardians.is_accepted_guardian(protected_id, reader_id)
        if not ok:
            raise ForbiddenError("Not authorized to view this location")

    async def submit(
        self,
        user_id: str,
        *,
        latitude: float,
        longitude: float,
        accuracy_m: float | None,
        source: str,
        device_id: str | None,
        recorded_at: datetime | None,
    ) -> dict:
        await self._assert_can_write(user_id, device_id)
        return await self._locations.create(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            accuracy_m=accuracy_m,
            source=source,
            device_id=device_id,
            recorded_at=recorded_at,
        )

    async def latest(self, reader_id: str, protected_id: str) -> dict | None:
        await self._assert_can_read(reader_id, protected_id)
        return await self._locations.latest_for_user(protected_id)

    async def history(self, reader_id: str, protected_id: str, *, limit: int, offset: int) -> tuple[list[dict], int]:
        await self._assert_can_read(reader_id, protected_id)
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return await self._locations.history_for_user(protected_id, limit=limit, offset=offset)
