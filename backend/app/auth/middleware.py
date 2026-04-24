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
        auth-session-jwt-impl-7264242705534940558
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
            detail="Not authenticated",
          main
        )

    token = auth_header.removeprefix("Bearer ")
    try:
        auth-session-jwt-impl-7264242705534940558
        payload = await verify_session(token)
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
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
        main
        )
