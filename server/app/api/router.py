"""Aggregate all /api routers."""

from fastapi import APIRouter

from app.admin.router import router as admin_router
from app.api.health import router as health_router
from app.auth.router import router as auth_router
from app.devices.router import router as devices_router
from app.emergencies.router import router as emergencies_router
from app.guardians.router import router as guardians_router
from app.locations.router import router as locations_router
from app.push_tokens.router import router as push_tokens_router
from app.users.router import router as users_router
from app.websocket.router import router as ws_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(devices_router)
api_router.include_router(guardians_router)
api_router.include_router(locations_router)
api_router.include_router(emergencies_router)
api_router.include_router(push_tokens_router)
api_router.include_router(admin_router)
api_router.include_router(ws_router)
