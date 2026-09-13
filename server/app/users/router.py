"""Users router."""

from fastapi import APIRouter, Depends, Request

from app.core.deps import Repos, get_current_user, get_repos
from app.users.schemas import UserPublic, UserUpdate
from app.users.service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic, summary="Get my profile")
async def get_me(request: Request, user: dict = Depends(get_current_user)):
    repos: Repos = get_repos(request)
    svc = UsersService(repos.users)
    return await svc.get_me(str(user["id"]))


@router.patch("/me", response_model=UserPublic, summary="Update my profile")
async def update_me(body: UserUpdate, request: Request, user: dict = Depends(get_current_user)):
    repos: Repos = get_repos(request)
    svc = UsersService(repos.users)
    return await svc.update_me(str(user["id"]), name=body.name, phone=body.phone)
