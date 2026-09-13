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
        await websocket.close(code=4401)
        return
    user_id = str(user["id"])
    await manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "user_id": user_id})
        while True:
            # Keep-alive / client pings; server pushes events asynchronously.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.info("WS error user=%s: %s", user_id, e)
    finally:
        await manager.disconnect(user_id, websocket)
