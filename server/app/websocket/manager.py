"""Authenticated WebSocket connection manager."""

import asyncio

from fastapi import WebSocket

from app.core.logging import get_logger

log = get_logger(__name__)


class ConnectionManager:
    """Tracks user_id -> set[WebSocket]; supports multiple simultaneous connections."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)
        log.info("WS connect user=%s total=%d", user_id, await self.count())

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(user_id)
            if sockets and websocket in sockets:
                sockets.discard(websocket)
                if not sockets:
                    self._connections.pop(user_id, None)
        log.info("WS disconnect user=%s", user_id)

    async def count(self) -> int:
        async with self._lock:
            return sum(len(s) for s in self._connections.values())

    async def send_to_user(self, user_id: str, message: dict) -> int:
        delivered = 0
        async with self._lock:
            sockets = list(self._connections.get(user_id, set()))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)
        return delivered

    async def broadcast_to_users(self, user_ids: list[str], message: dict) -> int:
        total = 0
        for uid in user_ids:
            try:
                total += await self.send_to_user(uid, message)
            except Exception:
                continue
        return total


manager = ConnectionManager()


async def emit_to_users(user_ids: list[str], event: dict) -> None:
    """Best-effort emit helper injected into services."""
    try:
        await manager.broadcast_to_users(user_ids, event)
    except Exception as e:
        log.warning("WS emit failed: %s", e)
