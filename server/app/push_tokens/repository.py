"""Push-token repository."""

from datetime import UTC, datetime
from typing import Any

DB = Any


def _row_to_dict(row: Any) -> dict:
    return dict(row)


class PushTokensRepository:
    def __init__(self, db: DB) -> None:
        self._db = db

    async def upsert(self, *, user_id: str, token_hash: str, platform: str, token: str | None = None) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO push_tokens (user_id, token_hash, token, platform, last_seen_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (token_hash) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                token = COALESCE(EXCLUDED.token, push_tokens.token),
                platform = EXCLUDED.platform,
                last_seen_at = EXCLUDED.last_seen_at
            RETURNING id, user_id, platform, created_at, last_seen_at
            """,
            user_id,
            token_hash,
            token,
            platform,
            datetime.now(UTC),
        )
        return _row_to_dict(row)

    async def list_for_user(self, user_id: str) -> list[dict]:
        rows = await self._db.fetch(
            "SELECT id, user_id, platform, created_at, last_seen_at "
            "FROM push_tokens WHERE user_id = $1 ORDER BY created_at",
            user_id,
        )
        return [_row_to_dict(r) for r in rows]

    async def delete(self, user_id: str, token_hash: str) -> bool:
        result = await self._db.execute(
            "DELETE FROM push_tokens WHERE user_id = $1 AND token_hash = $2",
            user_id,
            token_hash,
        )
        return result != "DELETE 0"

    async def tokens_for_users(self, user_ids: list[str]) -> list[dict]:
        """Raw sendable tokens for delivery. Never expose these via the API."""
        if not user_ids:
            return []
        rows = await self._db.fetch(
            "SELECT user_id, token, platform FROM push_tokens WHERE user_id = ANY($1::uuid[]) AND token IS NOT NULL",
            [str(u) for u in user_ids],
        )
        return [_row_to_dict(r) for r in rows]

    async def delete_by_token_hash(self, token_hash: str) -> bool:
        """Prune a dead token (e.g. FCM UNREGISTERED), regardless of owner."""
        result = await self._db.execute("DELETE FROM push_tokens WHERE token_hash = $1", token_hash)
        return result != "DELETE 0"

    async def get_by_id(self, token_id: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT id, user_id, platform, created_at, last_seen_at FROM push_tokens WHERE id = $1",
            token_id,
        )
        return _row_to_dict(row) if row else None

    async def delete_by_id(self, token_id: str) -> bool:
        result = await self._db.execute("DELETE FROM push_tokens WHERE id = $1", token_id)
        return result != "DELETE 0"

    async def count_all(self) -> int:
        row = await self._db.fetchrow("SELECT COUNT(*) AS c FROM push_tokens")
        return int(row["c"]) if row else 0
