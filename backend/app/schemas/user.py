"""Pydantic schemas for user profiles."""

import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    id: int
    email: str
    display_name: str
    neighbourhood: str | None
    role: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    neighbourhood: str | None = Field(None, max_length=200)


class ReputationOut(BaseModel):
    user_id: int
    display_name: str
    score: int
    level: str
    breakdown: dict[str, int]
