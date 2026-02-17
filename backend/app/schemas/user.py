"""Pydantic schemas for user profiles."""

import datetime

from pydantic import BaseModel


class UserProfile(BaseModel):
    id: int
    email: str
    display_name: str
    neighbourhood: str | None
    role: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    neighbourhood: str | None = None
