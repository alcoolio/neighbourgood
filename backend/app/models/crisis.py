"""SQLAlchemy models for Red Sky (crisis) mode – votes, emergency tickets."""

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CrisisVote(Base):
    __tablename__ = "crisis_votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("communities.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    vote_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # activate, deactivate
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    community: Mapped["Community"] = relationship()  # noqa: F821
    user: Mapped["User"] = relationship()  # noqa: F821


class EmergencyTicket(Base):
    __tablename__ = "emergency_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("communities.id"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    ticket_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # request, offer, emergency_ping
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False
    )  # open, in_progress, resolved
    urgency: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False
    )  # low, medium, high, critical
    assigned_to_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    community: Mapped["Community"] = relationship()  # noqa: F821
    author: Mapped["User"] = relationship(foreign_keys=[author_id])  # noqa: F821
    assigned_to: Mapped["User | None"] = relationship(foreign_keys=[assigned_to_id])  # noqa: F821
