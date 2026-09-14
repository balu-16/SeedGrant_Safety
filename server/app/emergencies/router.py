"""Emergencies router."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status

from app.core.deps import Repos, get_current_user, get_repos
from app.core.ratelimit import rate_limit
from app.emergencies.schemas import (
    EmergencyCreate,
    EmergencyListResponse,
    EmergencyPublic,
    EmergencyStatus,
    EmergencyStatusUpdate,
)
from app.emergencies.service import EmergenciesService

router = APIRouter(prefix="/emergencies", tags=["emergencies"])


def _svc(request: Request, background: BackgroundTasks | None = None) -> EmergenciesService:
    repos: Repos = get_repos(request)
    notifications = request.app.state.notifications
    return EmergenciesService(
        repos.emergencies,
        repos.guardians,
        repos.devices,
        notifications,
        emit=request.app.state.emit,
        emit_admins=getattr(request.app.state, "emit_admins", None),
        pool=repos.pool,
        background=background,
    )


@router.post(
    "",
    response_model=EmergencyPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create SOS incident",
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60, scope="emergencies:create"))],
)
async def create_emergency(
    body: EmergencyCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    svc = _svc(request, background_tasks)
    return await svc.create(
        str(user["id"]),
        trigger_type=body.trigger_type,
        device_id=str(body.device_id) if body.device_id else None,
        latitude=body.latitude,
        longitude=body.longitude,
        note=body.note,
    )


@router.get("", response_model=EmergencyListResponse, summary="List incidents")
async def list_emergencies(
    request: Request,
    user: dict = Depends(get_current_user),
    user_id: UUID | None = Query(default=None, description="Protected user; defaults to me"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: EmergencyStatus | None = Query(default=None),
):
    svc = _svc(request)
    protected = str(user_id) if user_id else str(user["id"])
    items, total = await svc.list_for(
        str(user["id"]),
        protected,
        limit=limit,
        offset=offset,
        status=status.value if status else None,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{emergency_id}", response_model=EmergencyPublic, summary="Get incident")
async def get_emergency(emergency_id: UUID, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.get(str(user["id"]), str(emergency_id))


@router.patch("/{emergency_id}/status", response_model=EmergencyPublic, summary="Update incident state")
async def update_status(
    emergency_id: UUID,
    body: EmergencyStatusUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    svc = _svc(request, background_tasks)
    return await svc.update_status(str(user["id"]), str(emergency_id), body.status.value)


@router.post("/{emergency_id}/resolve", response_model=EmergencyPublic, summary="Resolve incident")
async def resolve(
    emergency_id: UUID, request: Request, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)
):
    svc = _svc(request, background_tasks)
    return await svc.update_status(str(user["id"]), str(emergency_id), EmergencyStatus.RESOLVED.value)


@router.post("/{emergency_id}/cancel", response_model=EmergencyPublic, summary="Cancel incident")
async def cancel(
    emergency_id: UUID, request: Request, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)
):
    svc = _svc(request, background_tasks)
    return await svc.update_status(str(user["id"]), str(emergency_id), EmergencyStatus.CANCELLED.value)
