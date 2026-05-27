from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, WorkspaceActivity
from backend.routes.auth import get_current_user
from backend.schemas import OnboardingRequest, OnboardingResponse
from backend.routes.rate_limiter import rate_limit

router = APIRouter(prefix="/guidance", tags=["guidance"])

MIN_ELIGIBLE_AGGREGATE = 90.0


def compute_aggregate(maths: int, physics: int, chemistry: int) -> float:
    return float(maths + physics + chemistry)


@router.post("/onboarding", response_model=OnboardingResponse, dependencies=[Depends(rate_limit(10, 60))])
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
    ws.onboarding_completed_at = datetime.now(timezone.utc)

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
            created_at=datetime.now(timezone.utc),
        )
    )

    current_user.roll_number_verified = False

    db.commit()

    return OnboardingResponse(
        eligible=True,
        message="Eligibility confirmed. Continue with branch and district planning.",
        onboarding_completed=True,
    )
