"""Onboarding endpoints for marks, profile details, eligibility, and rank band."""

from fastapi import APIRouter, Depends

from app.auth.middleware import get_current_user
from app.db.connection import get_db_connection
from app.db.queries import fetch_rank_band, get_student_profile, get_workspace_id, save_details, save_marks
from app.errors import api_error
from app.models import DetailsRequest, MarksRequest, OnboardingResponse, RankBandResponse

router = APIRouter()

DISCLAIMER = "These bands are based on historical TNEA allotment data and are not a guarantee."


@router.post("/marks", response_model=OnboardingResponse)
async def post_marks(payload: MarksRequest, user: dict = Depends(get_current_user)) -> OnboardingResponse:
    async with get_db_connection() as conn:
        workspace_id = await get_workspace_id(conn, user["app_user_id"])
        state = await save_marks(conn, workspace_id, payload.maths_mark, payload.physics_mark, payload.chemistry_mark)
    return OnboardingResponse(**state)


@router.post("/details", response_model=OnboardingResponse)
async def post_details(payload: DetailsRequest, user: dict = Depends(get_current_user)) -> OnboardingResponse:
    async with get_db_connection() as conn:
        workspace_id = await get_workspace_id(conn, user["app_user_id"])
        try:
            state = await save_details(conn, workspace_id, payload.model_dump())
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
        band = await fetch_rank_band(
            conn,
            profile["maths_mark"],
            profile["physics_mark"],
            profile["chemistry_mark"],
            profile.get("community_quota"),
        )

    if not band:
        return RankBandResponse(
            maths_mark=profile["maths_mark"],
            physics_mark=profile["physics_mark"],
            chemistry_mark=profile["chemistry_mark"],
            rank_min=None,
            rank_max=None,
            confidence_label=None,
            sample_size=None,
            source_years=[],
            is_abstain=True,
            disclaimer=DISCLAIMER,
        )

    source_years = band.get("source_years") or []
    return RankBandResponse(
        maths_mark=profile["maths_mark"],
        physics_mark=profile["physics_mark"],
        chemistry_mark=profile["chemistry_mark"],
        rank_min=None if band["is_abstain"] else band["rank_min"],
        rank_max=None if band["is_abstain"] else band["rank_max"],
        confidence_label=None if band["is_abstain"] else band["confidence_label"],
        sample_size=band["sample_size"],
        source_years=source_years if isinstance(source_years, list) else [],
        is_abstain=band["is_abstain"],
        disclaimer=DISCLAIMER,
    )


@router.get("/ping")
async def onboarding_ping() -> dict:
    return {"module": "onboarding", "status": "ok"}
