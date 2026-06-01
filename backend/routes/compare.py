from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.community import resolve_user_community
from backend.database import get_db
from backend.models import Branch, College, CollegeCompareHistory, CutoffData, User, WorkspaceActivity, CollegeBranch
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


def build_multi_structural_explanation(columns: List[CollegeCompareColumn]) -> str:
    # 1. Fees
    valid_fees = [(c.name, c.fee_structure_annual) for c in columns if c.fee_structure_annual]
    fee_clause = ""
    if valid_fees:
        cheapest = min(valid_fees, key=lambda x: x[1])
        fee_clause = f"{cheapest[0]} has the most affordable annual fee (₹{cheapest[1]:,})"

    # 2. Placements
    valid_placements = [(c.name, c.placement_rate_pct) for c in columns if c.placement_rate_pct]
    placement_clause = ""
    if valid_placements:
        best_pl = max(valid_placements, key=lambda x: x[1])
        placement_clause = f"{best_pl[0]} has the highest placement rate ({best_pl[1]}%)"

    # 3. Autonomy
    auto_colleges = [c.name for c in columns if c.is_autonomous]
    autonomy_clause = ""
    if auto_colleges:
        autonomy_clause = f"autonomous regulation is offered at {', '.join(auto_colleges)}"

    # 4. Districts
    districts = {c.district for c in columns if c.district}
    district_clause = f"these options span {len(districts)} districts ({', '.join(districts)})"

    # Combine clauses
    clauses = [fee_clause, placement_clause, autonomy_clause, district_clause]
    clauses = [c for c in clauses if c]

    if not clauses:
        return "The selected options are highly competitive; compare cutoff trends and location practicality to guide your final choice order."

    return "For this comparison: " + "; ".join(clauses) + ". Use these factors as tie-breakers before finalizing your choice order."


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

        if not college or not branch:
            continue

        # Validate college-branch mapping
        cb_link = db.query(CollegeBranch).filter(
            and_(
                CollegeBranch.college_code == c_code,
                CollegeBranch.branch_code == b_code
            )
        ).first()
        if not cb_link:
            raise HTTPException(status_code=400, detail=f"College {c_code} does not offer branch {b_code}")

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

    return CompareResponse(
        colleges=columns,
        explanation=build_multi_structural_explanation(columns),
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
