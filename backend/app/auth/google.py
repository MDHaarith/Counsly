"""Google OAuth helpers."""

from urllib.parse import urlencode

from app.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


async def get_google_auth_url(redirect_uri: str) -> str:
    """Build the Google OAuth consent URL with the given redirect URI."""
    params = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{params}"
