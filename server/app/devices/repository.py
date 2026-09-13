"""Devices repository."""

from typing import Any

DB = Any


def _row_to_dict(row: Any) -> dict:
    return dict(row)


class DevicesRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

    async def create(self, *, owner_id: str, name: str, device_secret_hash: str | None = None) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO devices (owner_id, name, device_secret_hash)
            VALUES ($1, $2, $3)
            RETURNING id, owner_id, name, battery_pct, connection_state,
                      last_seen_at, created_at, updated_at
            """,
            owner_id,
            name,
            device_secret_hash,
        )
        return _row_to_dict(row)

    async def list_by_owner(self, owner_id: str) -> list[dict]:
        rows = await self._db.fetch(
            "SELECT id, owner_id, name, battery_pct, connection_state, last_seen_at, "
            "created_at, updated_at FROM devices WHERE owner_id = $1 ORDER BY created_at",
            owner_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def get_by_id(self, device_id: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT id, owner_id, name, battery_pct, connection_state, last_seen_at, "
            "created_at, updated_at FROM devices WHERE id = $1",
            device_id,
        )
        return _row_to_dict(row) if row else None

    async def get_secret_hash(self, device_id: str) -> str | None:
        row = await self._db.fetchrow("SELECT device_secret_hash FROM devices WHERE id = $1", device_id)
        if not row:
            return None
        return row["device_secret_hash"]

    async def update(
        self,
        device_id: str,
        *,
        name: str | None = None,
        battery_pct: int | None = None,
        connection_state: str | None = None,
        last_seen: bool = False,
    ) -> dict | None:
        row = await self._db.fetchrow(
            """
            UPDATE devices SET
                name = COALESCE($2, name),
                battery_pct = COALESCE($3, battery_pct),
                connection_state = COALESCE($4, connection_state),
                last_seen_at = CASE WHEN $5 THEN now() ELSE last_seen_at END,
                updated_at = now()
            WHERE id = $1
            RETURNING id, owner_id, name, battery_pct, connection_state,
                      last_seen_at, created_at, updated_at
            """,
            device_id,
            name,
            battery_pct,
            connection_state,
            last_seen,
        )
        return _row_to_dict(row) if row else None

    async def delete(self, device_id: str) -> bool:
        result = await self._db.execute("DELETE FROM devices WHERE id = $1", device_id)
        return result != "DELETE 0"
