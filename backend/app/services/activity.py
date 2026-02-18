"""Service for recording activity feed events."""

from sqlalchemy.orm import Session

from app.models.activity import Activity


def record_activity(
    db: Session,
    *,
    event_type: str,
    summary: str,
    actor_id: int,
    community_id: int | None = None,
) -> Activity:
    """Create an activity feed event."""
    event = Activity(
        event_type=event_type,
        summary=summary,
        actor_id=actor_id,
        community_id=community_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
