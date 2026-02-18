"""Community invite code endpoints."""

import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.community import Community, CommunityMember
from app.models.invite import Invite
from app.models.user import User
from app.schemas.invite import InviteCreate, InviteOut, InviteRedeemResult
from app.services.activity import record_activity

router = APIRouter(prefix="/invites", tags=["invites"])


def _generate_code() -> str:
    """Generate a URL-safe invite code."""
    return secrets.token_urlsafe(16)


@router.post("", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
def create_invite(
    body: InviteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an invite code for a community (members only)."""
    # Verify community exists and user is a member
    community = db.query(Community).filter(Community.id == body.community_id).first()
    if not community or not community.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    membership = (
        db.query(CommunityMember)
        .filter(
            CommunityMember.community_id == body.community_id,
            CommunityMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member to create invites",
        )

    expires_at = None
    if body.expires_in_hours is not None:
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=body.expires_in_hours)

    invite = Invite(
        code=_generate_code(),
        community_id=body.community_id,
        created_by_id=current_user.id,
        max_uses=body.max_uses,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("", response_model=list[InviteOut])
def list_invites(
    community_id: int = Query(..., description="Community to list invites for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List invite codes for a community (members only)."""
    membership = (
        db.query(CommunityMember)
        .filter(
            CommunityMember.community_id == community_id,
            CommunityMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member to view invites",
        )

    invites = (
        db.query(Invite)
        .filter(Invite.community_id == community_id, Invite.is_active.is_(True))
        .order_by(Invite.created_at.desc())
        .all()
    )
    return invites


@router.post("/{code}/redeem", response_model=InviteRedeemResult)
def redeem_invite(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Redeem an invite code to join a community."""
    invite = db.query(Invite).filter(Invite.code == code).first()
    if not invite or not invite.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code")

    # Check expiry
    if invite.expires_at and invite.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has expired")

    # Check max uses
    if invite.max_uses is not None and invite.use_count >= invite.max_uses:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has been fully used")

    community = db.query(Community).filter(Community.id == invite.community_id).first()
    if not community or not community.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    # Check if already a member
    existing = (
        db.query(CommunityMember)
        .filter(
            CommunityMember.community_id == invite.community_id,
            CommunityMember.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        return InviteRedeemResult(
            community_id=community.id,
            community_name=community.name,
            message="You are already a member of this community.",
        )

    # Join the community
    membership = CommunityMember(
        community_id=invite.community_id,
        user_id=current_user.id,
        role="member",
    )
    db.add(membership)
    invite.use_count += 1
    db.commit()

    record_activity(
        db,
        event_type="member_joined",
        summary=f"joined \"{community.name}\" via invite",
        actor_id=current_user.id,
        community_id=community.id,
    )

    return InviteRedeemResult(
        community_id=community.id,
        community_name=community.name,
        message=f"Welcome to {community.name}!",
    )


@router.delete("/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(
    invite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke an invite code (creator or community admin only)."""
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")

    # Check if user is the invite creator or a community admin
    if invite.created_by_id != current_user.id:
        membership = (
            db.query(CommunityMember)
            .filter(
                CommunityMember.community_id == invite.community_id,
                CommunityMember.user_id == current_user.id,
                CommunityMember.role == "admin",
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the invite creator or a community admin can revoke invites",
            )

    invite.is_active = False
    db.commit()
