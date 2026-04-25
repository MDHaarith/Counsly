"""Session creation and verification."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.config import settings
from app.errors import api_error


async def create_session(user_id: str) -> str:
    """Create a new session token for the given user and return it."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.session_ttl_seconds)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "typ": "session",
    }
    return jwt.encode(payload, settings.session_secret, algorithm="HS256")


async def verify_session(token: str) -> dict:
    """Verify a session token and return the decoded payload.

    Raises on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise api_error(401, "Session expired or invalid", "INVALID_SESSION") from exc

    if payload.get("typ") != "session" or not payload.get("sub"):
        raise api_error(401, "Session expired or invalid", "INVALID_SESSION")

    try:
        UUID(str(payload["sub"]))
    except ValueError as exc:
        raise api_error(401, "Session expired or invalid", "INVALID_SESSION") from exc

    return payload
