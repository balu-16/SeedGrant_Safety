"""Authenticated WebSocket connection manager."""

import asyncio

from fastapi import WebSocket

from app.core.logging import get_logger

log = get_logger(__name__)


class ConnectionManager:
    """Tracks user_id -> set[WebSocket]; supports multiple simultaneous connections.

    Admin accounts are additionally indexed in a separate registry so platform
    events (e.g. every emergency) can fan out to the admin portal's live monitor
    without belonging to any single user channel.
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._admin_connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket, *, is_admin: bool = False) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)
            if is_admin:
                self._admin_connections.setdefault(user_id, set()).add(websocket)
        log.info("WS connect user=%s admin=%s", user_id, is_admin)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(user_id)
            if sockets and websocket in sockets:
                sockets.discard(websocket)
                if not sockets:
                    self._connections.pop(user_id, None)
            admin_sockets = self._admin_connections.get(user_id)
            if admin_sockets and websocket in admin_sockets:
                admin_sockets.discard(websocket)
                if not admin_sockets:
                    self._admin_connections.pop(user_id, None)
        log.info("WS disconnect user=%s", user_id)

    @staticmethod
    async def _send(sockets: list[WebSocket], message: dict) -> tuple[int, list[WebSocket]]:
        delivered = 0
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                # A stalled client must not delay delivery to other sockets or
                # block the caller (e.g. the SOS request path).
                await asyncio.wait_for(ws.send_json(message), timeout=5.0)
                delivered += 1
            except Exception:
                dead.append(ws)
        return delivered, dead

    async def send_to_user(self, user_id: str, message: dict) -> int:
        async with self._lock:
            sockets = list(self._connections.get(user_id, set()))
        delivered, dead = await self._send(sockets, message)
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

    async def broadcast_to_admins(self, message: dict) -> int:
        async with self._lock:
            entries = [(uid, list(sockets)) for uid, sockets in self._admin_connections.items()]
        total = 0
        for uid, sockets in entries:
            delivered, dead = await self._send(sockets, message)
            total += delivered
            for ws in dead:
                await self.disconnect(uid, ws)
        return total

    async def admin_count(self) -> int:
        async with self._lock:
            return sum(len(sockets) for sockets in self._admin_connections.values())


manager = ConnectionManager()


async def emit_to_users(user_ids: list[str], event: dict) -> None:
    """Best-effort emit helper injected into services."""
    try:
        await manager.broadcast_to_users(user_ids, event)
    except Exception as e:
        log.warning("WS emit failed: %s", e)


async def emit_to_admins(event: dict) -> None:
    """Best-effort emit to every connected admin (live SOS monitor)."""
    try:
        await manager.broadcast_to_admins(event)
    except Exception as e:
        log.warning("WS admin emit failed: %s", e)
