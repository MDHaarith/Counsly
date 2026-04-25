"""FastAPI dependency for extracting the current authenticated user."""

from fastapi import Request

from app.auth.session import verify_session
from app.config import settings
from app.errors import api_error


async def get_current_user(request: Request) -> dict:
    """Extract and return the current user from an httpOnly session cookie."""
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")

    payload = await verify_session(token)
    return {"app_user_id": payload["sub"]}
