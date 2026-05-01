"""FastAPI dependency for extracting the current authenticated user."""

import logging

from fastapi import Request

from app.auth.session import verify_session
from app.config import settings
from app.errors import api_error

logger = logging.getLogger("counsly.security.auth")


async def get_current_user(request: Request) -> dict:
    """Extract and return the current user from an httpOnly session cookie."""
    token = request.cookies.get(settings.effective_session_cookie_name)
    if not token:
        logger.warning("session_cookie_missing path=%s", request.url.path)
        raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")

    payload = await verify_session(token)
    return {"app_user_id": payload["sub"]}
