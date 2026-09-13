"""Lightweight idempotent SQL migration runner (asyncpg, no ORM)."""

import asyncio
import pathlib

import asyncpg

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.pool import create_pool

log = get_logger(__name__)

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "migrations"


async def ensure_migrations_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


async def applied_versions(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT version FROM schema_migrations")
    return {r["version"] for r in rows}


async def run_migrations() -> list[str]:
    settings = get_settings()
    pool = await create_pool(settings)
    applied: list[str] = []
    try:
        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        if not files:
            log.warning("No migration files found in %s", MIGRATIONS_DIR)
            return applied
        async with pool.acquire() as conn:
            await ensure_migrations_table(conn)
            done = await applied_versions(conn)
            for path in files:
                version = path.stem
                if version in done:
                    log.info("Skipping already-applied migration %s", version)
                    continue
                sql = path.read_text(encoding="utf-8")
                log.info("Applying migration %s", version)
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO schema_migrations(version) VALUES($1)",
                        version,
                    )
                applied.append(version)
        log.info("Migrations complete: %s", applied)
        return applied
    finally:
        await pool.close()


def main() -> None:
    setup_logging()
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
