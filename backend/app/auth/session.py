"""Session creation and verification."""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


async def create_session(user_id: str) -> str:
    """Create a new session token for the given user and return it."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.session_secret, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_session(token: str) -> dict:
    """Verify a session token and return the decoded payload.

    Raises on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError("Invalid or expired token") from e
