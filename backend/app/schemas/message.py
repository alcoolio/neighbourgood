"""Pydantic schemas for in-app messaging."""

import datetime

from pydantic import BaseModel

from app.schemas.user import UserProfile


class MessageCreate(BaseModel):
    recipient_id: int
    booking_id: int | None = None
    body: str


class MessageOut(BaseModel):
    id: int
    sender_id: int
    sender: UserProfile
    recipient_id: int
    recipient: UserProfile
    booking_id: int | None
    body: str
    is_read: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class MessageList(BaseModel):
    items: list[MessageOut]
    total: int


class ConversationSummary(BaseModel):
    """Summary of a conversation with another user."""
    partner: UserProfile
    last_message_body: str
    last_message_at: datetime.datetime
    unread_count: int


class UnreadCount(BaseModel):
    count: int
