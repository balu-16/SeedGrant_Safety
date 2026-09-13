"""Auth router — thin HTTP layer, delegates to AuthService."""

from fastapi import APIRouter, Depends, Request, status

from app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from app.auth.service import AuthService
from app.core.config import Settings
from app.core.deps import get_current_user, get_repos, get_settings_dep
from app.users.schemas import UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(request: Request, settings: Settings) -> AuthService:
    repos = get_repos(request)
    return AuthService(repos.users, repos.refresh_tokens, settings)


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: RegisterRequest, request: Request, settings: Settings = Depends(get_settings_dep)):
    svc = _service(request, settings)
    return await svc.register(name=body.name, email=str(body.email), phone=body.phone, password=body.password)


@router.post("/login", status_code=status.HTTP_200_OK, summary="Login with email + password")
async def login(body: LoginRequest, request: Request, settings: Settings = Depends(get_settings_dep)):
    svc = _service(request, settings)
    result = await svc.login(email=str(body.email), password=body.password)
    tokens = result["tokens"]
    return {
        "user": result["user"],
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
        "expires_in": tokens["expires_in"],
    }


@router.post("/refresh", response_model=RefreshResponse, summary="Rotate refresh token")
async def refresh(body: RefreshRequest, request: Request, settings: Settings = Depends(get_settings_dep)):
    svc = _service(request, settings)
    pair = await svc.refresh(refresh_token=body.refresh_token)
    return pair


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke one refresh token")
async def logout(body: LogoutRequest, request: Request, settings: Settings = Depends(get_settings_dep)):
    svc = _service(request, settings)
    await svc.logout(refresh_token=body.refresh_token)
    return None


@router.post("/logout-all", status_code=status.HTTP_200_OK, summary="Revoke all refresh tokens")
async def logout_all(request: Request, user: dict = Depends(get_current_user)):
    repos = get_repos(request)
    svc = AuthService(repos.users, repos.refresh_tokens, repos.settings)
    count = await svc.logout_all(user_id=str(user["id"]))
    return {"revoked": count}


# Keep TokenResponse exported for OpenAPI docs completeness
__all__ = ["router", "TokenResponse"]
