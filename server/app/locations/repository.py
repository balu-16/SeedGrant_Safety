"""Locations repository."""

from datetime import UTC, datetime
from typing import Any

DB = Any


def _row_to_dict(row: Any) -> dict:
    return dict(row)


_COLUMNS = "id, user_id, device_id, latitude, longitude, accuracy_m, source, recorded_at, created_at"


class LocationsRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

    async def create(
        self,
        *,
        user_id: str,
        latitude: float,
        longitude: float,
        accuracy_m: float | None = None,
        source: str = "phone_gps",
        device_id: str | None = None,
        recorded_at: datetime | None = None,
    ) -> dict:
        recorded_at = recorded_at or datetime.now(UTC)
        row = await self._db.fetchrow(
            f"""
            INSERT INTO locations (user_id, device_id, latitude, longitude, accuracy_m, source, recorded_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING {_COLUMNS}
            """,
            user_id,
            device_id,
            latitude,
            longitude,
            accuracy_m,
            source,
            recorded_at,
        )
        return _row_to_dict(row)

    async def latest_for_user(self, user_id: str) -> dict | None:
        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM locations WHERE user_id = $1 ORDER BY recorded_at DESC LIMIT 1",
            user_id,
        )
        return _row_to_dict(row) if row else None

    async def history_for_user(self, user_id: str, *, limit: int, offset: int) -> tuple[list[dict], int]:
        total_row = await self._db.fetchrow("SELECT COUNT(*) AS c FROM locations WHERE user_id = $1", user_id)
        total = int(total_row["c"]) if total_row else 0
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM locations WHERE user_id = $1 ORDER BY recorded_at DESC LIMIT $2 OFFSET $3",
            user_id,
            limit,
            offset,
        )
        return ([_row_to_dict(r) for r in rows], total)

    async def delete_for_user(self, user_id: str) -> int:
        result = await self._db.execute("DELETE FROM locations WHERE user_id = $1", user_id)
        try:
            return int(result.split()[-1])
        except Exception:
            return 0
