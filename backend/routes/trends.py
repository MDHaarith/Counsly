from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from backend.database import get_db
from backend.models import (
    CutoffData, Branch, CommunitySeat, College, User
)
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/community-view")
def get_community_view(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return cutoff data grouped by community per year.
    """
    rows = (
        db.query(
            CutoffData.community,
            CutoffData.year,
            func.avg(CutoffData.cutoff_mark).label("avg_cutoff_mark"),
            func.min(CutoffData.cutoff_mark).label("min_cutoff"),
            func.max(CutoffData.cutoff_mark).label("max_cutoff"),
            func.count(CutoffData.id).label("record_count"),
        )
        .group_by(CutoffData.community, CutoffData.year)
        .order_by(CutoffData.year.desc(), CutoffData.community)
        .all()
    )

    return [
        {
            "community": r.community,
            "year": r.year,
            "avg_cutoff_mark": round(float(r.avg_cutoff_mark), 2)
            if r.avg_cutoff_mark
            else None,
            "min_cutoff": r.min_cutoff,
            "max_cutoff": r.max_cutoff,
            "record_count": r.record_count,
        }
        for r in rows
    ]


@router.get("/credit-hours")
def get_credit_hours(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return branch duration info aggregated by duration_years from Branch model.
    """
    rows = (
        db.query(
            Branch.duration_years,
            func.count(Branch.code).label("branch_count"),
            func.group_concat(Branch.code).label("branch_codes"),
        )
        .group_by(Branch.duration_years)
        .order_by(Branch.duration_years)
        .all()
    )

    result = []
    for r in rows:
        codes = r.branch_codes.split(",") if r.branch_codes else []
        # Get sample branch names
        sample_branches = []
        if codes:
            sample_rows = (
                db.query(Branch.name)
                .filter(Branch.code.in_(codes))
                .order_by(Branch.name)
                .limit(5)
                .all()
            )
            sample_branches = [sr[0] for sr in sample_rows]

        result.append(
            {
                "years": r.duration_years,
                "branch_count": r.branch_count,
                "sample_branches": sample_branches,
            }
        )

    return result


@router.get("/branch-state")
def get_branch_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return branch-state aggregated data: branch_code, branch_name, total_seats,
    college_count (distinct), avg_cutoff.
    """
    # Query CommunitySeat aggregated by branch_code
    seat_rows = (
        db.query(
            CommunitySeat.branch_code,
            func.sum(CommunitySeat.total).label("total_seats"),
            func.count(func.distinct(CommunitySeat.college_code)).label(
                "college_count"
            ),
        )
        .group_by(CommunitySeat.branch_code)
        .subquery()
    )

    # Query CutoffData aggregated by branch_code
    cutoff_rows = (
        db.query(
            CutoffData.branch_code,
            func.avg(CutoffData.cutoff_mark).label("avg_cutoff"),
        )
        .group_by(CutoffData.branch_code)
        .subquery()
    )

    # Join with Branch to get names
    query = (
        db.query(
            Branch.code,
            Branch.name,
            func.coalesce(seat_rows.c.total_seats, 0).label("total_seats"),
            func.coalesce(seat_rows.c.college_count, 0).label("college_count"),
            cutoff_rows.c.avg_cutoff,
        )
        .outerjoin(seat_rows, Branch.code == seat_rows.c.branch_code)
        .outerjoin(cutoff_rows, Branch.code == cutoff_rows.c.branch_code)
        .order_by(Branch.name)
    )

    rows = query.all()

    return [
        {
            "branch_code": r.code,
            "branch_name": r.name,
            "total_seats": r.total_seats,
            "college_count": r.college_count,
            "avg_cutoff": round(float(r.avg_cutoff), 2)
            if r.avg_cutoff
            else None,
        }
        for r in rows
    ]