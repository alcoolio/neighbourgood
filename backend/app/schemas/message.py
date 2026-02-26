"""Pydantic schemas for in-app messaging."""

import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserProfile


class MessageCreate(BaseModel):
    recipient_id: int
    booking_id: int | None = None
    skill_id: int | None = None
    body: str = Field(..., min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id: int
    sender_id: int
    sender: UserProfile
    recipient_id: int
    recipient: UserProfile
    booking_id: int | None
    skill_id: int | None
    body: str
    is_read: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class MessageList(BaseModel):
    items: list[MessageOut]
    total: int


class MessageableUser(BaseModel):
    """A user the current user can message (shares a community)."""
    id: int
    display_name: str
    email: str

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    """Summary of a conversation with another user."""
    partner: UserProfile
    last_message_body: str
    last_message_at: datetime.datetime
    unread_count: int


class UnreadCount(BaseModel):
    count: int
