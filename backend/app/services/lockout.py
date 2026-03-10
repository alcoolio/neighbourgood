"""In-memory account lockout tracker.

Policy:
  - After 5 failed login attempts within a 15-minute window, the account is
    locked for 15 minutes from the time of the 5th failure.
  - A successful login clears the failure counter for that email.

This is intentionally in-memory (no DB writes on every failed attempt) to
keep it fast and to avoid leaking timing information. The trade-off is that
the counter resets on process restart, which is acceptable for this use-case.
"""

import time
from collections import defaultdict
from threading import Lock

_WINDOW_SECONDS = 15 * 60   # 15 min sliding window
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 15 * 60  # lock duration after threshold is reached

_lock = Lock()
# email (lowercased) → list of monotonic timestamps of failed attempts
_failures: dict[str, list[float]] = defaultdict(list)


def record_failure(email: str) -> None:
    """Record a failed login attempt for *email*."""
    now = time.monotonic()
    email = email.lower()
    with _lock:
        _failures[email].append(now)


def clear_failures(email: str) -> None:
    """Clear the failure counter after a successful login."""
    email = email.lower()
    with _lock:
        _failures[email] = []


def check_lockout(email: str) -> tuple[bool, int]:
    """Return ``(is_locked, retry_after_seconds)``.

    Evicts stale entries before checking so the window truly slides.
    """
    now = time.monotonic()
    cutoff = now - _WINDOW_SECONDS
    email = email.lower()

    with _lock:
        recent = [t for t in _failures[email] if t > cutoff]
        _failures[email] = recent

        if len(recent) >= _MAX_ATTEMPTS:
            # Lock until the oldest attempt in the window ages out
            retry_after = int(_LOCKOUT_SECONDS - (now - recent[0])) + 1
            return True, max(retry_after, 1)

        return False, 0
