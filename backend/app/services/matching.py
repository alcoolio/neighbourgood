"""Smart matching engine: rule-based + optional AI enhancement."""

import json
import logging
import re
from collections import Counter

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.community import Community, CommunityMember
from app.models.crisis import EmergencyTicket
from app.models.resource import Resource
from app.models.skill import Skill
from app.models.user import User
from app.services.ai_client import AIClient

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens (≥3 chars) from text."""
    if not text:
        return set()
    return {w for w in re.findall(r"[a-zA-Z]{3,}", text.lower())}


def _keyword_overlap(a: str | None, b: str | None) -> float:
    """Return 0.0–1.0 overlap ratio between two text strings."""
    tokens_a = _tokenize(a or "")
    tokens_b = _tokenize(b or "")
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _reputation_bonus(db: Session, user_id: int) -> float:
    """Return 0.0–0.2 bonus based on user activity (simplified reputation)."""
    resource_count = db.query(Resource).filter(Resource.owner_id == user_id).count()
    completed = db.query(Booking).filter(
        Booking.borrower_id == user_id, Booking.status == "completed"
    ).count()
    skill_count = db.query(Skill).filter(Skill.owner_id == user_id).count()
    score = resource_count * 2 + completed * 5 + skill_count * 2
    if score >= 100:
        return 0.2
    if score >= 40:
        return 0.15
    if score >= 10:
        return 0.1
    return 0.0


# ── Skill matching ───────────────────────────────────────────────────────────


def get_skill_matches(db: Session, user: User, community_id: int | None = None) -> list[dict]:
    """Find skill offers that match skill requests in the user's communities."""
    # Determine which communities to search
    if community_id:
        community_ids = [community_id]
    else:
        memberships = db.query(CommunityMember.community_id).filter(
            CommunityMember.user_id == user.id
        ).all()
        community_ids = [m[0] for m in memberships]

    if not community_ids:
        return []

    # Get skill requests in those communities
    requests = db.query(Skill).filter(
        Skill.community_id.in_(community_ids),
        Skill.skill_type == "request",
    ).all()

    if not requests:
        return []

    # Get skill offers in those communities (exclude user's own)
    offers = db.query(Skill).filter(
        Skill.community_id.in_(community_ids),
        Skill.skill_type == "offer",
        Skill.owner_id != user.id,
    ).all()

    matches = []
    for req in requests:
        for offer in offers:
            score = 0.0
            # Category match
            if req.category == offer.category:
                score += 0.5
            else:
                continue  # no cross-category matching in rule-based mode

            # Keyword overlap in title + description
            text_a = f"{req.title} {req.description or ''}"
            text_b = f"{offer.title} {offer.description or ''}"
            score += _keyword_overlap(text_a, text_b) * 0.3

            # Reputation bonus for the offer provider
            score += _reputation_bonus(db, offer.owner_id)

            score = min(score, 1.0)

            reason = f"Matches {req.skill_type} \"{req.title}\" — same category ({offer.category})"

            matches.append({
                "match_type": "skill_match",
                "item_id": offer.id,
                "item_title": offer.title,
                "item_type": "skill",
                "category": offer.category,
                "score": round(score, 2),
                "reason": reason,
                "ai_enhanced": False,
            })

    # Deduplicate by item_id, keep highest score
    seen: dict[int, dict] = {}
    for m in matches:
        existing = seen.get(m["item_id"])
        if existing is None or m["score"] > existing["score"]:
            seen[m["item_id"]] = m
    matches = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
    return matches[:10]


# ── Resource suggestions ─────────────────────────────────────────────────────


