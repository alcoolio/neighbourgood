"""User profile and reputation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.booking import Booking
from app.models.message import Message
from app.models.resource import Resource
from app.models.skill import Skill
from app.models.user import User
from app.schemas.user import (
    ChangeEmail,
    ChangePassword,
    DashboardOverview,
    ReputationOut,
    UserProfile,
    UserProfileUpdate,
)
from app.services.auth import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])

# ── Reputation scoring weights ─────────────────────────────────────

POINTS_RESOURCE_SHARED = 5
POINTS_BOOKING_COMPLETED_LENDER = 10
POINTS_BOOKING_COMPLETED_BORROWER = 3
POINTS_SKILL_OFFERED = 5
POINTS_SKILL_REQUESTED = 2

REPUTATION_LEVELS = [
    (0, "Newcomer"),
    (10, "Neighbour"),
    (30, "Helper"),
    (60, "Trusted"),
    (100, "Pillar"),
]


def _compute_reputation(db: Session, user_id: int) -> dict:
    """Compute reputation score and breakdown for a user."""
    resources_shared = db.query(Resource).filter(Resource.owner_id == user_id).count()

    bookings_completed_lender = (
        db.query(Booking)
        .join(Resource, Resource.id == Booking.resource_id)
        .filter(Resource.owner_id == user_id, Booking.status == "completed")
        .count()
    )

    bookings_completed_borrower = (
        db.query(Booking)
        .filter(Booking.borrower_id == user_id, Booking.status == "completed")
        .count()
    )

    skills_offered = (
        db.query(Skill).filter(Skill.owner_id == user_id, Skill.skill_type == "offer").count()
    )
    skills_requested = (
        db.query(Skill).filter(Skill.owner_id == user_id, Skill.skill_type == "request").count()
    )

    breakdown = {
        "resources_shared": resources_shared * POINTS_RESOURCE_SHARED,
        "lending_completed": bookings_completed_lender * POINTS_BOOKING_COMPLETED_LENDER,
        "borrowing_completed": bookings_completed_borrower * POINTS_BOOKING_COMPLETED_BORROWER,
        "skills_offered": skills_offered * POINTS_SKILL_OFFERED,
        "skills_requested": skills_requested * POINTS_SKILL_REQUESTED,
    }

    score = sum(breakdown.values())

    level = "Newcomer"
    for threshold, label in REPUTATION_LEVELS:
        if score >= threshold:
            level = label

    return {"score": score, "level": level, "breakdown": breakdown}


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
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/reputation", response_model=ReputationOut)
def get_my_reputation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's reputation score."""
    rep = _compute_reputation(db, current_user.id)
    return ReputationOut(
        user_id=current_user.id,
        display_name=current_user.display_name,
        **rep,
    )


@router.get("/{user_id}/reputation", response_model=ReputationOut)
def get_user_reputation(user_id: int, db: Session = Depends(get_db)):
    """Get a user's public reputation score."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    rep = _compute_reputation(db, user.id)
    return ReputationOut(
        user_id=user.id,
        display_name=user.display_name,
        **rep,
    )


@router.get("/me/dashboard", response_model=DashboardOverview)
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard overview with counts and reputation."""
    resources_count = db.query(Resource).filter(Resource.owner_id == current_user.id).count()

    skills_count = (
        db.query(Skill).filter(Skill.owner_id == current_user.id).count()
    )

    bookings_count = (
        db.query(Booking)
        .filter(
            ((Booking.borrower_id == current_user.id) | (Booking.resource_id.in_(
                db.query(Resource.id).filter(Resource.owner_id == current_user.id)
            )))
        )
        .count()
    )

    messages_unread_count = (
        db.query(Message)
        .filter(Message.recipient_id == current_user.id, Message.is_read == False)
        .count()
    )

    rep = _compute_reputation(db, current_user.id)

    return DashboardOverview(
        resources_count=resources_count,
        skills_count=skills_count,
        bookings_count=bookings_count,
        messages_unread_count=messages_unread_count,
        reputation_score=rep["score"],
        reputation_level=rep["level"],
    )


@router.post("/me/change-password", response_model=UserProfile)
def change_password(
    body: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-email", response_model=UserProfile)
def change_email(
    body: ChangeEmail,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's email."""
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect",
        )

    existing_user = db.query(User).filter(User.email == body.new_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email already in use",
        )

    current_user.email = body.new_email
    db.commit()
    db.refresh(current_user)
    return current_user
