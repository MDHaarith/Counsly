"""Auth endpoints for direct Google OAuth and session management."""

import asyncio
import hmac
import logging
from secrets import token_urlsafe
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from psycopg.rows import dict_row

from app.auth.google import get_google_auth_url
from app.auth.middleware import get_current_user
from app.auth.session import create_session, revoke_session
from app.config import settings
from app.db.connection import get_db_connection
from app.db.queries import get_session_context
from app.errors import api_error, service_unavailable
from app.models import SessionUser

router = APIRouter()
logger = logging.getLogger("counsly.security.auth")

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://oauth2.googleapis.com/oauth2/v3/userinfo"
OAUTH_STATE_COOKIE = "counsly_oauth_state"


def _request_origin(request: Request) -> str:
    scheme = request.headers.get("x-forwarded-proto", "").split(",")[0].strip() or request.url.scheme
    host = request.headers.get("x-forwarded-host", "").split(",")[0].strip() or request.headers.get("host", "")
    if not host:
        return str(request.base_url).rstrip("/")
    return f"{scheme}://{host}"


def _session_cookie_samesite(request: Request) -> str:
    if not settings.frontend_url:
        return "lax"
    frontend = urlparse(settings.frontend_url)
    backend = urlparse(_request_origin(request))
    return "none" if (frontend.scheme, frontend.netloc) != (backend.scheme, backend.netloc) else "lax"


def _set_session_cookie(request: Request, response: Response, token: str) -> None:
    samesite = _session_cookie_samesite(request)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=samesite == "none" or settings.frontend_url.startswith("https://"),
        samesite=samesite,
    )


def _request_is_https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").split(",")[0].strip() == "https"


def _verify_google_id_token(token: str) -> dict:
    """Verify Google identity token and return its claims."""
    return google_id_token.verify_oauth2_token(token, GoogleAuthRequest(), settings.google_client_id)


@router.get("/google/start")
async def google_start(request: Request) -> RedirectResponse:
    if not settings.google_client_id:
        raise service_unavailable("Google OAuth is not configured", "GOOGLE_OAUTH_NOT_CONFIGURED")
    redirect_uri = str(request.url_for("google_callback"))
    state = token_urlsafe(32)
    google_url = await get_google_auth_url(redirect_uri, state)
    response = RedirectResponse(url=google_url)
    response.set_cookie(
        OAUTH_STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        secure=_request_is_https(request),
        samesite="lax",
    )
    return response


@router.get("/callback")
async def google_callback(request: Request, code: str, state: str) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise service_unavailable("Google OAuth is not configured", "GOOGLE_OAUTH_NOT_CONFIGURED")
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not expected_state or not hmac.compare_digest(expected_state, state):
        logger.warning("oauth_state_invalid path=%s has_cookie=%s", request.url.path, bool(expected_state))
        raise api_error(401, "Google OAuth state verification failed", "GOOGLE_OAUTH_STATE_INVALID")

    redirect_uri = str(request.url_for("google_callback"))
    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        if token_res.status_code >= 400:
            logger.warning("oauth_token_exchange_failed status=%s", token_res.status_code)
            raise api_error(401, "Google OAuth token exchange failed", "GOOGLE_TOKEN_EXCHANGE_FAILED")
        token_payload = token_res.json()
        access_token = token_payload.get("access_token")
        identity_token = token_payload.get("id_token")
        if not access_token:
            logger.warning("oauth_access_token_missing")
            raise api_error(401, "Google access token missing", "GOOGLE_ACCESS_TOKEN_MISSING")
        if not identity_token:
            logger.warning("oauth_id_token_missing")
            raise api_error(401, "Google identity token missing", "GOOGLE_ID_TOKEN_MISSING")
        try:
            verified_claims = await asyncio.to_thread(_verify_google_id_token, identity_token)
        except ValueError as exc:
            logger.warning("oauth_id_token_invalid reason=%s", exc.__class__.__name__)
            raise api_error(401, "Google identity token verification failed", "GOOGLE_ID_TOKEN_INVALID") from exc
        user_res = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_res.status_code >= 400:
            logger.warning("oauth_profile_lookup_failed status=%s", user_res.status_code)
            raise api_error(401, "Google profile lookup failed", "GOOGLE_PROFILE_FAILED")
        profile = user_res.json()

    if not profile.get("sub") or not profile.get("email"):
        logger.warning("oauth_profile_incomplete has_sub=%s has_email=%s", bool(profile.get("sub")), bool(profile.get("email")))
        raise api_error(401, "Google profile is missing required identity fields", "GOOGLE_PROFILE_INCOMPLETE")
    if verified_claims.get("sub") != profile.get("sub") or verified_claims.get("email") != profile.get("email"):
        logger.warning("oauth_identity_mismatch")
        raise api_error(401, "Google identity token does not match profile", "GOOGLE_IDENTITY_MISMATCH")
    if not verified_claims.get("email_verified"):
        logger.warning("oauth_email_not_verified")
        raise api_error(401, "Google email is not verified", "GOOGLE_EMAIL_NOT_VERIFIED")

    auth_user_id = str(uuid4())
    async with get_db_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO auth_identities (auth_user_id, google_id, email, email_verified, display_name, avatar_url, last_login_at)
                VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (google_id) DO UPDATE SET
                    email = EXCLUDED.email,
                    email_verified = EXCLUDED.email_verified,
                    display_name = EXCLUDED.display_name,
                    avatar_url = EXCLUDED.avatar_url,
                    last_login_at = now(),
                    updated_at = now()
                RETURNING id, auth_user_id
                """,
                (auth_user_id, profile["sub"], profile["email"], bool(profile.get("email_verified")), profile.get("name"), profile.get("picture")),
            )
            identity = await cur.fetchone()
            await cur.execute(
                """
                INSERT INTO app_users (auth_identity_id, auth_user_id, current_season_year)
                VALUES (%s, %s, %s)
                ON CONFLICT (auth_identity_id) DO UPDATE SET status = %s, updated_at = now()
                RETURNING id
                """,
                (identity["id"], identity["auth_user_id"], settings.season_year, "active"),
            )
            app_user = await cur.fetchone()
            await cur.execute(
                """
                INSERT INTO workspaces (app_user_id, workspace_kind, display_name, season_year)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (app_user_id) DO UPDATE SET updated_at = now()
                """,
                (app_user["id"], "personal", profile.get("name"), settings.season_year),
            )
        await conn.commit()

    token = await create_session(str(app_user["id"]))
    response = RedirectResponse(url=f"{settings.frontend_url}/dashboard")
    _set_session_cookie(request, response, token)
    response.delete_cookie(OAUTH_STATE_COOKIE)
    return response


@router.get("/session", response_model=SessionUser)
async def get_session(user: dict = Depends(get_current_user)) -> SessionUser:
    async with get_db_connection() as conn:
        context = await get_session_context(conn, user["app_user_id"])
    if not context:
        raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
    return SessionUser(**context)


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, bool]:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await revoke_session(token)
    response.delete_cookie(settings.session_cookie_name)
    return {"ok": True}


@router.get("/ping")
async def auth_ping() -> dict:
    return {"module": "auth", "status": "ok"}
