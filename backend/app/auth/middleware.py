"""FastAPI dependency for extracting the current authenticated user."""

from fastapi import Request, HTTPException, status


async def get_current_user(request: Request) -> dict:
    """Extract and return the current user from the session token.

    Expects a Bearer token in the Authorization header.
    Raises 401 if missing or invalid.
    """
    # TODO: extract Bearer token, call verify_session, return user dict
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
