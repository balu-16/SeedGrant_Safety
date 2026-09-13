"""Emergencies repository with transactional create + audit events."""

from typing import Any

DB = Any


def _row_to_dict(row: Any) -> dict:
    return dict(row)


_COLUMNS = (
    "id, protected_user_id, device_id, trigger_type, status, latitude, longitude, "
    "note, created_at, updated_at, resolved_at"
)


class EmergenciesRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

    async def create(
        self,
        *,
        protected_user_id: str,
        trigger_type: str,
        device_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        note: str | None = None,
        conn: Any = None,
    ) -> dict:
        db = conn or self._db
        row = await db.fetchrow(
            f"""
            INSERT INTO emergencies
                (protected_user_id, device_id, trigger_type, status, latitude, longitude, note)
            VALUES ($1, $2, $3, 'active', $4, $5, $6)
            RETURNING {_COLUMNS}
            """,
            protected_user_id,
            device_id,
            trigger_type,
            latitude,
            longitude,
            note,
        )
        return _row_to_dict(row)

    async def create_event(
        self,
        *,
        emergency_id: str,
        actor_user_id: str | None,
        from_status: str | None,
        to_status: str,
        conn: Any = None,
    ) -> dict:
        db = conn or self._db
        row = await db.fetchrow(
            """
            INSERT INTO emergency_events (emergency_id, actor_user_id, from_status, to_status)
            VALUES ($1, $2, $3, $4)
            RETURNING id, emergency_id, actor_user_id, from_status, to_status, created_at
            """,
            emergency_id,
            actor_user_id,
            from_status,
            to_status,
        )
        return _row_to_dict(row)

    async def get_by_id(self, emergency_id: str) -> dict | None:
        row = await self._db.fetchrow(f"SELECT {_COLUMNS} FROM emergencies WHERE id = $1", emergency_id)
        return _row_to_dict(row) if row else None

    async def list_for_user(
        self, protected_user_id: str, *, limit: int, offset: int, status: str | None = None
    ) -> tuple[list[dict], int]:
        if status:
            total_row = await self._db.fetchrow(
                "SELECT COUNT(*) AS c FROM emergencies WHERE protected_user_id = $1 AND status = $2",
                protected_user_id,
                status,
            )
            rows = await self._db.fetch(
                f"SELECT {_COLUMNS} FROM emergencies WHERE protected_user_id = $1 AND status = $2 "
                "ORDER BY created_at DESC LIMIT $3 OFFSET $4",
                protected_user_id,
                status,
                limit,
                offset,
            )
        else:
            total_row = await self._db.fetchrow(
                "SELECT COUNT(*) AS c FROM emergencies WHERE protected_user_id = $1",
                protected_user_id,
            )
            rows = await self._db.fetch(
                f"SELECT {_COLUMNS} FROM emergencies WHERE protected_user_id = $1 "
                "ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                protected_user_id,
                limit,
                offset,
            )
        total = int(total_row["c"]) if total_row else 0
        return ([_row_to_dict(r) for r in rows], total)

    async def update_status(self, emergency_id: str, status: str, *, conn: Any = None) -> dict | None:
        db = conn or self._db
        row = await db.fetchrow(
            f"""
            UPDATE emergencies SET status = $2, updated_at = now(),
                resolved_at = CASE WHEN $2 IN ('resolved', 'cancelled') THEN now() ELSE resolved_at END
            WHERE id = $1
            RETURNING {_COLUMNS}
            """,
            emergency_id,
            status,
        )
        return _row_to_dict(row) if row else None
