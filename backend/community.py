from typing import Any

from sqlalchemy.orm import Session

from backend.models import TNEARollNumber, User

VALID_COMMUNITIES = ("OC", "BC", "BCM", "MBC", "SC", "SCA", "ST")


def normalize_community(value: str | None) -> str:
    community = (value or "OC").strip().upper()
    return community if community in VALID_COMMUNITIES else "OC"


def resolve_user_community(community: str | None, current_user: User, db: Session) -> str:
    if community:
        return normalize_community(community)
    if current_user.roll_number_verified and current_user.roll_number:
        roll_rec = db.query(TNEARollNumber).filter(TNEARollNumber.roll_number == current_user.roll_number).first()
        if roll_rec:
            return normalize_community(roll_rec.community)
    return "OC"


def community_seat_payload(seats: Any, community: str | None) -> dict[str, int | str]:
    selected = normalize_community(community)
    key = selected.lower()
    return {
        "community": selected,
        "available": int(getattr(seats, key, 0) or 0),
        "total": int(getattr(seats, "total", 0) or 0),
    }
