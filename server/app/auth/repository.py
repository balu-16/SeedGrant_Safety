"""Refresh-token repository — server-side revocation store."""

from datetime import datetime
from typing import Any

DB = Any


def _row_to_dict(row: Any) -> dict:
    return dict(row)


class RefreshTokensRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

    async def create(self, *, user_id: str, jti_hash: str, expires_at: datetime) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO refresh_tokens (user_id, jti_hash, expires_at)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, jti_hash, expires_at, revoked_at, created_at
            """,
            user_id,
            jti_hash,
            expires_at,
        )
        return _row_to_dict(row)

    async def get_by_jti_hash(self, jti_hash: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT id, user_id, jti_hash, expires_at, revoked_at, created_at FROM refresh_tokens WHERE jti_hash = $1",
            jti_hash,
        )
        return _row_to_dict(row) if row else None

    async def revoke_by_jti_hash(self, jti_hash: str) -> bool:
        result = await self._db.execute(
            "UPDATE refresh_tokens SET revoked_at = now() WHERE jti_hash = $1 AND revoked_at IS NULL",
            jti_hash,
        )
        return result != "UPDATE 0"

    async def revoke_all_for_user(self, user_id: str) -> int:
        result = await self._db.execute(
            "UPDATE refresh_tokens SET revoked_at = now() WHERE user_id = $1 AND revoked_at IS NULL",
            user_id,
        )
        # result looks like "UPDATE <n>"
        try:
            return int(result.split()[-1])
        except Exception:
            return 0
