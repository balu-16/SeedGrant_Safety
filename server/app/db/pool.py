"""Reusable asyncpg connection pool with Supabase SSL support."""

import asyncpg

from app.core.config import Settings
from app.core.logging import get_logger

log = get_logger(__name__)


def _ssl_arg(settings: Settings) -> str | None:
    # Supabase Postgres requires SSL. `sslmode=require` style is configured
    # via DB_SSLMODE; asyncpg accepts 'require'/'prefer'/etc. as ssl arg shorthand.
    mode = (settings.db_sslmode or "").strip().lower()
    if not settings.database_url:
        return None
    if mode in ("disable", "disabled", "off", ""):
        return None
    if mode in ("require", "prefer", "allow", "verify-ca", "verify-full"):
        return mode
    return "require"


async def create_pool(settings: Settings) -> asyncpg.Pool:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    ssl = _ssl_arg(settings)
    kwargs: dict = {
        "dsn": settings.database_url,
        "min_size": settings.db_pool_min,
        "max_size": settings.db_pool_max,
        "command_timeout": 30,
    }
    if ssl:
        kwargs["ssl"] = ssl
    log.info("Opening asyncpg pool (ssl=%s)", ssl)
    pool = await asyncpg.create_pool(**kwargs)
    if pool is None:
        raise RuntimeError("Failed to create asyncpg pool")
    return pool


async def check_pool(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
