"""Pydantic schemas for community invite codes."""

import datetime

from pydantic import BaseModel


class InviteCreate(BaseModel):
    community_id: int
    max_uses: int | None = None
    expires_in_hours: int | None = None  # None = never expires


class InviteOut(BaseModel):
    id: int
    code: str
    community_id: int
    created_by_id: int
    max_uses: int | None
    use_count: int
    is_active: bool
    expires_at: datetime.datetime | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class InviteRedeemResult(BaseModel):
    community_id: int
    community_name: str
    message: str
