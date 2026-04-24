"""Session creation and verification."""


async def create_session(user_id: str) -> str:
    """Create a new session token for the given user and return it."""
    # TODO: sign JWT with settings.session_secret
    return ""


async def verify_session(token: str) -> dict:
    """Verify a session token and return the decoded payload.

    Raises on invalid/expired tokens.
    """
    # TODO: decode and validate JWT
    return {}
