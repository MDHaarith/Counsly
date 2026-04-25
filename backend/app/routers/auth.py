"""Auth endpoints for direct Google OAuth and session management."""

from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from psycopg.rows import dict_row

from app.auth.google import get_google_auth_url
from app.auth.middleware import get_current_user
from app.auth.session import create_session
from app.config import settings
from app.db.connection import get_db_connection
from app.db.queries import get_session_context
from app.errors import api_error, service_unavailable
from app.models import SessionUser

router = APIRouter()

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://oauth2.googleapis.com/oauth2/v3/userinfo"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.frontend_url.startswith("https://"),
        samesite="lax",
    )


@router.get("/google/start")
async def google_start(request: Request) -> dict[str, str]:
    if not settings.google_client_id:
        raise service_unavailable("Google OAuth is not configured", "GOOGLE_OAUTH_NOT_CONFIGURED")
    redirect_uri = str(request.url_for("google_callback"))
    return {"url": await get_google_auth_url(redirect_uri)}


@router.get("/callback")
async def google_callback(request: Request, code: str) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise service_unavailable("Google OAuth is not configured", "GOOGLE_OAUTH_NOT_CONFIGURED")

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
            raise api_error(401, "Google OAuth token exchange failed", "GOOGLE_TOKEN_EXCHANGE_FAILED")
        access_token = token_res.json().get("access_token")
        user_res = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_res.status_code >= 400:
            raise api_error(401, "Google profile lookup failed", "GOOGLE_PROFILE_FAILED")
        profile = user_res.json()

    if not profile.get("sub") or not profile.get("email"):
        raise api_error(401, "Google profile is missing required identity fields", "GOOGLE_PROFILE_INCOMPLETE")

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
    _set_session_cookie(response, token)
    return response


@router.get("/session", response_model=SessionUser)
async def get_session(user: dict = Depends(get_current_user)) -> SessionUser:
    async with get_db_connection() as conn:
        context = await get_session_context(conn, user["app_user_id"])
    if not context:
        raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
    return SessionUser(**context)


@router.post("/logout")
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(settings.session_cookie_name)
    return {"ok": True}


@router.get("/ping")
async def auth_ping() -> dict:
    return {"module": "auth", "status": "ok"}
