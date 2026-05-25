from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    College,
    CollegeCompareHistory,
    RoundChecklistProgress,
    RoundDate,
    User,
    UserCollegePreference,
    WorkspaceActivity,
)
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/reporting", tags=["reporting"])


class ReportRequest(BaseModel):
    report_type: str

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, v: str) -> str:
        allowed = {"choice_list", "compare_summary", "round_summary", "financial_overview"}
        if v not in allowed:
            raise ValueError(
                f"Invalid report_type '{v}'. Must be one of: {', '.join(sorted(allowed))}"
            )
        return v


@router.post("/generate")
def generate_report(
    req: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    if req.report_type == "choice_list":
        return _choice_list_report(ws.id, db)
    elif req.report_type == "compare_summary":
        return _compare_summary_report(ws.id, db)
    elif req.report_type == "round_summary":
        return _round_summary_report(ws.id, db)
    elif req.report_type == "financial_overview":
        return _financial_overview_report(ws.id, db)


def _choice_list_report(workspace_id: str, db: Session) -> dict:
    preferences = (
        db.query(UserCollegePreference)
        .filter(UserCollegePreference.workspace_id == workspace_id)
        .order_by(UserCollegePreference.priority.asc())
        .all()
    )

    items = []
    for pref in preferences:
        college = db.query(College).filter(College.code == pref.college_code).first()
        items.append(
            {
                "priority": pref.priority,
                "college_code": pref.college_code,
                "branch_code": pref.branch_code,
                "college_name": college.name if college else None,
                "category": pref.category,
                "notes": pref.notes,
            }
        )

    total_choices = len(items)
    safe_count = sum(1 for i in items if i["category"] == "Safe")
    moderate_count = sum(1 for i in items if i["category"] == "Moderate")
    ambitious_count = sum(1 for i in items if i["category"] == "Ambitious")

    summary = (
        f"Choice list contains {total_choices} selections "
        f"({safe_count} Safe, {moderate_count} Moderate, {ambitious_count} Ambitious)."
    )

    return {
        "report_type": "choice_list",
        "generated_at": datetime.utcnow().isoformat(),
        "data": {"choices": items, "total_count": total_choices},
        "summary": summary,
    }


def _compare_summary_report(workspace_id: str, db: Session) -> dict:
    sessions = (
        db.query(CollegeCompareHistory)
        .filter(CollegeCompareHistory.workspace_id == workspace_id)
        .order_by(CollegeCompareHistory.created_at.desc())
        .limit(10)
        .all()
    )

    items = []
    for s in sessions:
        college_codes = [c.strip() for c in (s.college_codes or "").split(",") if c.strip()]
        college_names = []
        for code in college_codes:
            college = db.query(College).filter(College.code == code).first()
            college_names.append(college.name if college else code)
        items.append(
            {
                "id": s.id,
                "session_name": s.session_name,
                "colleges": college_names,
                "college_codes": college_codes,
                "saved": s.saved,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
        )

    total_sessions = len(items)
    saved_sessions = sum(1 for i in items if i["saved"])

    summary = (
        f"Compare history contains {total_sessions} recent session(s), "
        f"{saved_sessions} of which are saved."
    )

    return {
        "report_type": "compare_summary",
        "generated_at": datetime.utcnow().isoformat(),
        "data": {"sessions": items},
        "summary": summary,
    }


def _round_summary_report(workspace_id: str, db: Session) -> dict:
    now = datetime.utcnow()

    round_dates = db.query(RoundDate).order_by(RoundDate.round_number.asc()).all()
    dates_data = []
    for rd in round_dates:
        dates_data.append(
            {
                "round_number": rd.round_number,
                "choice_start": rd.choice_start.isoformat() if rd.choice_start else None,
                "choice_end": rd.choice_end.isoformat() if rd.choice_end else None,
                "allotment": rd.allotment.isoformat() if rd.allotment else None,
                "confirm_start": rd.confirm_start.isoformat() if rd.confirm_start else None,
                "confirm_end": rd.confirm_end.isoformat() if rd.confirm_end else None,
                "reporting_end": rd.reporting_end.isoformat() if rd.reporting_end else None,
            }
        )

    checklist_progress = (
        db.query(RoundChecklistProgress)
        .filter(RoundChecklistProgress.workspace_id == workspace_id)
        .order_by(RoundChecklistProgress.round_number.asc())
        .all()
    )
    checklist_data = []
    steps_completed = 0
    total_steps = 0
    for cp in checklist_progress:
        steps = {
            "step_1_completed": cp.step_1_completed,
            "step_2_completed": cp.step_2_completed,
            "step_3_completed": cp.step_3_completed,
            "step_4_completed": cp.step_4_completed,
        }
        steps_completed += sum(1 for v in steps.values() if v)
        total_steps += len(steps)
        checklist_data.append(
            {
                "round_number": cp.round_number,
                "steps": steps,
            }
        )

    summary = (
        f"Round summary: {len(dates_data)} round(s) configured, "
        f"{steps_completed}/{total_steps} checklist step(s) completed."
    )

    return {
        "report_type": "round_summary",
        "generated_at": now.isoformat(),
        "data": {
            "round_dates": dates_data,
            "checklist_progress": checklist_data,
        },
        "summary": summary,
    }


def _financial_overview_report(workspace_id: str, db: Session) -> dict:
    preferences = (
        db.query(UserCollegePreference)
        .filter(UserCollegePreference.workspace_id == workspace_id)
        .order_by(UserCollegePreference.priority.asc())
        .all()
    )

    colleges_with_fees = []
    total_annual_fees = 0
    colleges_with_fee_data = 0
    colleges_with_placement_data = 0

    for pref in preferences:
        college = db.query(College).filter(College.code == pref.college_code).first()
        if college:
            entry = {
                "priority": pref.priority,
                "college_code": pref.college_code,
                "college_name": college.name,
                "fee_structure_annual": college.fee_structure_annual,
                "placement_rate_pct": college.placement_rate_pct,
                "avg_package_lpa": college.avg_package_lpa,
            }
            colleges_with_fees.append(entry)
            if college.fee_structure_annual is not None:
                total_annual_fees += college.fee_structure_annual
                colleges_with_fee_data += 1
            if college.placement_rate_pct is not None:
                colleges_with_placement_data += 1

    avg_fee = round(total_annual_fees / colleges_with_fee_data, 2) if colleges_with_fee_data else None

    summary_parts = []
    if colleges_with_fee_data:
        summary_parts.append(f"Average annual fee across {colleges_with_fee_data} choice(s): ₹{avg_fee:,.2f}")
    if colleges_with_placement_data:
        summary_parts.append(
            f"Placement data available for {colleges_with_placement_data} of {len(colleges_with_fees)} choice(s)"
        )
    summary = ". ".join(summary_parts) if summary_parts else "No financial data available for current choices."

    return {
        "report_type": "financial_overview",
        "generated_at": datetime.utcnow().isoformat(),
        "data": {
            "colleges": colleges_with_fees,
            "total_annual_fees": total_annual_fees,
            "average_annual_fee": avg_fee,
        },
        "summary": summary,
    }