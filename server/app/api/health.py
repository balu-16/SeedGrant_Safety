"""Health endpoints — liveness vs readiness split."""

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness: server is running")
async def health(request: Request):
    settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.env,
        "time": datetime.now(UTC).isoformat(),
    }


@router.get("/ready", summary="Readiness: database reachable")
async def ready(request: Request):
    settings = request.app.state.settings
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        # Pytest fake-repo mode (testing=True) has no live pool but is ready.
        if getattr(settings, "testing", False):
            return {"status": "ready", "database": "fake"}
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "database not configured"})
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "database unreachable"})
    return {"status": "ready", "database": "up"}
