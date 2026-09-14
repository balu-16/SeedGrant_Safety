"""Promote a user to admin: ``uv run python -m app.bootstrap_admin admin@example.com``.

Complements the ADMIN_EMAILS startup bootstrap for one-off promotions
(e.g. before the env var lands in the deployment).
"""

import asyncio
import sys

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.pool import create_pool
from app.users.repository import UsersRepository

log = get_logger(__name__)


async def promote(email: str) -> int:
    settings = get_settings()
    pool = await create_pool(settings)
    try:
        repo = UsersRepository(pool)
        promoted = await repo.promote_by_emails([email.strip().lower()])
        return promoted
    finally:
        await pool.close()


def main() -> None:
    setup_logging()
    if len(sys.argv) != 2:
        print("Usage: uv run python -m app.bootstrap_admin <email>")
        raise SystemExit(2)
    email = sys.argv[1]
    promoted = asyncio.run(promote(email))
    if promoted:
        log.info("Promoted %s to admin", email)
    else:
        log.warning("No user account found for %s — they must register first", email)


if __name__ == "__main__":
    main()
