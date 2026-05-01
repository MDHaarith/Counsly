"""Recommendation endpoints based on rank, community, and verified cutoff data."""

from fastapi import APIRouter, Depends

from app.auth.middleware import get_current_user
from app.db.connection import get_db_connection
from app.db.queries import get_session_context
from app.errors import api_error
from app.models import RecommendationsEnvelope
from app.services import recommendation_service

router = APIRouter()


@router.get("", response_model=RecommendationsEnvelope)
async def get_recommendations(user: dict = Depends(get_current_user)) -> RecommendationsEnvelope:
    async with get_db_connection() as conn:
        context = await get_session_context(conn, user["app_user_id"])
        if not context:
            raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
        payload = await recommendation_service.get_student_recommendations(
            conn, str(context["workspace_id"]), bool(context["paid"])
        )
    return RecommendationsEnvelope(**payload)


@router.get("/ping")
async def recommendations_ping() -> dict:
    return {"module": "recommendations", "status": "ok"}
