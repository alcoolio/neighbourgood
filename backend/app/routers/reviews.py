"""Review and rating endpoints for completed bookings."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.booking import Booking
from app.models.resource import Resource
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut, ReviewSummary

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Leave a review for a completed booking (borrower reviews lender, or vice versa)."""
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.resource))
        .filter(Booking.id == body.booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can only review completed bookings",
        )

    resource = booking.resource
    is_borrower = booking.borrower_id == current_user.id
    is_lender = resource.owner_id == current_user.id if resource else False

    if not is_borrower and not is_lender:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the borrower or lender can review this booking",
        )

    # Determine who is being reviewed
    if is_borrower:
        reviewee_id = resource.owner_id if resource else booking.borrower_id
    else:
        reviewee_id = booking.borrower_id

    # Check for duplicate review
    existing = (
        db.query(Review)
        .filter(
            Review.booking_id == body.booking_id,
            Review.reviewer_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this booking",
        )

    review = Review(
        booking_id=body.booking_id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    _ = review.reviewer
    _ = review.reviewee
    return review


@router.get("/booking/{booking_id}", response_model=list[ReviewOut])
def get_booking_reviews(booking_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a specific booking."""
    reviews = (
        db.query(Review)
        .options(joinedload(Review.reviewer), joinedload(Review.reviewee))
        .filter(Review.booking_id == booking_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return reviews


@router.get("/user/{user_id}", response_model=list[ReviewOut])
def get_user_reviews(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get all reviews received by a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    reviews = (
        db.query(Review)
        .options(joinedload(Review.reviewer), joinedload(Review.reviewee))
        .filter(Review.reviewee_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return reviews


@router.get("/user/{user_id}/summary", response_model=ReviewSummary)
def get_user_review_summary(user_id: int, db: Session = Depends(get_db)):
    """Get average rating and total review count for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = (
        db.query(
            sqlfunc.count(Review.id).label("total"),
            sqlfunc.avg(Review.rating).label("avg"),
        )
        .filter(Review.reviewee_id == user_id)
        .first()
    )

    total = result.total or 0
    avg = round(float(result.avg), 2) if result.avg else 0.0

    return ReviewSummary(user_id=user_id, average_rating=avg, total_reviews=total)
