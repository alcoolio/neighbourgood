"""Pydantic schemas for skill exchange listings."""

import datetime

from pydantic import BaseModel

from app.schemas.user import UserProfile

VALID_SKILL_CATEGORIES = [
    "tutoring",
    "repairs",
    "cooking",
    "languages",
    "music",
    "gardening",
    "tech",
    "crafts",
    "fitness",
    "other",
]

SKILL_CATEGORY_META = {
    "tutoring":  {"label": "Tutoring",    "icon": "book"},
    "repairs":   {"label": "Repairs",     "icon": "wrench"},
    "cooking":   {"label": "Cooking",     "icon": "utensils"},
    "languages": {"label": "Languages",   "icon": "globe"},
    "music":     {"label": "Music",       "icon": "music"},
    "gardening": {"label": "Gardening",   "icon": "leaf"},
    "tech":      {"label": "Tech",        "icon": "laptop"},
    "crafts":    {"label": "Crafts",      "icon": "scissors"},
    "fitness":   {"label": "Fitness",     "icon": "dumbbell"},
    "other":     {"label": "Other",       "icon": "star"},
}

VALID_SKILL_TYPES = ["offer", "request"]


class SkillCreate(BaseModel):
    title: str
    description: str | None = None
    category: str
    skill_type: str  # "offer" or "request"
    community_id: int | None = None


class SkillUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    skill_type: str | None = None


class SkillOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    skill_type: str
    owner_id: int
    community_id: int | None
    owner: UserProfile
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class SkillList(BaseModel):
    items: list[SkillOut]
    total: int


class SkillCategoryInfo(BaseModel):
    value: str
    label: str
    icon: str
