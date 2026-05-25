from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, WorkspaceActivity
from backend.routes.auth import get_current_user
from backend.config import settings
from backend.schemas import AIGuidanceRequest, AIGuidanceResponse, OnboardingRequest, OnboardingResponse

router = APIRouter(prefix="/guidance", tags=["guidance"])

MIN_ELIGIBLE_AGGREGATE = 90.0


def compute_aggregate(maths: int, physics: int, chemistry: int) -> float:
    return float(maths + physics + chemistry)


def build_ai_guidance(
    marks_total: float | None,
    community: str | None,
    district: str | None,
    preferred_branches: list[str],
    provider_enabled: bool,
) -> dict:
    branches = ", ".join(preferred_branches) if preferred_branches else "the selected branch set"
    home = district or "the student district"
    score = marks_total if marks_total is not None else 0
    confidence = "High" if score >= 190 else "Medium" if score >= 170 else "Conservative"

    if provider_enabled:
        return {
            "ai_available": True,
            "strategy_note": (
                f"AI strategy: prioritize {branches} around {home}, keep one ambitious anchor, "
                "two moderate choices, and multiple safe branches before final filing."
            ),
            "confidence_label": confidence,
            "next_action": "Review recommendations and save a choice snapshot.",
        }

    return {
        "ai_available": False,
        "strategy_note": (
            f"Data-only strategy: prioritize {branches} for {community or 'OC'} community near {home}. "
            "Use cutoff history, official rank, and district practicality before trusting any high-risk row."
        ),
        "confidence_label": confidence,
        "next_action": "Open recommendations, compare two targets, then save the choice list.",
    }


@router.post("/onboarding", response_model=OnboardingResponse)
def run_onboarding(
    req: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = compute_aggregate(req.maths, req.physics, req.chemistry)

    if total < MIN_ELIGIBLE_AGGREGATE:
        return OnboardingResponse(
            eligible=False,
            message=(
                "Under the official DTE Tamil Nadu guidelines, candidates with a cumulative "
                "aggregate mark below 90 out of 200 are ineligible for the 2027 counseling flow "
                "in Counsly. Review official notices; recommendations and choices stay locked."
            ),
            onboarding_completed=False,
        )

    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")

    ws.onboarding_step = "completed"
    ws.onboarding_completed = True
    ws.onboarding_completed_at = datetime.utcnow()

    workspace_settings = ws.settings
    if workspace_settings:
        if req.default_district:
            workspace_settings.default_district = req.default_district
        if req.preferred_branches:
            workspace_settings.preferred_branch_defaults = ",".join(req.preferred_branches)

    db.add(
        WorkspaceActivity(
            workspace_id=ws.id,
            event_type="onboarding_completed",
            summary=(
                f"Marks submitted successfully: M/P/C = {req.maths}/{req.physics}/{req.chemistry} "
                f"(Aggregate: {total})."
            ),
            created_at=datetime.utcnow(),
        )
    )

    current_user.roll_number_verified = False

    db.commit()

    return OnboardingResponse(
        eligible=True,
        message="Eligibility confirmed. Continue with branch and district planning.",
        onboarding_completed=True,
    )


@router.post("/ai", response_model=AIGuidanceResponse)
def ai_guidance(
    req: AIGuidanceRequest,
    current_user: User = Depends(get_current_user),
):
    workspace_settings = current_user.workspace.settings if current_user.workspace and current_user.workspace.settings else None
    response = build_ai_guidance(
        marks_total=req.marks_total,
        community=req.community,
        district=req.district or (workspace_settings.default_district if workspace_settings else None),
        preferred_branches=req.preferred_branches,
        provider_enabled=settings.AI_PROVIDER_CONFIGURED,
    )
    return AIGuidanceResponse(**response)
