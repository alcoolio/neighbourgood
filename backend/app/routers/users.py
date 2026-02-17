"""User profile endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserProfile, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserProfile)
def update_my_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's profile fields."""
    if body.display_name is not None:
        current_user.display_name = body.display_name
    if body.neighbourhood is not None:
        current_user.neighbourhood = body.neighbourhood
    db.commit()
    db.refresh(current_user)
    return current_user