def get_resource_suggestions(db: Session, user: User, community_id: int | None = None) -> list[dict]:
    """Suggest resources based on user's past booking categories."""
    # Get categories from past bookings
    past_bookings = db.query(Booking).filter(Booking.borrower_id == user.id).all()
    booked_resource_ids = {b.resource_id for b in past_bookings}
    category_counts: Counter[str] = Counter()
    for booking in past_bookings:
        resource = db.query(Resource).filter(Resource.id == booking.resource_id).first()
        if resource:
            category_counts[resource.category] += 1

    if not category_counts:
        return []

    # Determine communities
    if community_id:
        community_ids = [community_id]
    else:
        memberships = db.query(CommunityMember.community_id).filter(
            CommunityMember.user_id == user.id
        ).all()
        community_ids = [m[0] for m in memberships]

    if not community_ids:
        return []

    # Find available resources in those categories (not owned by user, not already booked)
    candidates = db.query(Resource).filter(
        Resource.community_id.in_(community_ids),
        Resource.is_available == True,  # noqa: E712
        Resource.owner_id != user.id,
    ).all()

    top_category_count = max(category_counts.values()) if category_counts else 1
    suggestions = []
    for res in candidates:
        if res.id in booked_resource_ids:
            continue
        if res.category not in category_counts:
            continue

        # Score: category frequency (0–0.5) + reputation bonus (0–0.2) + recency (0–0.3)
        cat_score = (category_counts[res.category] / top_category_count) * 0.5
        rep_bonus = _reputation_bonus(db, res.owner_id)

        # Recency: newer items score higher (simple heuristic)
        recency_score = 0.15  # default mid-range

        score = min(cat_score + rep_bonus + recency_score, 1.0)

        suggestions.append({
            "match_type": "resource_suggestion",
            "item_id": res.id,
            "item_title": res.title,
            "item_type": "resource",
            "category": res.category,
            "score": round(score, 2),
            "reason": f"Based on your interest in {res.category} items",
            "ai_enhanced": False,
        })

    suggestions.sort(key=lambda x: x["score"], reverse=True)
    return suggestions[:10]


# ── Unmet needs (Red Sky) ────────────────────────────────────────────────────


def get_unmet_needs(db: Session, community_id: int) -> list[dict]:
    """List open emergency requests with few or no matching offers."""
    requests = db.query(EmergencyTicket).filter(
        EmergencyTicket.community_id == community_id,
        EmergencyTicket.ticket_type == "request",
        EmergencyTicket.status == "open",
    ).all()

    offers = db.query(EmergencyTicket).filter(
        EmergencyTicket.community_id == community_id,
        EmergencyTicket.ticket_type == "offer",
        EmergencyTicket.status == "open",
    ).all()

    results = []
    for req in requests:
        req_tokens = _tokenize(f"{req.title} {req.description}")
        offer_count = 0
        for offer in offers:
            offer_tokens = _tokenize(f"{offer.title} {offer.description}")
            if req_tokens & offer_tokens:
                offer_count += 1

        results.append({
            "ticket_id": req.id,
            "title": req.title,
            "ticket_type": req.ticket_type,
            "urgency": req.urgency,
            "created_at": req.created_at,
            "offer_count": offer_count,
        })

    # Sort: fewest offers first, then by urgency priority
    urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    results.sort(key=lambda x: (x["offer_count"], urgency_order.get(x["urgency"], 99)))
    return results


# ── AI enhancement ───────────────────────────────────────────────────────────


def enhance_with_ai(
    ai_client: AIClient,
    suggestions: list[dict],
    context: str,
) -> list[dict]:
    """Use an LLM to re-rank suggestions and add better reason text.

    Falls back to the original suggestions if the AI call fails.
    """
    if not suggestions:
        return suggestions

    prompt_items = "\n".join(
        f"- [{s['item_type']}] \"{s['item_title']}\" (category: {s['category']}, score: {s['score']})"
        for s in suggestions[:10]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a community resource matching assistant. "
                "Re-rank the following suggestions by relevance and provide a short, "
                "friendly reason for each match. Respond with a JSON array of objects "
                "with keys: item_title, score (0.0-1.0), reason (max 100 chars). "
                "Only output valid JSON, no markdown."
            ),
        },
        {
            "role": "user",
            "content": f"Context: {context}\n\nSuggestions:\n{prompt_items}",
        },
    ]

    response = ai_client.chat(messages, max_tokens=500)
    if response is None:
        return suggestions

    try:
        ai_results = json.loads(response)
        if not isinstance(ai_results, list):
            return suggestions

        # Build a lookup by title
        title_to_ai: dict[str, dict] = {}
        for item in ai_results:
            if isinstance(item, dict) and "item_title" in item:
                title_to_ai[item["item_title"]] = item

        # Merge AI results into original suggestions
        for s in suggestions:
            ai_data = title_to_ai.get(s["item_title"])
            if ai_data:
                if "score" in ai_data and isinstance(ai_data["score"], (int, float)):
                    s["score"] = round(min(max(float(ai_data["score"]), 0.0), 1.0), 2)
                if "reason" in ai_data and isinstance(ai_data["reason"], str):
                    s["reason"] = ai_data["reason"][:500]
                s["ai_enhanced"] = True

        suggestions.sort(key=lambda x: x["score"], reverse=True)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Failed to parse AI re-ranking response: %s", exc)

    return suggestions
