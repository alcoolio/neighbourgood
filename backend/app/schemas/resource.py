"""Pydantic schemas for resources."""

import datetime

from pydantic import BaseModel

from app.schemas.user import UserProfile

VALID_CATEGORIES = [
    "tool", "vehicle", "electronics", "furniture",
    "food", "clothing", "skill", "other",
]

VALID_CONDITIONS = ["new", "good", "fair", "worn"]


class ResourceCreate(BaseModel):
    title: str
    description: str | None = None
    category: str
    condition: str | None = None


class ResourceUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    condition: str | None = None
    is_available: bool | None = None


class ResourceOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    condition: str | None
    is_available: bool
    owner_id: int
    owner: UserProfile
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class ResourceList(BaseModel):
    items: list[ResourceOut]
    total: int
