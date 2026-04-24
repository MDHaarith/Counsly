"""Session creation and verification."""

from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week


async def create_session(user_id: str) -> str:
    """Create a new session token for the given user and return it."""
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + expires_delta

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(UTC),
    }

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
        raise ValueError(f"Invalid or expired token: {str(e)}")
