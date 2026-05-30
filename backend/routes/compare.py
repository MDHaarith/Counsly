from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.community import resolve_user_community
from backend.database import get_db
from backend.models import Branch, College, CollegeCompareHistory, CutoffData, User, WorkspaceActivity
from backend.routes.auth import get_current_user
from backend.schemas import (
    CollegeCompareColumn,
    CompareRequest,
    CompareResponse,
    CompareSessionCreate,
    CompareSessionResponse,
)

router = APIRouter(prefix="/compare", tags=["compare"])


def encode_selection(codes: List[str]) -> str:
    return ",".join(code.strip() for code in codes if code and code.strip())


def decode_selection(codes: str | None) -> List[str]:
    return [code.strip() for code in (codes or "").split(",") if code.strip()]


def build_structural_explanation(c1: CollegeCompareColumn, c2: CollegeCompareColumn, diffs: list[str]) -> str:
    if len(diffs) >= 2:
        return (
            f"{c1.name} and {c2.name} differ most on {diffs[0].lower()} and {diffs[1].lower()}, "
            "so use fees, cutoff pressure, and travel practicality as the primary tie-breakers."
        )
    if diffs:
        return (
            f"{c1.name} and {c2.name} differ most on {diffs[0].lower()}, "
            "so use that metric as the primary tie-breaker before locking the choice order."
        )
    return (
        f"{c1.name} and {c2.name} are close on the visible metrics, so review cutoff history, fees, "
        "and location fit before finalizing the order."
    )


@router.post("/", response_model=CompareResponse)
async def compare_colleges(req: CompareRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if len(req.college_codes) < 2:
        raise HTTPException(status_code=400, detail="Must select at least 2 colleges to compare.")
    if len(req.college_codes) > 4:
        raise HTTPException(status_code=400, detail="Can compare at most 4 colleges side-by-side.")
    if not req.branch_codes:
        raise HTTPException(status_code=400, detail="Must select at least 1 branch to compare.")

    user_community = resolve_user_community(req.community, current_user, db)
    columns = []

    for i, c_code in enumerate(req.college_codes):
        b_code = req.branch_codes[i] if i < len(req.branch_codes) else req.branch_codes[0]

        college = db.query(College).filter(College.code == c_code).first()
        branch = db.query(Branch).filter(Branch.code == b_code).first()

        if not college:
            continue

        cutoff_rows = db.query(CutoffData).filter(
            and_(
                CutoffData.college_code == c_code,
                CutoffData.branch_code == b_code,
                CutoffData.community == user_community,
            )
        ).order_by(CutoffData.year.desc()).limit(3).all()
        cutoff = cutoff_rows[0] if cutoff_rows else None

        columns.append(
            CollegeCompareColumn(
                code=c_code,
                name=college.name,
                type=college.type,
                fee_structure_annual=college.fee_structure_annual,
                placement_rate_pct=college.placement_rate_pct,
                avg_package_lpa=college.avg_package_lpa,
                district=college.district,
                is_autonomous=college.is_autonomous,
                nba_accredited=college.nba_accredited,
                hostel_available=college.hostel_available,
                transport_available=college.transport_available,
                nearest_railway_station=college.nearest_railway_station,
                nearest_railway_distance_km=college.nearest_railway_distance_km,
                cutoff_2025=cutoff.cutoff_mark if cutoff else None,
                cutoff_rank_2025=cutoff.cutoff_rank if cutoff else None,
                cutoff_marks_last_three=[row.cutoff_mark for row in cutoff_rows],
            )
        )

    if len(columns) < 2:
        raise HTTPException(status_code=404, detail="Could not retrieve comparative metrics for the specified colleges.")

    differences: list[str] = []
    c1, c2 = columns[0], columns[1]

    if c1.fee_structure_annual and c2.fee_structure_annual:
        diff_fees = abs(c1.fee_structure_annual - c2.fee_structure_annual)
        if diff_fees > 20000:
            cheaper_college = c1.name if c1.fee_structure_annual < c2.fee_structure_annual else c2.name
            differences.append(f"fees difference (₹{diff_fees:,}/year lower at {cheaper_college})")

    if c1.placement_rate_pct and c2.placement_rate_pct:
        diff_place = abs(c1.placement_rate_pct - c2.placement_rate_pct)
        if diff_place > 10.0:
            better_college = c1.name if c1.placement_rate_pct > c2.placement_rate_pct else c2.name
            differences.append(f"placement rate difference ({round(diff_place, 1)}% higher at {better_college})")

    if c1.is_autonomous != c2.is_autonomous:
        auto_college = c1.name if c1.is_autonomous else c2.name
        differences.append(f"autonomy status ({auto_college} offers autonomous regulation)")

    if c1.district != c2.district:
        differences.append(f"district fit ({c1.district} versus {c2.district})")

    if len(differences) < 2:
        differences.append(f"cutoff marks ({c1.cutoff_2025 or 'N/A'} vs {c2.cutoff_2025 or 'N/A'})")
        differences.append(
            f"accreditation status ({c1.name}: {c1.nba_accredited}, {c2.name}: {c2.nba_accredited})"
        )

    return CompareResponse(
        colleges=columns,
        explanation=build_structural_explanation(c1, c2, differences[:2]),
    )


@router.get("/sessions", response_model=List[CompareSessionResponse])
def get_compare_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")

    sessions = db.query(CollegeCompareHistory).filter(
        CollegeCompareHistory.workspace_id == ws.id,
        CollegeCompareHistory.saved.is_(True)
    ).order_by(CollegeCompareHistory.created_at.desc()).limit(12).all()

    return [
        CompareSessionResponse(
            id=session.id,
            session_name=session.session_name or "Saved compare",
            college_codes=decode_selection(session.college_codes),
            branch_codes=decode_selection(session.branch_codes),
            created_at=session.created_at,
            saved=session.saved,
        )
        for session in sessions
    ]


@router.post("/sessions", response_model=CompareSessionResponse)
def save_compare_session(req: CompareSessionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
    if len(req.college_codes) < 2 or len(req.college_codes) > 4:
        raise HTTPException(status_code=400, detail="Saved compare sessions require 2 to 4 colleges.")

    session = CollegeCompareHistory(
        workspace_id=ws.id,
        session_name=req.session_name.strip() or "Saved compare",
        college_codes=encode_selection(req.college_codes),
        branch_codes=encode_selection(req.branch_codes),
        saved=True,
    )
    db.add(session)
    db.flush()
    db.add(WorkspaceActivity(
        workspace_id=ws.id,
        event_type="compare_session_saved",
        entity_type="college_compare_history",
        entity_id=str(session.id),
        summary=f"Saved compare session '{session.session_name}' with {len(req.college_codes)} colleges.",
    ))
    db.commit()
    db.refresh(session)

    return CompareSessionResponse(
        id=session.id,
        session_name=session.session_name,
        college_codes=decode_selection(session.college_codes),
        branch_codes=decode_selection(session.branch_codes),
        created_at=session.created_at,
        saved=session.saved,
    )
