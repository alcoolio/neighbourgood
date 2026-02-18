"""Pydantic schemas for community activity feed."""

import datetime

from pydantic import BaseModel

from app.schemas.user import UserProfile


class ActivityOut(BaseModel):
    id: int
    event_type: str
    summary: str
    actor_id: int
    community_id: int | None
    actor: UserProfile
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ActivityList(BaseModel):
    items: list[ActivityOut]
    total: int
