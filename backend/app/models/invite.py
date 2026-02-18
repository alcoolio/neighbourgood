"""SQLAlchemy model for community invite codes."""

import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    community_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("communities.id"), nullable=False, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    community: Mapped["Community"] = relationship()  # noqa: F821
    created_by: Mapped["User"] = relationship()  # noqa: F821
