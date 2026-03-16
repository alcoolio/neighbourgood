"""SQLAlchemy model for BLE mesh message deduplication tracking."""

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MeshSyncedMessage(Base):
    """Tracks mesh message IDs that have been synced to prevent duplicates."""

    __tablename__ = "mesh_synced_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mesh_message_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    message_type: Mapped[str] = mapped_column(String(30), nullable=False)
    community_id: Mapped[int] = mapped_column(Integer, ForeignKey("communities.id"), nullable=False, index=True)
    synced_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    server_object_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    synced_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
