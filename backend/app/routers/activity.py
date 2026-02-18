"""Community activity feed endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import ActivityList, ActivityOut

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=ActivityList)
def list_activity(
    community_id: int | None = Query(None, description="Filter by community"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List recent activity events, optionally filtered by community."""
    query = db.query(Activity).options(joinedload(Activity.actor))

    if community_id is not None:
        query = query.filter(Activity.community_id == community_id)

    total = query.count()
    items = query.order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()
    return ActivityList(
        items=[ActivityOut.model_validate(a) for a in items],
        total=total,
    )


@router.get("/my", response_model=ActivityList)
def list_my_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the authenticated user's own activity."""
    query = (
        db.query(Activity)
        .options(joinedload(Activity.actor))
        .filter(Activity.actor_id == current_user.id)
    )
    total = query.count()
    items = query.order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()
    return ActivityList(
        items=[ActivityOut.model_validate(a) for a in items],
        total=total,
    )
