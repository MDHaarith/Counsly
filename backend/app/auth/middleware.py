"""FastAPI dependency for extracting the current authenticated user."""

from fastapi import Request, HTTPException, status
from app.auth.session import verify_session


async def get_current_user(request: Request) -> dict:
    """Extract and return the current user from the session token.

    Expects a Bearer token in the Authorization header.
    Raises 401 if missing or invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = auth_header.removeprefix("Bearer ")
    try:
        user = await verify_session(token)
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
