"""Pydantic schemas for communities (neighbourhood groups)."""

import datetime

from pydantic import BaseModel

from app.schemas.user import UserProfile


class CommunityCreate(BaseModel):
    name: str
    description: str | None = None
    postal_code: str
    city: str
    country_code: str = "DE"


class CommunityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CommunityMemberOut(BaseModel):
    id: int
    user: UserProfile
    role: str
    joined_at: datetime.datetime

    model_config = {"from_attributes": True}


class CommunityOut(BaseModel):
    id: int
    name: str
    description: str | None
    postal_code: str
    city: str
    country_code: str
    is_active: bool
    member_count: int = 0
    created_by: UserProfile
    merged_into_id: int | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CommunityList(BaseModel):
    items: list[CommunityOut]
    total: int


class MergeRequest(BaseModel):
    source_id: int
    target_id: int


class MergeSuggestion(BaseModel):
    source: CommunityOut
    target: CommunityOut
    reason: str
