"""Profile endpoints for student profile retrieval and updates."""

from fastapi import APIRouter, Depends

from app.auth.middleware import get_current_user
from app.db.connection import get_db_connection
from app.db.queries import fetch_profile, get_session_context, update_profile
from app.errors import api_error
from app.models import DetailsRequest, ProfileResponse

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)) -> ProfileResponse:
    async with get_db_connection() as conn:
        context = await get_session_context(conn, user["app_user_id"])
        if not context:
            raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
        payload = await fetch_profile(conn, str(context["workspace_id"]), bool(context["paid"]))
    return ProfileResponse(**payload)


@router.patch("", response_model=ProfileResponse)
async def patch_profile(payload: DetailsRequest, user: dict = Depends(get_current_user)) -> ProfileResponse:
    async with get_db_connection() as conn:
        context = await get_session_context(conn, user["app_user_id"])
        if not context:
            raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
        result = await update_profile(conn, str(context["workspace_id"]), payload.model_dump())
        result["paid"] = bool(context["paid"])
    return ProfileResponse(**result)


@router.get("/ping")
async def profile_ping() -> dict:
    return {"module": "profile", "status": "ok"}
