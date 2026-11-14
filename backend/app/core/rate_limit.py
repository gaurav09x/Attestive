"""Per-process sliding-window rate limiting.

Auth endpoints get a tighter budget than the rest of the API. The window is held
in memory, so the limit is per running process: a multi-instance deployment
needs a shared counter (see docs/RUNBOOK.md). Rejected requests receive the same
error envelope as every other failure plus `Retry-After`.
"""

from __future__ import annotations

import threading
import time
from collections import deque

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

WINDOW_SECONDS = 60
MAX_TRACKED_KEYS = 20_000


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _bucket(self, path: str) -> tuple[str, int]:
        if "/auth/" in path:
            return "auth", settings.RATE_LIMIT_AUTH_PER_MINUTE
        return "default", settings.RATE_LIMIT_DEFAULT_PER_MINUTE

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if (
            not settings.RATE_LIMIT_ENABLED
            or request.method == "OPTIONS"
            or request.url.path.endswith("/health")
        ):
            return await call_next(request)

        bucket, limit = self._bucket(request.url.path)
        if limit <= 0:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        key = f"{client}:{bucket}"
        now = time.monotonic()

        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= limit:
                retry_after = max(1, int(hits[0] + WINDOW_SECONDS - now) + 1)
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limited",
                            "message": "Too many requests. Please slow down and try again shortly.",
                        }
                    },
                    headers={"Retry-After": str(retry_after)},
                )
                return response
            hits.append(now)
            if len(self._hits) > MAX_TRACKED_KEYS:
                # Drop keys with no hit inside the current window, otherwise the
                # dict grows without bound on a long-lived process.
                cutoff = now - WINDOW_SECONDS
                for stale in [k for k, v in self._hits.items() if not v or v[-1] <= cutoff]:
                    del self._hits[stale]

        return await call_next(request)
