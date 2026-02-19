"""Pydantic schemas for resources."""

import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserProfile

VALID_CATEGORIES = [
    "tool", "vehicle", "electronics", "furniture",
    "food", "clothing", "skill", "other",
]

VALID_CONDITIONS = ["new", "good", "fair", "worn"]

CATEGORY_META = {
    "tool":        {"label": "Tools",       "icon": "wrench"},
    "vehicle":     {"label": "Vehicles",    "icon": "car"},
    "electronics": {"label": "Electronics", "icon": "zap"},
    "furniture":   {"label": "Furniture",   "icon": "armchair"},
    "food":        {"label": "Food",        "icon": "utensils"},
    "clothing":    {"label": "Clothing",    "icon": "shirt"},
    "skill":       {"label": "Skills",      "icon": "lightbulb"},
    "other":       {"label": "Other",       "icon": "box"},
}


class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    category: str
    condition: str | None = None
    community_id: int | None = None


class ResourceUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    category: str | None = None
    condition: str | None = None
    is_available: bool | None = None


class ResourceOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    condition: str | None
    image_url: str | None = None
    is_available: bool
    owner_id: int
    community_id: int | None = None
    owner: UserProfile
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class ResourceList(BaseModel):
    items: list[ResourceOut]
    total: int


class CategoryInfo(BaseModel):
    value: str
    label: str
    icon: str
