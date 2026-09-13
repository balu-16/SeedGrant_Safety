"""Password hashing (Argon2) and JWT helpers (PyJWT)."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bool(_password_hash.verify(password, password_hash))
    except Exception:
        return False


def hash_token_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(*, user_id: str, secret: str, algorithm: str, expires_minutes: int) -> tuple[str, str]:
    now = _now()
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "type": ACCESS_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "jti": jti,
    }
    return jwt.encode(payload, secret, algorithm=algorithm), jti


def create_refresh_token(*, user_id: str, secret: str, algorithm: str, expires_days: int) -> tuple[str, str]:
    now = _now()
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "type": REFRESH_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=expires_days)).timestamp()),
        "jti": jti,
    }
    return jwt.encode(payload, secret, algorithm=algorithm), jti


def decode_token(*, token: str, secret: str, algorithms: list[str], expected_type: str) -> dict:
    from app.core.exceptions import UnauthorizedError

    try:
        payload = jwt.decode(token, secret, algorithms=algorithms, options={"require": ["exp", "sub", "type"]})
    except jwt.ExpiredSignatureError as e:
        raise UnauthorizedError("Token expired") from e
    except jwt.InvalidTokenError as e:
        raise UnauthorizedError("Invalid token") from e
    if payload.get("type") != expected_type:
        raise UnauthorizedError(f"Wrong token type: expected {expected_type}")
    return payload
