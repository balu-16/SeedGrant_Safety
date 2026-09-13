"""FastAPI dependencies: settings, repos, authentication."""

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.repository import RefreshTokensRepository
from app.core.config import Settings
from app.core.exceptions import DatabaseError, UnauthorizedError
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.devices.repository import DevicesRepository
from app.emergencies.repository import EmergenciesRepository
from app.guardians.repository import GuardiansRepository
from app.locations.repository import LocationsRepository
from app.push_tokens.repository import PushTokensRepository
from app.users.repository import UsersRepository

_bearer = HTTPBearer(auto_error=False)


@dataclass
class Repos:
    settings: Settings
    pool: Any | None
    users: UsersRepository
    refresh_tokens: RefreshTokensRepository
    devices: DevicesRepository
    guardians: GuardiansRepository
    locations: LocationsRepository
    emergencies: EmergenciesRepository
    push_tokens: PushTokensRepository


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_repos(request: Request) -> Repos:
    repos = request.app.state.repos
    if isinstance(repos, Repos):
        if repos.pool is None and not repos.settings.testing:
            raise DatabaseError("Database not configured")
        return repos
    # Fallback: build from pool (should not happen; app factory always sets Repos)
    raise RuntimeError("Repositories not initialized")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing bearer token")
    repos = get_repos(request)
    payload = decode_token(
        token=credentials.credentials,
        secret=repos.settings.jwt_secret,
        algorithms=[repos.settings.jwt_algorithm],
        expected_type=ACCESS_TOKEN_TYPE,
    )
    user = await repos.users.get_by_id(str(payload["sub"]))
    if not user:
        raise UnauthorizedError("User no longer exists")
    return user


async def authenticate_ws_token(token: str, repos: Repos) -> dict:
    payload = decode_token(
        token=token,
        secret=repos.settings.jwt_secret,
        algorithms=[repos.settings.jwt_algorithm],
        expected_type=ACCESS_TOKEN_TYPE,
    )
    user = await repos.users.get_by_id(str(payload["sub"]))
    if not user:
        raise UnauthorizedError("User no longer exists")
    return user
