"""SQLAlchemy model for community activity feed events."""

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Event types for the activity feed
EVENT_TYPES = [
    "resource_shared",
    "resource_borrowed",
    "booking_completed",
    "skill_offered",
    "skill_requested",
    "member_joined",
]


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    community_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("communities.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    actor: Mapped["User"] = relationship()  # noqa: F821
