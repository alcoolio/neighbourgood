"""Pydantic schemas for webhooks and Telegram integration."""

import datetime

from pydantic import BaseModel, Field


WEBHOOK_EVENTS = [
    "message.new",
    "booking.created",
    "booking.status_changed",
    "crisis.mode_changed",
    "ticket.created",
    "ticket.assigned",
    "resource.shared",
    "skill.created",
    "member.joined",
]


class WebhookCreate(BaseModel):
    url: str = Field(..., max_length=500)
    secret: str = Field(..., min_length=8, max_length=64)
    event_types: list[str]

    def validate_events(self) -> list[str]:
        invalid = [e for e in self.event_types if e not in WEBHOOK_EVENTS]
        if invalid:
            raise ValueError(f"Unknown event types: {invalid}. Valid: {WEBHOOK_EVENTS}")
        return self.event_types


class WebhookOut(BaseModel):
    id: int
    owner_type: str
    owner_id: int
    url: str
    event_types: list[str]
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj) -> "WebhookOut":
        import json
        return cls(
            id=obj.id,
            owner_type=obj.owner_type,
            owner_id=obj.owner_id,
            url=obj.url,
            event_types=json.loads(obj.event_types),
            is_active=obj.is_active,
            created_at=obj.created_at,
        )


class TelegramLinkStart(BaseModel):
    bot_url: str


class TelegramGroupLinkStart(BaseModel):
    token: str
