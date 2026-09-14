"""Admin portal router — every route requires the admin role."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.admin.schemas import AdminUserUpdate, DeviceAdminUpdate, GuardianForceStatus, PushSendRequest
from app.admin.service import AdminService
from app.core.deps import Repos, get_current_admin, get_repos, get_settings_dep
from app.core.ratelimit import rate_limit
from app.emergencies.service import EmergenciesService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(rate_limit(max_requests=120, window_seconds=60, scope="admin"))],
)


def _svc(request: Request) -> AdminService:
    repos: Repos = get_repos(request)
    return AdminService(
        users=repos.users,
        refresh_tokens=repos.refresh_tokens,
        devices=repos.devices,
        guardians=repos.guardians,
        locations=repos.locations,
        emergencies=repos.emergencies,
        push_tokens=repos.push_tokens,
        audit=repos.audit,
        admin=repos.admin,
        notifications=request.app.state.notifications,
        emergencies_service=_emergencies_svc(repos, request),
    )


def _emergencies_svc(repos: Repos, request: Request) -> EmergenciesService:
    return EmergenciesService(
        repos.emergencies,
        repos.guardians,
        repos.devices,
        request.app.state.notifications,
        emit=getattr(request.app.state, "emit", None),
        emit_admins=getattr(request.app.state, "emit_admins", None),
        pool=repos.pool,
    )


@router.get("/stats", summary="Dashboard KPIs + 30-day series")
async def stats(request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).stats()


@router.get("/health", summary="Platform health (non-secret)")
async def health(request: Request, settings=Depends(get_settings_dep), admin: dict = Depends(get_current_admin)):
    repos: Repos = get_repos(request)
    return await _svc(request).health(settings=settings, pool=repos.pool)


# ---------------------------------------------------------------- users ---


@router.get("/users", summary="List / search users")
async def list_users(
    request: Request,
    admin: dict = Depends(get_current_admin),
    q: str | None = Query(default=None, max_length=120),
    role: str | None = Query(default=None, pattern="^(user|admin)$"),
    disabled: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = await _svc(request).list_users(
        q=q, role=role, disabled=disabled, limit=limit, offset=offset
    )
    return {"items": items, "total": total}


@router.get("/users/{user_id}", summary="Full user detail")
async def user_detail(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).user_detail(str(user_id))


@router.patch("/users/{user_id}", summary="Update user profile")
async def update_user(
    user_id: UUID, body: AdminUserUpdate, request: Request, admin: dict = Depends(get_current_admin)
):
    return await _svc(request).update_user(str(admin["id"]), str(user_id), name=body.name, phone=body.phone)


@router.post("/users/{user_id}/disable", summary="Suspend account (kills sessions)")
async def disable_user(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).set_disabled(str(admin["id"]), str(user_id), disabled=True)


@router.post("/users/{user_id}/enable", summary="Reinstate account")
async def enable_user(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).set_disabled(str(admin["id"]), str(user_id), disabled=False)


@router.post("/users/{user_id}/force-logout", summary="Revoke all refresh tokens")
async def force_logout(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    revoked = await _svc(request).force_logout(str(admin["id"]), str(user_id))
    return {"revoked": revoked}


@router.post("/users/{user_id}/reset-password", summary="Set a one-time temp password")
async def reset_password(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    temp = await _svc(request).reset_password(str(admin["id"]), str(user_id))
    return {"temp_password": temp}


@router.post("/users/{user_id}/promote", summary="Grant admin role")
async def promote_user(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).set_role(str(admin["id"]), str(user_id), "admin")


@router.post("/users/{user_id}/demote", summary="Revoke admin role")
async def demote_user(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).set_role(str(admin["id"]), str(user_id), "user")


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user + all data")
async def delete_user(user_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    await _svc(request).delete_user(str(admin["id"]), str(user_id))
    return None


# -------------------------------------------------------------- devices ---


@router.get("/devices", summary="List all tags")
async def list_devices(
    request: Request,
    admin: dict = Depends(get_current_admin),
    connection_state: str | None = Query(default=None, pattern="^(online|offline|unknown)$"),
    low_battery: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = await _svc(request).list_devices(
        connection_state=connection_state, low_battery=low_battery, limit=limit, offset=offset
    )
    return {"items": items, "total": total}


@router.patch("/devices/{device_id}", summary="Rename a tag")
async def update_device(
    device_id: UUID, body: DeviceAdminUpdate, request: Request, admin: dict = Depends(get_current_admin)
):
    return await _svc(request).update_device(str(admin["id"]), str(device_id), name=body.name)


@router.post("/devices/{device_id}/force-offline", summary="Mark tag offline")
async def force_offline(device_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).force_offline(str(admin["id"]), str(device_id))


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a tag")
async def delete_device(device_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    await _svc(request).delete_device(str(admin["id"]), str(device_id))
    return None


# ------------------------------------------------------------- guardians ---


@router.get("/guardians", summary="List all guardian links")
async def list_guardians(
    request: Request,
    admin: dict = Depends(get_current_admin),
    status_filter: str | None = Query(
        default=None, alias="status", pattern="^(pending|accepted|rejected|removed)$"
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = await _svc(request).list_guardians(status=status_filter, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.patch("/guardians/{guardian_id}/status", summary="Force consent status")
async def force_guardian_status(
    guardian_id: UUID, body: GuardianForceStatus, request: Request, admin: dict = Depends(get_current_admin)
):
    return await _svc(request).force_guardian_status(str(admin["id"]), str(guardian_id), body.status)


@router.delete("/guardians/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete guardian link")
async def delete_guardian(guardian_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    await _svc(request).delete_guardian(str(admin["id"]), str(guardian_id))
    return None


# ----------------------------------------------------------- emergencies ---


@router.get("/emergencies", summary="List all incidents")
async def list_emergencies(
    request: Request,
    admin: dict = Depends(get_current_admin),
    status_filter: str | None = Query(
        default=None, alias="status", pattern="^(active|acknowledged|resolved|cancelled)$"
    ),
    trigger_type: str | None = Query(
        default=None,
        pattern="^(TAG_BUTTON|TAG_VOICE|APP_BUTTON|APP_VOICE|FALL_DETECTION)$",
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = await _svc(request).list_emergencies(
        status=status_filter, trigger_type=trigger_type, limit=limit, offset=offset
    )
    return {"items": items, "total": total}


@router.get("/emergencies/{emergency_id}", summary="Incident detail + event timeline")
async def emergency_detail(emergency_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).emergency_detail(str(emergency_id))


@router.post("/emergencies/{emergency_id}/ack", summary="Acknowledge on behalf")
async def ack_emergency(emergency_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).emergency_transition(str(admin["id"]), str(emergency_id), "ack")


@router.post("/emergencies/{emergency_id}/resolve", summary="Resolve on behalf")
async def resolve_emergency(emergency_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).emergency_transition(str(admin["id"]), str(emergency_id), "resolve")


@router.post("/emergencies/{emergency_id}/cancel", summary="Cancel on behalf")
async def cancel_emergency(emergency_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).emergency_transition(str(admin["id"]), str(emergency_id), "cancel")


# ------------------------------------------------------------- locations ---


@router.get("/locations/latest", summary="Latest location for a user")
async def latest_location(
    request: Request,
    admin: dict = Depends(get_current_admin),
    user_id: UUID = Query(...),
):
    return await _svc(request).latest_location(str(user_id))


@router.get("/locations/history", summary="Location history for a user")
async def location_history(
    request: Request,
    admin: dict = Depends(get_current_admin),
    user_id: UUID = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    items, total = await _svc(request).location_history(str(user_id), limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.delete("/locations", summary="Purge a user's location history")
async def purge_locations(
    request: Request,
    admin: dict = Depends(get_current_admin),
    user_id: UUID = Query(...),
):
    deleted = await _svc(request).purge_locations(str(admin["id"]), str(user_id))
    return {"deleted": deleted}


# ------------------------------------------------------------------ push ---


@router.get("/push-tokens", summary="List a user's push tokens")
async def list_push_tokens(
    request: Request,
    admin: dict = Depends(get_current_admin),
    user_id: UUID = Query(...),
):
    return await _svc(request).list_push_tokens(str(user_id))


@router.delete("/push-tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a push token")
async def delete_push_token(token_id: UUID, request: Request, admin: dict = Depends(get_current_admin)):
    await _svc(request).delete_push_token(str(admin["id"]), str(token_id))
    return None


@router.post("/push/send", summary="Test push / broadcast")
async def send_push(body: PushSendRequest, request: Request, admin: dict = Depends(get_current_admin)):
    return await _svc(request).send_push(
        str(admin["id"]),
        title=body.title,
        body=body.body,
        user_ids=[str(u) for u in body.user_ids] if body.user_ids else None,
        all_users=body.all_users,
    )


# ----------------------------------------------------------------- audit ---


@router.get("/audit", summary="Admin audit log")
async def list_audit(
    request: Request,
    admin: dict = Depends(get_current_admin),
    actor_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None, max_length=80),
    target_type: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = await _svc(request).list_audit(
        actor_id=str(actor_id) if actor_id else None,
        action=action,
        target_type=target_type,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total}
