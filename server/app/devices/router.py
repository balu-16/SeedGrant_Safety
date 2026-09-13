"""Devices router."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.core.deps import Repos, get_current_user, get_repos
from app.devices.schemas import (
    DeviceCreate,
    DevicePairRequest,
    DevicePublic,
    DeviceStatus,
    DeviceUpdate,
)
from app.devices.service import DevicesService

router = APIRouter(prefix="/devices", tags=["devices"])


def _svc(request: Request) -> DevicesService:
    repos: Repos = get_repos(request)
    return DevicesService(repos.devices)


@router.post("", response_model=DevicePublic, status_code=status.HTTP_201_CREATED, summary="Register a tag")
async def create_device(body: DeviceCreate, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.register(str(user["id"]), name=body.name, device_secret=body.device_secret)


@router.get("", response_model=list[DevicePublic], summary="List my tags")
async def list_devices(request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.list_mine(str(user["id"]))


@router.get("/{device_id}", response_model=DevicePublic, summary="Get one tag")
async def get_device(device_id: UUID, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.get_mine(str(user["id"]), str(device_id))


@router.patch("/{device_id}", response_model=DevicePublic, summary="Update tag")
async def update_device(device_id: UUID, body: DeviceUpdate, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.update_mine(
        str(user["id"]),
        str(device_id),
        name=body.name,
        battery_pct=body.battery_pct,
        connection_state=body.connection_state,
    )


@router.post("/{device_id}/pair", response_model=DevicePublic, summary="Pair / mark online")
async def pair_device(
    device_id: UUID,
    body: DevicePairRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    svc = _svc(request)
    return await svc.pair(str(user["id"]), str(device_id), device_secret=body.device_secret)


@router.post("/{device_id}/unpair", status_code=status.HTTP_204_NO_CONTENT, summary="Unpair / remove tag")
async def unpair_device(device_id: UUID, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    await svc.unpair(str(user["id"]), str(device_id))
    return None


@router.get("/{device_id}/status", response_model=DeviceStatus, summary="Tag status")
async def device_status(device_id: UUID, request: Request, user: dict = Depends(get_current_user)):
    svc = _svc(request)
    return await svc.status(str(user["id"]), str(device_id))
