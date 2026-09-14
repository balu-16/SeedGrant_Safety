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

    async def list_for_protected(self, protected_user_id: str) -> list[dict]:
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM guardians WHERE protected_user_id = $1 "
            "AND status <> 'removed' ORDER BY created_at",
            protected_user_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def list_for_guardian_user(self, guardian_user_id: str, *, include_pending: bool = False) -> list[dict]:
        status_filter = "IN ('accepted', 'pending')" if include_pending else "= 'accepted'"
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM guardians WHERE guardian_user_id = $1 AND status {status_filter} "
            "ORDER BY created_at",
            guardian_user_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def link_pending_for_email(self, email: str, guardian_user_id: str) -> int:
        """Link a freshly-registered account to pending invites sent to that email."""
        rows = await self._db.fetch(
            "UPDATE guardians SET guardian_user_id = $2, updated_at = now() "
            "WHERE guardian_email = $1 AND status = 'pending' AND guardian_user_id IS NULL "
            "RETURNING id",
            email.strip().lower(),
            guardian_user_id,
        )
        return len(rows)

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

    async def delete(self, guardian_id: str) -> bool:
        result = await self._db.execute("DELETE FROM guardians WHERE id = $1", guardian_id)
        return result != "DELETE 0"

    async def list_all_admin(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        clauses = []
        args: list[Any] = []
        if status:
            args.append(status)
            clauses.append(f"g.status = ${len(args)}")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        total_row = await self._db.fetchrow(f"SELECT COUNT(*) AS c FROM guardians g {where}", *args)
        total = int(total_row["c"]) if total_row else 0
        args.extend([limit, offset])
        rows = await self._db.fetch(
            f"""
            SELECT g.id, g.protected_user_id, g.guardian_user_id, g.guardian_email, g.guardian_name,
                   g.relation, g.status, g.is_primary, g.created_at, g.updated_at,
                   up.email AS protected_email, up.name AS protected_name,
                   ug.email AS guardian_account_email
            FROM guardians g
            JOIN users up ON up.id = g.protected_user_id
            LEFT JOIN users ug ON ug.id = g.guardian_user_id
            {where}
            ORDER BY g.created_at DESC LIMIT ${len(args) - 1} OFFSET ${len(args)}
            """,
            *args,
        )
        return ([_row_to_dict(r) for r in rows], total)
