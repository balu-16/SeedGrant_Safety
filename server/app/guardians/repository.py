"""Guardians repository."""

from typing import Any

DB = Any


def _row_to_dict(row: Any) -> dict:
    return dict(row)


_COLUMNS = (
    "id, protected_user_id, guardian_user_id, guardian_email, guardian_name, "
    "relation, status, is_primary, created_at, updated_at"
)


class GuardiansRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

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
        row = await self._db.fetchrow(
            f"""
            INSERT INTO guardians
                (protected_user_id, guardian_user_id, guardian_email, guardian_name,
                 relation, status, is_primary)
            VALUES ($1, $2, $3, $4, $5, 'pending', $6)
            RETURNING {_COLUMNS}
            """,
            protected_user_id,
            guardian_user_id,
            guardian_email,
            guardian_name,
            relation,
            is_primary,
        )
        return _row_to_dict(row)

    async def get_by_id(self, guardian_id: str) -> dict | None:
        row = await self._db.fetchrow(f"SELECT {_COLUMNS} FROM guardians WHERE id = $1", guardian_id)
        return _row_to_dict(row) if row else None

    async def find_by_protected_and_email(self, protected_user_id: str, email: str) -> dict | None:
        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM guardians WHERE protected_user_id = $1 AND guardian_email = $2",
            protected_user_id,
            email,
        )
        return _row_to_dict(row) if row else None

    async def list_for_protected(self, protected_user_id: str, *, include_removed: bool = False) -> list[dict]:
        if include_removed:
            rows = await self._db.fetch(
                f"SELECT {_COLUMNS} FROM guardians WHERE protected_user_id = $1 ORDER BY created_at",
                protected_user_id,
            )
        else:
            rows = await self._db.fetch(
                f"SELECT {_COLUMNS} FROM guardians WHERE protected_user_id = $1 "
                "AND status <> 'removed' ORDER BY created_at",
                protected_user_id,
            )
        return [_row_to_dict(r) for r in rows]

    async def list_for_guardian_user(self, guardian_user_id: str) -> list[dict]:
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM guardians WHERE guardian_user_id = $1 AND status = 'accepted' ORDER BY created_at",
            guardian_user_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def is_accepted_guardian(self, protected_user_id: str, guardian_user_id: str) -> bool:
        row = await self._db.fetchrow(
            "SELECT 1 FROM guardians WHERE protected_user_id = $1 "
            "AND guardian_user_id = $2 AND status = 'accepted' LIMIT 1",
            protected_user_id,
            guardian_user_id,
        )
        return row is not None

    async def accepted_guardian_user_ids(self, protected_user_id: str) -> list[str]:
        """Linked user ids of accepted guardians (push audience for emergencies)."""
        rows = await self._db.fetch(
            "SELECT guardian_user_id FROM guardians WHERE protected_user_id = $1 "
            "AND status = 'accepted' AND guardian_user_id IS NOT NULL",
            protected_user_id,
        )
        return [str(r["guardian_user_id"]) for r in rows]

    async def update_status(self, guardian_id: str, status: str) -> dict | None:
        row = await self._db.fetchrow(
            f"UPDATE guardians SET status = $2, updated_at = now() WHERE id = $1 RETURNING {_COLUMNS}",
            guardian_id,
            status,
        )
        return _row_to_dict(row) if row else None

    async def link_user(self, guardian_id: str, guardian_user_id: str) -> dict | None:
        row = await self._db.fetchrow(
            f"UPDATE guardians SET guardian_user_id = $2, updated_at = now() WHERE id = $1 RETURNING {_COLUMNS}",
            guardian_id,
            guardian_user_id,
        )
        return _row_to_dict(row) if row else None
