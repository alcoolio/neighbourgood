"""CSRF protection middleware.

Strategy
--------
NeighbourGood is a Bearer-token API, so classic cookie-based CSRF is not the
primary threat — a browser cannot attach an ``Authorization: Bearer …`` header
in a cross-origin form POST without triggering a CORS preflight that the server
will reject.  However, defence-in-depth is valuable and the platform does serve
browser clients, so we apply two complementary controls:

1. **Origin / Referer validation** — for every state-changing request
   (POST / PUT / PATCH / DELETE) that does NOT carry a ``Bearer`` token we
   verify that the ``Origin`` (or, as a fallback, the ``Referer``) header
   matches one of the configured CORS origins.  Requests without either header
   are rejected unless ``NG_DEBUG=true``.

2. **X-CSRF-Token header** — a CSRF double-submit token can be obtained via
   ``GET /auth/csrf-token`` and must be sent back as the ``X-CSRF-Token``
   request header for state-changing requests from browser sessions that do
   not use a Bearer token.  Bearer-authenticated requests are exempt (the
   token is required only when the endpoint is unauthenticated or
   cookie-authenticated).

Exemptions
----------
- ``GET``, ``HEAD``, ``OPTIONS`` — safe / idempotent; never checked.
- Any request that carries ``Authorization: Bearer …`` — the browser cannot
  attach that header in a cross-origin request without a CORS preflight, so
  CSRF via form/img/script injection is not possible.
- Requests from ``localhost`` in debug mode — eases local development.
"""

import hashlib
import hmac
import secrets
import time
from urllib.parse import urlparse

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

# HMAC-signed token valid for 24 hours
_TOKEN_TTL_SECONDS = 86_400
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


# ── Token helpers ─────────────────────────────────────────────────────────────

def generate_csrf_token() -> str:
    """Return a signed CSRF token of the form ``<nonce>.<timestamp>.<signature>``."""
    nonce = secrets.token_hex(16)
    ts = str(int(time.time()))
    sig = _sign(nonce, ts)
    return f"{nonce}.{ts}.{sig}"


def validate_csrf_token(token: str) -> bool:
    """Return ``True`` if *token* is a valid, unexpired CSRF token."""
    try:
        nonce, ts_str, sig = token.split(".", 2)
    except ValueError:
        return False

    # Check expiry
    try:
        issued_at = int(ts_str)
    except ValueError:
        return False
    if time.time() - issued_at > _TOKEN_TTL_SECONDS:
        return False

    # Constant-time MAC verification
    expected = _sign(nonce, ts_str)
    return hmac.compare_digest(sig, expected)


def _sign(nonce: str, ts: str) -> str:
    key = settings.secret_key.encode()
    msg = f"{nonce}.{ts}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


# ── Origin helpers ────────────────────────────────────────────────────────────

def _allowed_origins() -> frozenset[str]:
    origins = set(settings.cors_origins)
    # Always allow localhost in debug mode
    if settings.debug:
        origins.update({"http://localhost", "http://127.0.0.1"})
    return frozenset(origins)


def _origin_matches(request: Request) -> bool:
    """Return True if the request Origin/Referer is in the allowed set."""
    allowed = _allowed_origins()

    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/") in allowed

    referer = request.headers.get("referer")
    if referer:
        parsed = urlparse(referer)
        base = f"{parsed.scheme}://{parsed.netloc}"
        return base.rstrip("/") in allowed

    # No origin information — only allow in debug mode
    return settings.debug


# ── Middleware ────────────────────────────────────────────────────────────────

# Machine-to-machine endpoints that use their own auth mechanisms (e.g. webhook
# secrets, federation tokens) and are never called from a browser form.
_M2M_EXEMPT_PATHS: frozenset[str] = frozenset({
    "/telegram/webhook",
    "/federation/alerts/receive",
    "/federation/migrate/import",
    "/mesh/sync",
    "/webhooks/inbound",
})


class CsrfMiddleware(BaseHTTPMiddleware):
    """Reject state-changing requests that lack a valid CSRF proof.

    Skipped when ``NG_DEBUG=true`` so the test suite and local development are
    not interrupted.  In production this enforces:

    1. An ``Origin`` / ``Referer`` header matching a configured CORS origin.
    2. A valid ``X-CSRF-Token`` header for requests without a Bearer token.

    Bearer-token requests are exempt because browsers cannot attach an
    ``Authorization: Bearer`` header cross-origin without a CORS preflight.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.config import settings  # local import to avoid circular at module load

        if settings.debug:
            return await call_next(request)

        if request.method in _SAFE_METHODS:
            return await call_next(request)

        # Bearer-authenticated requests are exempt — the browser can't forge
        # the Authorization header in a cross-origin context.
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        # Machine-to-machine endpoints use their own auth — exempt from CSRF.
        if request.url.path in _M2M_EXEMPT_PATHS:
            return await call_next(request)

        # For unauthenticated state-changing requests, require:
        #   (a) a matching Origin/Referer, AND
        #   (b) a valid X-CSRF-Token header
        csrf_token = request.headers.get("x-csrf-token", "")

        if not _origin_matches(request):
            return Response(
                content='{"detail":"CSRF check failed: invalid or missing Origin header."}',
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

        if not validate_csrf_token(csrf_token):
            return Response(
                content='{"detail":"CSRF check failed: missing or invalid X-CSRF-Token header."}',
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

        return await call_next(request)
