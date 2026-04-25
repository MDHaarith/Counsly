"""Session creation and verification."""

from hashlib import sha256
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt

from app.config import settings
from app.db.connection import get_db_connection
from app.errors import api_error


def _hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


async def create_session(user_id: str) -> str:
    """Create a revocable session token for the given user and return it."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.session_ttl_seconds)
    jti = str(uuid4())
    payload = {
        "sub": user_id,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "typ": "session",
    }
    token = jwt.encode(payload, settings.session_secret, algorithm="HS256")

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_sessions (app_user_id, jti, token_hash, issued_at, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, jti, _hash_token(token), now, expires_at),
            )
        await conn.commit()

    return token


async def verify_session(token: str) -> dict:
    """Verify a session token and return the decoded payload.

    Raises on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise api_error(401, "Session expired or invalid", "INVALID_SESSION") from exc

    if payload.get("typ") != "session" or not payload.get("sub") or not payload.get("jti"):
        raise api_error(401, "Session expired or invalid", "INVALID_SESSION")

    try:
        UUID(str(payload["sub"]))
    except ValueError as exc:
        raise api_error(401, "Session expired or invalid", "INVALID_SESSION") from exc

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 1
                FROM user_sessions
                WHERE app_user_id = %s
                  AND jti = %s
                  AND token_hash = %s
                  AND revoked_at IS NULL
                  AND expires_at > now()
                """,
                (str(payload["sub"]), str(payload["jti"]), _hash_token(token)),
            )
            row = await cur.fetchone()
    if not row:
        raise api_error(401, "Session expired or invalid", "INVALID_SESSION")

    return payload


async def revoke_session(token: str) -> None:
    """Revoke a session token if it is known to the server."""
    try:
        payload = jwt.get_unverified_claims(token)
    except JWTError:
        return
    if not payload.get("sub") or not payload.get("jti"):
        return
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_sessions
                SET revoked_at = now(), updated_at = now()
                WHERE app_user_id = %s
                  AND jti = %s
                  AND revoked_at IS NULL
                """,
                (str(payload["sub"]), str(payload["jti"])),
            )
        await conn.commit()
