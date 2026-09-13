"""Locations router."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.deps import Repos, get_current_user, get_repos
from app.locations.schemas import LocationCreate, LocationHistoryResponse, LocationPublic
from app.locations.service import LocationsService

router = APIRouter(prefix="/locations", tags=["locations"])


def _svc(request: Request) -> LocationsService:
    repos: Repos = get_repos(request)
    return LocationsService(repos.locations, repos.guardians, repos.devices)


@router.post("", response_model=LocationPublic, status_code=status.HTTP_201_CREATED, summary="Submit GPS fix")
async def submit(body: LocationCreate, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.submit(
        str(user["id"]),
        latitude=body.latitude,
        longitude=body.longitude,
        accuracy_m=body.accuracy_m,
        source=body.source.value,
        device_id=str(body.device_id) if body.device_id else None,
        recorded_at=body.recorded_at,
    )


@router.get("/latest", response_model=LocationPublic | None, summary="Latest authorized location")
async def latest(
    request: Request,
    user: dict = Depends(get_current_user),
    user_id: UUID | None = Query(default=None, description="Protected user; defaults to me"),
):
    svc = _svc(request)
    protected = str(user_id) if user_id else str(user["id"])
    return await svc.latest(str(user["id"]), protected)


@router.get("/history", response_model=LocationHistoryResponse, summary="Paginated location history")
async def history(
    request: Request,
    user: dict = Depends(get_current_user),
    user_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    svc = _svc(request)
    protected = str(user_id) if user_id else str(user["id"])
    items, total = await svc.history(str(user["id"]), protected, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
