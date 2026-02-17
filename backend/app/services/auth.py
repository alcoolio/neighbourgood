"""Authentication service – password hashing and JWT tokens.

Uses a minimal HS256 JWT implementation (stdlib only) to avoid
cryptography library issues in constrained environments.
"""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Minimal HS256 JWT ──────────────────────────────────────────────


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def create_access_token(user_id: int) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = _b64url_encode(
        json.dumps({"sub": str(user_id), "exp": int(expire.timestamp())}).encode()
    )
    signature = _b64url_encode(
        hmac.new(
            settings.secret_key.encode(),
            f"{header}.{payload}".encode(),
            hashlib.sha256,
        ).digest()
    )
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> int | None:
    """Return user_id from token, or None if invalid / expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, signature = parts

        expected = _b64url_encode(
            hmac.new(
                settings.secret_key.encode(),
                f"{header}.{payload}".encode(),
                hashlib.sha256,
            ).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None

        claims = json.loads(_b64url_decode(payload))
        if datetime.now(timezone.utc).timestamp() > claims.get("exp", 0):
            return None

        return int(claims["sub"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return None
