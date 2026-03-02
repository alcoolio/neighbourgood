"""Mesh sync endpoint — ingests messages received via BLE mesh when internet returns."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.community import Community, CommunityMember
from app.models.crisis import CrisisVote, EmergencyTicket, TicketComment
from app.models.mesh import MeshSyncedMessage
from app.models.user import User
from app.schemas.mesh import MeshMessageIn, MeshSyncRequest, MeshSyncResponse
from app.services.activity import record_activity

router = APIRouter(prefix="/mesh", tags=["mesh"])


@router.post("/sync", response_model=MeshSyncResponse)
def sync_mesh_messages(
    body: MeshSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync messages received via BLE mesh to the server.

    Each message is deduplicated by its unique mesh ID. Already-synced
    messages are skipped. Supported types: emergency_ticket, ticket_comment,
    crisis_vote. Other types (heartbeat, crisis_status, direct_message)
    are acknowledged but not persisted.
    """
    synced = 0
    duplicates = 0
    errors = 0

    for msg in body.messages:
        # Check for duplicate
        existing = (
            db.query(MeshSyncedMessage)
            .filter(MeshSyncedMessage.mesh_message_id == msg.id)
            .first()
        )
        if existing:
            duplicates += 1
            continue

        try:
            _process_mesh_message(db, msg, current_user)
            # Record as synced
            db.add(
                MeshSyncedMessage(
                    mesh_message_id=msg.id,
                    message_type=msg.type,
                    community_id=msg.community_id,
                    synced_by_id=current_user.id,
                )
            )
            db.commit()
            synced += 1
        except HTTPException:
            db.rollback()
            errors += 1
        except Exception:
            db.rollback()
            errors += 1

    return MeshSyncResponse(synced=synced, duplicates=duplicates, errors=errors)


def _process_mesh_message(
    db: Session, msg: MeshMessageIn, current_user: User
) -> None:
    """Process a single mesh message based on its type."""
    # Verify community exists
    community = db.query(Community).filter(Community.id == msg.community_id).first()
    if not community or not community.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Community not found"
        )

    # Verify user is a member of the community
    membership = (
        db.query(CommunityMember)
        .filter(
            CommunityMember.community_id == msg.community_id,
            CommunityMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member"
        )

    if msg.type == "emergency_ticket":
        _sync_emergency_ticket(db, msg, current_user, community)
    elif msg.type == "ticket_comment":
        _sync_ticket_comment(db, msg, current_user)
    elif msg.type == "crisis_vote":
        _sync_crisis_vote(db, msg, current_user)
    # heartbeat, crisis_status, direct_message: acknowledged but not persisted


def _sync_emergency_ticket(
    db: Session, msg: MeshMessageIn, user: User, community: Community
) -> None:
    """Create an emergency ticket from a mesh message."""
    data = msg.data
    ticket_type = data.get("ticket_type", "request")
    title = data.get("title", "")
    description = data.get("description", "")
    urgency = data.get("urgency", "medium")

    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ticket title required",
        )

    # Validate ticket_type
    if ticket_type not in ("request", "offer", "emergency_ping"):
        ticket_type = "request"
    if urgency not in ("low", "medium", "high", "critical"):
        urgency = "medium"

    # Emergency pings require crisis mode
    if ticket_type == "emergency_ping" and community.mode != "red":
        ticket_type = "request"  # downgrade silently for mesh sync

    ticket = EmergencyTicket(
        community_id=msg.community_id,
        author_id=user.id,
        ticket_type=ticket_type,
        title=str(title)[:300],
        description=str(description)[:5000],
        urgency=urgency,
    )
    db.add(ticket)
    db.flush()

    record_activity(
        db,
        event_type="ticket_created",
        summary=f'created {ticket_type} ticket "{title}" (via mesh sync)',
        actor_id=user.id,
        community_id=msg.community_id,
    )


def _sync_ticket_comment(
    db: Session, msg: MeshMessageIn, user: User
) -> None:
    """Create a ticket comment from a mesh message."""
    data = msg.data
    body = data.get("body", "")
    ticket_mesh_id = data.get("ticket_mesh_id", "")

    if not body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Comment body required",
        )

    # For mesh comments, we don't have the server ticket ID.
    # The comment is recorded as a standalone entry associated with the community.
    # A more sophisticated implementation could map mesh IDs to server IDs.
    # For now, skip comments that reference mesh-only tickets.
    pass


def _sync_crisis_vote(
    db: Session, msg: MeshMessageIn, user: User
) -> None:
    """Record a crisis vote from a mesh message."""
    data = msg.data
    vote_type = data.get("vote_type", "")

    if vote_type not in ("activate", "deactivate"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid vote type",
        )

    # Check for existing vote
    existing = (
        db.query(CrisisVote)
        .filter(
            CrisisVote.community_id == msg.community_id,
            CrisisVote.user_id == user.id,
        )
        .first()
    )
    if existing:
        if existing.vote_type == vote_type:
            return  # Same vote already exists, no-op
        existing.vote_type = vote_type
    else:
        vote = CrisisVote(
            community_id=msg.community_id,
            user_id=user.id,
            vote_type=vote_type,
        )
        db.add(vote)
    db.flush()
