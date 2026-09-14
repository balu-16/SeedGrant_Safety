"""Application factory with lifespan-managed asyncpg pool."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.repository import AdminAuditRepository, AdminRepository
from app.api.router import api_router
from app.auth.repository import RefreshTokensRepository
from app.core.config import Settings, get_settings
from app.core.deps import Repos
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.pool import create_pool
from app.devices.repository import DevicesRepository
from app.emergencies.repository import EmergenciesRepository
from app.guardians.repository import GuardiansRepository
from app.locations.repository import LocationsRepository
from app.notifications.service import NotificationService, build_notifications
from app.push_tokens.repository import PushTokensRepository
from app.users.repository import UsersRepository
from app.websocket.manager import emit_to_admins, emit_to_users

log = get_logger(__name__)


def build_repos(settings: Settings, pool: object | None) -> Repos:
    return Repos(
        settings=settings,
        pool=pool,
        users=UsersRepository(pool),  # type: ignore[arg-type]
        refresh_tokens=RefreshTokensRepository(pool),  # type: ignore[arg-type]
        devices=DevicesRepository(pool),  # type: ignore[arg-type]
        guardians=GuardiansRepository(pool),  # type: ignore[arg-type]
        locations=LocationsRepository(pool),  # type: ignore[arg-type]
        emergencies=EmergenciesRepository(pool),  # type: ignore[arg-type]
        push_tokens=PushTokensRepository(pool),  # type: ignore[arg-type]
        audit=AdminAuditRepository(pool),  # type: ignore[arg-type]
        admin=AdminRepository(pool),  # type: ignore[arg-type]
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    # Tests inject app.state.pool / app.state.repos beforehand; don't override.
    if getattr(app.state, "pool", None) is None and not settings.testing and settings.database_url:
        try:
            app.state.pool = await create_pool(settings)
            log.info("Database pool ready")
        except Exception as e:
            log.warning("Database pool unavailable at startup: %s", e)
            app.state.pool = None
    if getattr(app.state, "repos", None) is None:
        app.state.repos = build_repos(settings, getattr(app.state, "pool", None))
    if getattr(app.state, "notifications", None) is None:
        app.state.notifications = build_notifications(settings)
    notifications = app.state.notifications
    if isinstance(notifications, NotificationService) and getattr(app.state, "repos", None) is not None:
        notifications.bind(push_tokens=app.state.repos.push_tokens, guardians=app.state.repos.guardians)
    if getattr(app.state, "emit", None) is None:
        app.state.emit = emit_to_users
    if getattr(app.state, "emit_admins", None) is None:
        app.state.emit_admins = emit_to_admins
    await _bootstrap_admins(app)
    yield
    pool = getattr(app.state, "pool", None)
    if pool is not None:
        try:
            await pool.close()
        except Exception:
            pass


async def _bootstrap_admins(app: FastAPI) -> None:
    """Promote ADMIN_EMAILS accounts to admin at startup (idempotent)."""
    settings: Settings = app.state.settings
    emails = settings.admin_emails
    if not emails or settings.testing:
        return
    repos = getattr(app.state, "repos", None)
    if repos is None or getattr(repos, "users", None) is None:
        return
    try:
        promoted = await repos.users.promote_by_emails(emails)
        if promoted:
            log.info("Promoted %d ADMIN_EMAILS account(s) to admin", promoted)
    except Exception as e:
        # The admin router fails closed regardless; never block startup here.
        log.warning("ADMIN_EMAILS bootstrap failed: %s", e)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    if not settings.testing and settings.jwt_secret.startswith("change-me"):
        if settings.is_production:
            raise RuntimeError(
                "Refusing to start: JWT_SECRET is still the insecure default. "
                "Set a strong secret (min 32 chars) via the environment before deploying."
            )
        log.warning("JWT_SECRET is still the insecure default — set a strong secret in .env")
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Smart Safety Tag V0 backend — personal safety API (REST + WebSocket events).",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.pool = None
    app.state.repos = None
    app.state.notifications = build_notifications(settings)
    app.state.emit = emit_to_users

    wildcard = "*" in settings.cors_origins
    if wildcard and not settings.testing:
        log.warning("CORS_ORIGINS is '*' — set explicit origins before exposing this API publicly")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # Bearer-header auth needs no credentialed CORS; credentials stay off
        # for wildcard origins so responses can never mirror arbitrary origins.
        allow_credentials=not wildcard,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
