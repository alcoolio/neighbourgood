"""Pydantic schemas for bookings (borrow requests)."""

import datetime

from pydantic import BaseModel

from app.schemas.user import UserProfile

VALID_BOOKING_STATUSES = ["pending", "approved", "rejected", "cancelled", "completed"]


class BookingCreate(BaseModel):
    resource_id: int
    start_date: datetime.date
    end_date: datetime.date
    message: str | None = None


class BookingStatusUpdate(BaseModel):
    status: str


class BookingOut(BaseModel):
    id: int
    resource_id: int
    resource_title: str | None = None
    borrower_id: int
    borrower: UserProfile
    start_date: datetime.date
    end_date: datetime.date
    message: str | None
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class BookingList(BaseModel):
    items: list[BookingOut]
    total: int
