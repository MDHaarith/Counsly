"""Onboarding endpoints for marks, profile details, eligibility, and rank band."""

from fastapi import APIRouter, Depends

from app.auth.middleware import get_current_user
from app.db.connection import get_db_connection
from app.db.queries import get_student_profile, get_workspace_id
from app.errors import api_error
from app.models import DetailsRequest, MarksRequest, OnboardingResponse, RankBandResponse
from app.services import onboarding_service

router = APIRouter()


@router.post("/marks", response_model=OnboardingResponse)
async def post_marks(payload: MarksRequest, user: dict = Depends(get_current_user)) -> OnboardingResponse:
    async with get_db_connection() as conn:
        workspace_id = await get_workspace_id(conn, user["app_user_id"])
        state = await onboarding_service.save_student_marks(
            conn, workspace_id, payload.maths_mark, payload.physics_mark, payload.chemistry_mark
        )
    return OnboardingResponse(**state)


@router.post("/details", response_model=OnboardingResponse)
async def post_details(payload: DetailsRequest, user: dict = Depends(get_current_user)) -> OnboardingResponse:
    async with get_db_connection() as conn:
        workspace_id = await get_workspace_id(conn, user["app_user_id"])
        try:
            state = await onboarding_service.save_student_details(conn, workspace_id, payload.model_dump())
        except LookupError as exc:
            raise api_error(400, "Marks are required before details", "MARKS_REQUIRED") from exc
    return OnboardingResponse(**state)


@router.get("/rank", response_model=RankBandResponse)
async def get_rank(user: dict = Depends(get_current_user)) -> RankBandResponse:
    async with get_db_connection() as conn:
        workspace_id = await get_workspace_id(conn, user["app_user_id"])
        profile = await get_student_profile(conn, workspace_id)
        if not profile or profile.get("maths_mark") is None:
            raise api_error(400, "Marks are required before rank guidance", "MARKS_REQUIRED")
        
        result = await onboarding_service.get_rank_band(
            conn,
            profile["maths_mark"],
            profile["physics_mark"],
            profile["chemistry_mark"]
        )

    return RankBandResponse(**result)


@router.get("/ping")
async def onboarding_ping() -> dict:
    return {"module": "onboarding", "status": "ok"}
