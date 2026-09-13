"""Guardians router."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.core.deps import Repos, get_current_user, get_repos
from app.guardians.schemas import GuardianInviteRequest, GuardianPublic, GuardianStatusUpdate
from app.guardians.service import GuardiansService

router = APIRouter(prefix="/guardians", tags=["guardians"])


def _svc(request: Request) -> GuardiansService:
    repos: Repos = get_repos(request)
    return GuardiansService(repos.guardians, repos.users)


@router.post(
    "/invite",
    response_model=GuardianPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a guardian",
)
async def invite(body: GuardianInviteRequest, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.invite(
        str(user["id"]),
        guardian_email=str(body.guardian_email),
        guardian_name=body.guardian_name,
        relation=body.relation,
        is_primary=body.is_primary,
    )


@router.get("", response_model=list[GuardianPublic], summary="List my guardians")
async def list_mine(request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.list_mine(str(user["id"]))


@router.get("/protecting", response_model=list[GuardianPublic], summary="Users I protect")
async def list_protecting(request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.list_protecting_me(str(user["id"]))


@router.patch("/{guardian_id}/status", response_model=GuardianPublic, summary="Accept/reject/remove")
async def update_status(
    guardian_id: UUID,
    body: GuardianStatusUpdate,
    request: Request,
    user: dict = Depends(get_current_user),
):
    svc = _svc(request)
    return await svc.update_status(str(user["id"]), str(guardian_id), body.status.value)


@router.delete("/{guardian_id}", response_model=GuardianPublic, summary="Remove a guardian")
async def remove(guardian_id: UUID, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.remove(str(user["id"]), str(guardian_id))
