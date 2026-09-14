"""Auth service — registration, login, refresh, logout."""

from datetime import UTC, datetime, timedelta

import asyncpg

from app.auth.repository import RefreshTokensRepository
from app.core.config import Settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token_value,
    verify_password,
)
from app.guardians.repository import GuardiansRepository
from app.users.repository import UsersRepository

log = get_logger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(
        self,
        users: UsersRepository,
        refresh_tokens: RefreshTokensRepository,
        settings: Settings,
        guardians: GuardiansRepository | None = None,
    ) -> None:
        self._users = users
        self._refresh = refresh_tokens
        self._settings = settings
        self._guardians = guardians

    async def register(self, *, name: str, email: str, phone: str, password: str) -> dict:
        email = _normalize_email(email)
        existing = await self._users.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered")
        try:
            user = await self._users.create(
                email=email,
                name=name.strip(),
                phone=phone.strip(),
                password_hash=hash_password(password),
            )
        except asyncpg.UniqueViolationError:
            # Two concurrent registrations raced past the pre-check above.
            raise ConflictError("Email already registered") from None
        # Pending invites sent to this email before the account existed can
        # now be linked so the guardian can actually accept them.
        if self._guardians is not None:
            try:
                linked = await self._guardians.link_pending_for_email(email, str(user["id"]))
                if linked:
                    log.info("Linked %d pending guardian invite(s) to new user %s", linked, user["id"])
            except Exception as e:
                log.warning("Pending guardian invite link failed for %s: %s", email, e)
        return user

    async def _issue_pair(self, user_id: str) -> dict:
        s = self._settings
        access, _ = create_access_token(
            user_id=user_id,
            secret=s.jwt_secret,
            algorithm=s.jwt_algorithm,
            expires_minutes=s.access_token_expire_minutes,
        )
        refresh, refresh_jti = create_refresh_token(
            user_id=user_id,
            secret=s.jwt_secret,
            algorithm=s.jwt_algorithm,
            expires_days=s.refresh_token_expire_days,
        )
        expires_at = datetime.now(UTC) + timedelta(days=s.refresh_token_expire_days)
        await self._refresh.create(user_id=user_id, jti_hash=hash_token_value(refresh_jti), expires_at=expires_at)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": s.access_token_expire_minutes * 60,
        }

    async def login(self, *, email: str, password: str) -> dict:
        record = await self._users.get_by_email(_normalize_email(email))
        if not record or not verify_password(password, record["password_hash"]):
            raise UnauthorizedError("Invalid email or password")
        if record.get("disabled_at") is not None:
            raise UnauthorizedError("Account is disabled")
        pair = await self._issue_pair(str(record["id"]))
        user = {
            k: record[k]
            for k in ("id", "email", "name", "phone", "role", "created_at", "updated_at")
            if k in record
        }
        return {"user": user, "tokens": pair}

    async def refresh(self, *, refresh_token: str) -> dict:
        s = self._settings
        payload = decode_token(
            token=refresh_token,
            secret=s.jwt_secret,
            algorithms=[s.jwt_algorithm],
            expected_type="refresh",
        )
        jti = str(payload.get("jti", ""))
        stored = await self._refresh.get_by_jti_hash(hash_token_value(jti))
        if not stored or stored.get("revoked_at") is not None:
            raise UnauthorizedError("Refresh token revoked")
        expires_at = stored["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise UnauthorizedError("Refresh token expired")
        # Rotate atomically: revoke returns False when a concurrent refresh
        # already consumed this token, so only the first use mints a new pair.
        revoked = await self._refresh.revoke_by_jti_hash(hash_token_value(jti))
        if not revoked:
            raise UnauthorizedError("Refresh token revoked")
        pair = await self._issue_pair(str(payload["sub"]))
        return pair

    async def logout(self, *, refresh_token: str) -> None:
        s = self._settings
        payload = decode_token(
            token=refresh_token,
            secret=s.jwt_secret,
            algorithms=[s.jwt_algorithm],
            expected_type="refresh",
        )
        await self._refresh.revoke_by_jti_hash(hash_token_value(str(payload.get("jti", ""))))

    async def logout_all(self, *, user_id: str) -> int:
        return await self._refresh.revoke_all_for_user(user_id)
