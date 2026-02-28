"""SQLAlchemy models for communities (neighbourhood groups)."""

import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(5), default="DE", nullable=False)
    primary_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(10), default="blue", nullable=False)  # blue (normal) / red (crisis)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    telegram_group_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    merged_into_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("communities.id"), nullable=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])  # noqa: F821
    merged_into: Mapped["Community | None"] = relationship(
        foreign_keys=[merged_into_id], remote_side=[id]
    )
    members: Mapped[list["CommunityMember"]] = relationship(back_populates="community")


class CommunityMember(Base):
    __tablename__ = "community_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community_id: Mapped[int] = mapped_column(Integer, ForeignKey("communities.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)  # member, leader, admin
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    community: Mapped["Community"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()  # noqa: F821
