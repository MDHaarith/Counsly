from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import RoundChecklistProgress, RoundDate, TFCLocation, User, WorkspaceActivity
from backend.routes.auth import get_current_user
from backend.schemas import DecisionConfirmationRequest, DecisionConfirmationResponse, RoundStatusResponse

router = APIRouter(prefix="/rounds", tags=["rounds"])


def build_round_phase(seconds_remaining: int, active_phase: str) -> dict:
    labels = {
        "choice_filling": "Choice filling window",
        "allotment_pending": "Allotment pending",
        "confirmation": "Confirmation window",
        "reporting": "Reporting window",
        "inactive": "Inactive",
    }
    return {
        "label": labels.get(active_phase, "Inactive"),
        "urgent": active_phase in {"choice_filling", "confirmation", "reporting"} and seconds_remaining <= 86_400,
        "seconds_remaining": max(0, seconds_remaining),
    }


def build_tfc_guidance_message(decision_type: str, district: str) -> str:
    if decision_type in {"Accept_and_Upward", "Decline_and_Upward"}:
        return (
            f"TFC guidance for {district}: this upward decision requires fee/payment readiness, "
            "certificate verification, and deadline tracking before the confirmation window closes."
        )
    if decision_type == "Accept_and_Join":
        return "Report to the allotted college with the provisional allotment letter before reporting closes."
    return "This decision exits or releases the current allotment path; confirm only after checking official consequences."


def _default_round_dates(now: datetime) -> RoundDate:
    return RoundDate(
        round_number=1,
        choice_start=now - timedelta(days=1),
        choice_end=now + timedelta(hours=20),
        allotment=now + timedelta(days=1),
        confirm_start=now + timedelta(days=1, hours=3),
        confirm_end=now + timedelta(days=3),
        reporting_end=now + timedelta(days=7),
    )


def _active_phase(dates: RoundDate, now: datetime) -> tuple[str, int]:
    if dates.choice_start and dates.choice_end and dates.choice_start <= now <= dates.choice_end:
        return "choice_filling", int((dates.choice_end - now).total_seconds())
    if dates.choice_end and dates.confirm_start and dates.choice_end < now <= dates.confirm_start:
        return "allotment_pending", int((dates.confirm_start - now).total_seconds())
    if dates.confirm_start and dates.confirm_end and dates.confirm_start <= now <= dates.confirm_end:
        return "confirmation", int((dates.confirm_end - now).total_seconds())
    if dates.confirm_end and dates.reporting_end and dates.confirm_end < now <= dates.reporting_end:
        return "reporting", int((dates.reporting_end - now).total_seconds())
    return "inactive", 0


@router.get("/status", response_model=RoundStatusResponse)
def get_round_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")

    now = datetime.utcnow()
    dates = db.query(RoundDate).filter(RoundDate.round_number == 1).first() or _default_round_dates(now)
    active_phase, seconds_remaining = _active_phase(dates, now)

    checklist = db.query(RoundChecklistProgress).filter(
        and_(RoundChecklistProgress.workspace_id == ws.id, RoundChecklistProgress.round_number == 1)
    ).first()
    if not checklist:
        checklist = RoundChecklistProgress(workspace_id=ws.id, round_number=1)
        db.add(checklist)
        db.commit()
        db.refresh(checklist)

    checklist_dict = {
        "choice_list_snapshot": checklist.step_1_completed,
        "official_links_checked": checklist.step_2_completed,
        "tfc_plan_ready": checklist.step_3_completed,
        "decision_confirmed": checklist.step_4_completed,
    }

    return RoundStatusResponse(
        round_number=1,
        choice_start=dates.choice_start,
        choice_end=dates.choice_end,
        allotment=dates.allotment,
        confirm_start=dates.confirm_start,
        confirm_end=dates.confirm_end,
        reporting_end=dates.reporting_end,
        active_phase=active_phase,
        seconds_remaining=seconds_remaining,
        phase=build_round_phase(seconds_remaining, active_phase),
        checklist=checklist_dict,
    )


@router.post("/confirm", response_model=DecisionConfirmationResponse)
def confirm_round_decision(req: DecisionConfirmationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")

    checklist = db.query(RoundChecklistProgress).filter(
        and_(RoundChecklistProgress.workspace_id == ws.id, RoundChecklistProgress.round_number == 1)
    ).first()
    if not checklist:
        checklist = RoundChecklistProgress(workspace_id=ws.id, round_number=1)
        db.add(checklist)

    checklist.step_4_completed = True
    district = ws.settings.default_district if ws.settings and ws.settings.default_district else "Chennai"
    tfc_required = req.decision_type in {"Accept_and_Upward", "Decline_and_Upward"}
    nearest_tfc = None
    if tfc_required:
        tfc = db.query(TFCLocation).filter(TFCLocation.district == district).first() or db.query(TFCLocation).first()
        if tfc:
            nearest_tfc = {
                "centre_name": tfc.centre_name,
                "district": tfc.district,
                "address": tfc.address,
                "phone": tfc.phone,
                "google_maps_url": tfc.google_maps_url,
            }

    message = build_tfc_guidance_message(req.decision_type, district)
    db.add(WorkspaceActivity(
        workspace_id=ws.id,
        event_type="round_decision_confirmed",
        summary=f"Confirmed round decision {req.decision_type}. TFC required: {tfc_required}.",
    ))
    db.commit()
    return DecisionConfirmationResponse(success=True, message=message, tfc_required=tfc_required, nearest_tfc=nearest_tfc)
