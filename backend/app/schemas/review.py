"""Pydantic schemas for transaction reviews/ratings."""

import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserProfile


class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewOut(BaseModel):
    id: int
    booking_id: int
    reviewer_id: int
    reviewee_id: int
    rating: int
    comment: str | None
    reviewer: UserProfile
    reviewee: UserProfile
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ReviewSummary(BaseModel):
    user_id: int
    average_rating: float
    total_reviews: int
