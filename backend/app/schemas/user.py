"""Pydantic schemas for user profiles."""

import datetime
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


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


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangeEmail(BaseModel):
    new_email: EmailStr
    password: str


class DashboardOverview(BaseModel):
    resources_count: int
    skills_count: int
    bookings_count: int
    messages_unread_count: int
    reputation_score: int
    reputation_level: str


class ReputationOut(BaseModel):
    user_id: int
    display_name: str
    score: int
    level: str
    breakdown: dict[str, int]
