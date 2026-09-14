"""Authenticated WebSocket endpoint for real-time safety events."""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.deps import authenticate_ws_token
from app.core.logging import get_logger
from app.websocket.manager import manager

log = get_logger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str = Query(...)):
    repos = websocket.app.state.repos
    try:
        user = await authenticate_ws_token(token, repos)
    except Exception:
        # Accept before closing so the client actually receives the 4401
        # close code instead of a bare HTTP 403 handshake rejection.
        try:
            await websocket.accept()
            await websocket.close(code=4401)
        except Exception:
            pass
        return
    user_id = str(user["id"])
    is_admin = str(user.get("role", "user")) == "admin"
    await manager.connect(user_id, websocket, is_admin=is_admin)
    try:
        await websocket.send_json({"type": "connected", "user_id": user_id, "is_admin": is_admin})
        while True:
            # Keep-alive / client pings; server pushes events asynchronously.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.info("WS error user=%s: %s", user_id, e)
    finally:
        await manager.disconnect(user_id, websocket)
