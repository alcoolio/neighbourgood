"""Pydantic schemas for Red Sky (crisis) mode features."""

import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserProfile


# ── Crisis mode toggle ────────────────────────────────────────────


class CrisisModeToggle(BaseModel):
    mode: str = Field(..., pattern="^(blue|red)$")


class CrisisModeStatus(BaseModel):
    community_id: int
    mode: str
    votes_to_activate: int = 0
    votes_to_deactivate: int = 0
    total_members: int = 0
    threshold_pct: int = 60


# ── Voting ────────────────────────────────────────────────────────


class CrisisVoteCreate(BaseModel):
    vote_type: str = Field(..., pattern="^(activate|deactivate)$")


class CrisisVoteOut(BaseModel):
    id: int
    community_id: int
    user: UserProfile
    vote_type: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Emergency tickets ─────────────────────────────────────────────


class EmergencyTicketCreate(BaseModel):
    ticket_type: str = Field(..., pattern="^(request|offer|emergency_ping)$")
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field("", max_length=5000)
    urgency: str = Field("medium", pattern="^(low|medium|high|critical)$")


class EmergencyTicketUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = Field(None, max_length=5000)
    status: str | None = Field(None, pattern="^(open|in_progress|resolved)$")
    urgency: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    assigned_to_id: int | None = None


class EmergencyTicketOut(BaseModel):
    id: int
    community_id: int
    author: UserProfile
    ticket_type: str
    title: str
    description: str
    status: str
    urgency: str
    assigned_to: UserProfile | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class EmergencyTicketList(BaseModel):
    items: list[EmergencyTicketOut]
    total: int


# ── Leader management ─────────────────────────────────────────────


class LeaderOut(BaseModel):
    id: int
    user: UserProfile
    role: str
    joined_at: datetime.datetime

    model_config = {"from_attributes": True}
