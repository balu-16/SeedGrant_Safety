"""In-memory sliding-window rate limiter for abuse-sensitive endpoints.

Limiter instances live on ``app.state`` so each app (and each test) gets a
fresh one, and per-process only — every uvicorn worker limits independently.
Sufficient for V0 single-instance deploys; swap for a shared-store limiter
(e.g. Redis) before scaling horizontally.
"""

import time
from collections import deque
from collections.abc import Awaitable, Callable

from fastapi import Request

from app.core.exceptions import RateLimitError

_MAX_TRACKED_KEYS = 10_000


class SlidingWindowLimiter:
    def __init__(self, *, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits.setdefault(key, deque())
        cutoff = now - self._window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self._max_requests:
            raise RateLimitError("Too many requests. Please slow down and try again soon.")
        hits.append(now)
        if len(self._hits) > _MAX_TRACKED_KEYS:
            self._prune(now)

    def _prune(self, now: float) -> None:
        cutoff = now - self._window
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff]
        for key in stale:
            del self._hits[key]


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(*, max_requests: int, window_seconds: float, scope: str) -> Callable[[Request], Awaitable[None]]:
    """FastAPI dependency factory: per-client sliding window for one scope."""

    async def dependency(request: Request) -> None:
        existing = getattr(request.app.state, "rate_limiters", None)
        limiters: dict[str, SlidingWindowLimiter] = existing if isinstance(existing, dict) else {}
        request.app.state.rate_limiters = limiters
        limiter = limiters.get(scope)
        if limiter is None:
            limiter = limiters[scope] = SlidingWindowLimiter(max_requests=max_requests, window_seconds=window_seconds)
        limiter.check(f"{scope}:{_client_ip(request)}")

    return dependency
