"""Public instance metadata endpoint for federation discovery."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.community import Community
from app.models.user import User


router = APIRouter(prefix="/instance", tags=["instance"])


class InstanceInfo(BaseModel):
    name: str
    description: str
    region: str
    url: str
    version: str
    platform_mode: str
    admin_name: str
    admin_contact: str
    community_count: int
    user_count: int


@router.get("/info", response_model=InstanceInfo)
def get_instance_info(db: Session = Depends(get_db)):
    """Public metadata about this instance. Used for federation directory crawling."""
    community_count = db.query(Community).filter(Community.is_active == True).count()  # noqa: E712
    user_count = db.query(User).count()

    return InstanceInfo(
        name=settings.instance_name,
        description=settings.instance_description,
        region=settings.instance_region,
        url=settings.instance_url,
        version=settings.app_version,
        platform_mode=settings.platform_mode,
        admin_name=settings.admin_name,
        admin_contact=settings.admin_contact,
        community_count=community_count,
        user_count=user_count,
    )
