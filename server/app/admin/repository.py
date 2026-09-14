"""Admin repositories: audit trail + cross-domain dashboard queries."""

import json
from datetime import UTC, datetime
from typing import Any

DB = Any


def _row_to_dict(row: Any) -> dict:
    return dict(row)


class AdminAuditRepository:
    """Append-only audit log for admin-portal mutations."""

    def __init__(self, db: DB) -> None:
        self._db = db

    async def create(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        target_type: str,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO admin_audit_log (actor_user_id, action, target_type, target_id, details)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            RETURNING id, actor_user_id, action, target_type, target_id, details, created_at
            """,
            actor_user_id,
            action,
            target_type,
            target_id,
            json.dumps(details) if details else None,
        )
        return _row_to_dict(row)

    async def list_all(
        self,
        *,
        actor_id: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        clauses = []
        args: list[Any] = []
        if actor_id:
            args.append(actor_id)
            clauses.append(f"actor_user_id = ${len(args)}")
        if action:
            args.append(action)
            clauses.append(f"action = ${len(args)}")
        if target_type:
            args.append(target_type)
            clauses.append(f"target_type = ${len(args)}")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        total_row = await self._db.fetchrow(
            f"""
            SELECT COUNT(*) AS c FROM admin_audit_log a {where}
            """,
            *args,
        )
        total = int(total_row["c"]) if total_row else 0
        args.extend([limit, offset])
        rows = await self._db.fetch(
            f"""
            SELECT a.id, a.actor_user_id, a.action, a.target_type, a.target_id, a.details,
                   a.created_at, u.email AS actor_email, u.name AS actor_name
            FROM admin_audit_log a LEFT JOIN users u ON u.id = a.actor_user_id
            {where}
            ORDER BY a.created_at DESC LIMIT ${len(args) - 1} OFFSET ${len(args)}
            """,
            *args,
        )
        return ([_row_to_dict(r) for r in rows], total)


class AdminRepository:
    """Read-only cross-domain aggregates for the dashboard."""

    def __init__(self, db: DB) -> None:
        self._db = db

    async def stats(self) -> dict:
        row = await self._db.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM users) AS users_total,
                (SELECT COUNT(*) FROM users WHERE created_at > now() - interval '7 days') AS users_new_7d,
                (SELECT COUNT(*) FROM users WHERE created_at > now() - interval '30 days') AS users_new_30d,
                (SELECT COUNT(*) FROM devices) AS devices_total,
                (SELECT COUNT(*) FROM devices WHERE connection_state = 'online') AS devices_online,
                (SELECT COUNT(*) FROM guardians WHERE status = 'accepted') AS guardians_accepted,
                (SELECT COUNT(*) FROM guardians WHERE status = 'pending') AS guardians_pending,
                (SELECT COUNT(*) FROM emergencies WHERE status IN ('active', 'acknowledged')) AS emergencies_open,
                (SELECT COUNT(*) FROM emergencies WHERE created_at > now() - interval '30 days')
                    AS emergencies_30d,
                (SELECT COUNT(*) FROM push_tokens) AS push_tokens_total
            """
        )
        data = _row_to_dict(row) if row else {}
        return {k: int(v) for k, v in data.items()}

    async def series(self, *, days: int = 30) -> list[dict]:
        rows = await self._db.fetch(
            """
            SELECT d::date AS day,
                   (SELECT COUNT(*) FROM users u WHERE u.created_at::date = d::date) AS signups,
                   (SELECT COUNT(*) FROM emergencies e WHERE e.created_at::date = d::date) AS emergencies
            FROM generate_series(
                (now() - make_interval(days => $1 - 1))::date,
                now()::date,
                interval '1 day'
            ) AS d
            ORDER BY day
            """,
            days,
        )
        return [
            {"day": r["day"].isoformat(), "signups": int(r["signups"]), "emergencies": int(r["emergencies"])}
            for r in rows
        ]

    async def all_user_ids(self) -> list[str]:
        rows = await self._db.fetch("SELECT id FROM users")
        return [str(r["id"]) for r in rows]


def utcnow() -> datetime:
    return datetime.now(UTC)
