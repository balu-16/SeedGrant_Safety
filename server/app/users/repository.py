"""Users repository — parameterized asyncpg queries only."""

from typing import Any

DB = Any  # asyncpg.Pool | asyncpg.Connection (duck-typed for transactions)


def _row_to_dict(row: Any) -> dict:
    return dict(row)


class UsersRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

    async def create(self, *, email: str, name: str, phone: str, password_hash: str) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO users (email, name, phone, password_hash)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, name, phone, created_at, updated_at
            """,
            email,
            name,
            phone,
            password_hash,
        )
        return _row_to_dict(row)

    async def get_by_id(self, user_id: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT id, email, name, phone, created_at, updated_at FROM users WHERE id = $1",
            user_id,
        )
        return _row_to_dict(row) if row else None

    async def get_by_email(self, email: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT id, email, name, phone, password_hash, created_at, updated_at FROM users WHERE email = $1",
            email,
        )
        return _row_to_dict(row) if row else None

    async def get_auth_record(self, user_id: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT id, email, password_hash FROM users WHERE id = $1",
            user_id,
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
