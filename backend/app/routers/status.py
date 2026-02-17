"""Status endpoint – health check and platform mode indicator."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["status"])


@router.get("/status")
def get_status():
    """Return platform health and current operating mode.

    The `mode` field reflects the dual-state architecture:
    - **blue** – normal "Blue Sky" operation (sharing, booking, gamification)
    - **red**  – "Red Sky" crisis mode (emergency coordination, low-bandwidth UI)
    """
    return {
        "status": "ok",
        "version": settings.app_version,
        "mode": settings.platform_mode,
    }
