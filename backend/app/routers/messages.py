"""In-app messaging endpoints – direct messages between users."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.message import Message
from app.models.user import User
from app.services.notifications import notify_new_message
from app.schemas.message import (
    ConversationSummary,
    MessageCreate,
    MessageList,
    MessageOut,
    UnreadCount,
)
from app.schemas.user import UserProfile

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message to another user."""
    if body.recipient_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot send a message to yourself",
        )

    recipient = db.query(User).filter(User.id == body.recipient_id, User.is_active).first()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    msg = Message(
        sender_id=current_user.id,
        recipient_id=body.recipient_id,
        booking_id=body.booking_id,
        body=body.body,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    _ = msg.sender
    _ = msg.recipient

    notify_new_message(recipient.email, current_user.display_name)

    return msg


@router.get("", response_model=MessageList)
def list_messages(
    partner_id: int | None = Query(None, description="Filter conversation with a specific user"),
    booking_id: int | None = Query(None, description="Filter messages related to a booking"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List messages for the current user, optionally filtered by conversation partner or booking."""
    query = db.query(Message).options(
        joinedload(Message.sender),
        joinedload(Message.recipient),
    ).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id,
        )
    )

    if partner_id is not None:
        query = query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == partner_id),
                and_(Message.sender_id == partner_id, Message.recipient_id == current_user.id),
            )
        )

    if booking_id is not None:
        query = query.filter(Message.booking_id == booking_id)

    total = query.count()
    items = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    return MessageList(items=items, total=total)


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversation partners with the last message and unread count."""
    # Get the partner ID for each message (the other user)
    partner_id_col = case(
        (Message.sender_id == current_user.id, Message.recipient_id),
        else_=Message.sender_id,
    ).label("partner_id")

    # Subquery: get distinct partner IDs
    partner_subq = (
        db.query(partner_id_col)
        .filter(
            or_(
                Message.sender_id == current_user.id,
                Message.recipient_id == current_user.id,
            )
        )
        .distinct()
        .subquery()
    )

    partner_ids = [row[0] for row in db.query(partner_subq.c.partner_id).all()]

    conversations = []
    for pid in partner_ids:
        partner = db.query(User).filter(User.id == pid).first()
        if not partner:
            continue

        # Last message in this conversation
        last_msg = (
            db.query(Message)
            .filter(
                or_(
                    and_(Message.sender_id == current_user.id, Message.recipient_id == pid),
                    and_(Message.sender_id == pid, Message.recipient_id == current_user.id),
                )
            )
            .order_by(Message.created_at.desc())
            .first()
        )

        # Count unread from this partner
        unread = (
            db.query(func.count(Message.id))
            .filter(
                Message.sender_id == pid,
                Message.recipient_id == current_user.id,
                Message.is_read == False,  # noqa: E712
            )
            .scalar()
        )

        if last_msg:
            conversations.append(
                ConversationSummary(
                    partner=partner,
                    last_message_body=last_msg.body,
                    last_message_at=last_msg.created_at,
                    unread_count=unread or 0,
                )
            )

    conversations.sort(key=lambda c: c.last_message_at, reverse=True)
    return conversations


@router.get("/unread", response_model=UnreadCount)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the total number of unread messages for the current user."""
    count = (
        db.query(func.count(Message.id))
        .filter(
            Message.recipient_id == current_user.id,
            Message.is_read == False,  # noqa: E712
        )
        .scalar()
    )
    return UnreadCount(count=count or 0)


@router.patch("/{message_id}/read", response_model=MessageOut)
def mark_as_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a message as read (recipient only)."""
    msg = (
        db.query(Message)
        .options(joinedload(Message.sender), joinedload(Message.recipient))
        .filter(Message.id == message_id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if msg.recipient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your message")

    msg.is_read = True
    db.commit()
    db.refresh(msg)
    return msg


@router.post("/conversation/{partner_id}/read")
def mark_conversation_read(
    partner_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all messages from a partner as read."""
    db.query(Message).filter(
        Message.sender_id == partner_id,
        Message.recipient_id == current_user.id,
        Message.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}
