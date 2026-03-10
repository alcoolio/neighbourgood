"""In-memory sliding-window rate limiter middleware.

Limits:
  - Auth endpoints (/auth/login, /auth/register): 5 requests / 60 s per IP
  - Upload endpoints (paths ending with /image):  10 requests / 60 s per IP
  - All other API paths:                          60 requests / 60 s per IP

Returns HTTP 429 with a ``Retry-After`` header (seconds) when a limit is hit.
No external dependencies — uses only the stdlib threading.Lock + time module.
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

_AUTH_ENDPOINTS: frozenset[str] = frozenset({"/auth/login", "/auth/register"})
_WINDOW_SECONDS = 60

_AUTH_LIMIT = 5
_UPLOAD_LIMIT = 10
_GENERAL_LIMIT = 60


def _bucket(path: str) -> str:
    if path in _AUTH_ENDPOINTS:
        return "auth"
    if path.endswith("/image"):
        return "upload"
    return "general"


def _limit_for_bucket(b: str) -> int:
    return {"auth": _AUTH_LIMIT, "upload": _UPLOAD_LIMIT, "general": _GENERAL_LIMIT}[b]


class RateLimitStore:
    """Thread-safe in-memory sliding-window store."""

    def __init__(self) -> None:
        self._lock = Lock()
        # key: (ip, bucket) → list of monotonic timestamps
        self._windows: dict[tuple[str, str], list[float]] = defaultdict(list)

    def check_and_record(self, ip: str, path: str) -> tuple[bool, int]:
        """Return ``(allowed, retry_after_seconds)``.

        Records the request if allowed; does NOT record if rejected.
        """
        b = _bucket(path)
        limit = _limit_for_bucket(b)
        key = (ip, b)
        now = time.monotonic()
        cutoff = now - _WINDOW_SECONDS

        with self._lock:
            timestamps = self._windows[key]
            # Evict timestamps outside the sliding window
            self._windows[key] = [t for t in timestamps if t > cutoff]
            timestamps = self._windows[key]

            if len(timestamps) >= limit:
                # Retry after the oldest request ages out of the window
                retry_after = int(_WINDOW_SECONDS - (now - timestamps[0])) + 1
                return False, retry_after

            timestamps.append(now)
            return True, 0


# Module-level singleton so it persists across requests
_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply per-IP rate limiting to all API paths.

    Skipped when ``NG_DEBUG=true`` so the test suite and local development are
    not impacted by the in-memory counter state.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.config import settings  # local import to avoid circular at module load

        if settings.debug:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        allowed, retry_after = _store.check_and_record(ip, path)
        if not allowed:
            return Response(
                content='{"detail":"Too many requests. Please slow down."}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(retry_after),
                },
            )

        return await call_next(request)
