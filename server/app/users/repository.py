"""Users repository — parameterized asyncpg queries only."""

from typing import Any

DB = Any  # asyncpg.Pool | asyncpg.Connection (duck-typed for transactions)


def _row_to_dict(row: Any) -> dict:
    return dict(row)


_PUBLIC_COLUMNS = "id, email, name, phone, role, disabled_at, created_at, updated_at"


class UsersRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

    async def create(self, *, email: str, name: str, phone: str, password_hash: str) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO users (email, name, phone, password_hash)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, name, phone, role, created_at, updated_at
            """,
            email,
            name,
            phone,
            password_hash,
        )
        return _row_to_dict(row)

    async def get_by_id(self, user_id: str) -> dict | None:
        row = await self._db.fetchrow(
            f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE id = $1",
            user_id,
        )
        return _row_to_dict(row) if row else None

    async def get_by_email(self, email: str) -> dict | None:
        row = await self._db.fetchrow(
            f"SELECT {_PUBLIC_COLUMNS}, password_hash FROM users WHERE email = $1",
            email,
        )
        return _row_to_dict(row) if row else None

    async def update(self, user_id: str, *, name: str | None, phone: str | None) -> dict | None:
        row = await self._db.fetchrow(
            """
            UPDATE users SET
                name = COALESCE($2, name),
                phone = COALESCE($3, phone),
                updated_at = now()
            WHERE id = $1
            RETURNING id, email, name, phone, created_at, updated_at
            """,
            user_id,
            name,
            phone,
        )
        return _row_to_dict(row) if row else None

    # ------------------------------------------------------------ admin ---

    async def list_all(
        self,
        *,
        q: str | None = None,
        role: str | None = None,
        disabled: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        clauses = []
        args: list[Any] = []

        if q:
            args.append(f"%{q}%")
            clauses.append(f"(email ILIKE ${len(args)} OR name ILIKE ${len(args)})")
        if role:
            args.append(role)
            clauses.append(f"role = ${len(args)}")
        if disabled is not None:
            # Static clause — a parameter placeholder here is unnecessary and
            # would shift the $n numbering used below.
            clauses.append("disabled_at IS NOT NULL" if disabled else "disabled_at IS NULL")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        total_row = await self._db.fetchrow(f"SELECT COUNT(*) AS c FROM users {where}", *args)
        total = int(total_row["c"]) if total_row else 0
        args.extend([limit, offset])
        rows = await self._db.fetch(
            f"SELECT {_PUBLIC_COLUMNS} FROM users {where} "
            f"ORDER BY created_at DESC LIMIT ${len(args) - 1} OFFSET ${len(args)}",
            *args,
        )
        return ([_row_to_dict(r) for r in rows], total)

    async def set_role(self, user_id: str, role: str) -> dict | None:
        row = await self._db.fetchrow(
            f"UPDATE users SET role = $2, updated_at = now() WHERE id = $1 RETURNING {_PUBLIC_COLUMNS}",
            user_id,
            role,
        )
        return _row_to_dict(row) if row else None

    async def set_disabled(self, user_id: str, disabled: bool) -> dict | None:
        row = await self._db.fetchrow(
            f"""
            UPDATE users SET
                disabled_at = CASE WHEN $2 THEN now() ELSE NULL END,
                updated_at = now()
            WHERE id = $1
            RETURNING {_PUBLIC_COLUMNS}
            """,
            user_id,
            disabled,
        )
        return _row_to_dict(row) if row else None

    async def set_password(self, user_id: str, password_hash: str) -> bool:
        result = await self._db.execute(
            "UPDATE users SET password_hash = $2, updated_at = now() WHERE id = $1",
            user_id,
            password_hash,
        )
        return result != "UPDATE 0"

    async def delete(self, user_id: str) -> bool:
        result = await self._db.execute("DELETE FROM users WHERE id = $1", user_id)
        return result != "DELETE 0"

    async def promote_by_emails(self, emails: list[str]) -> int:
        """ADMIN_EMAILS bootstrap: promote every matching account to admin."""
        if not emails:
            return 0
        rows = await self._db.fetch(
            "UPDATE users SET role = 'admin', updated_at = now() "
            "WHERE email = ANY($1::text[]) AND role <> 'admin' RETURNING id",
            emails,
        )
        return len(rows)
