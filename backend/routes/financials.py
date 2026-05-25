from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from backend.database import get_db
from backend.models import College, User
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/financials", tags=["financials"])

SEATS_PER_COLLEGE = 120


@router.get("/revenue")
def get_revenue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Aggregate fee projection: sum of fee_structure_annual * 120 seats
    across all colleges, with a by_type breakdown.
    """
    row = db.query(
        func.sum(College.fee_structure_annual * SEATS_PER_COLLEGE).label(
            "total_projected"
        )
    ).filter(College.fee_structure_annual.isnot(None)).first()
    total_projected_fee_revenue = round(float(row.total_projected or 0), 2)

    # by_type breakdown
    type_rows = (
        db.query(
            College.type,
            func.sum(College.fee_structure_annual * SEATS_PER_COLLEGE).label(
                "projected_revenue"
            ),
            func.count(College.code).label("college_count"),
        )
        .filter(College.fee_structure_annual.isnot(None))
        .group_by(College.type)
        .order_by(College.type)
        .all()
    )

    by_type = [
        {
            "type": r.type,
            "projected_revenue": round(float(r.projected_revenue or 0), 2),
            "college_count": r.college_count,
        }
        for r in type_rows
    ]

    return {
        "total_projected_fee_revenue": total_projected_fee_revenue,
        "assumed_seats_per_college": SEATS_PER_COLLEGE,
        "by_type": by_type,
    }


@router.get("/expenditure")
def get_expenditure(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return structured expenditure data: avg_annual_fees across colleges
    and estimated spending categories.
    """
    avg_row = db.query(
        func.avg(College.fee_structure_annual).label("avg_fees")
    ).filter(College.fee_structure_annual.isnot(None)).first()
    avg_annual_fees = round(float(avg_row.avg_fees or 0), 2) if avg_row else 0

    # Estimated spending categories based on fee data
    spending_categories = {
        "tuition": {
            "label": "Tuition & Academic",
            "estimated_pct": 60.0,
            "estimated_amount": round(avg_annual_fees * 0.60, 2),
        },
        "hostel": {
            "label": "Hostel & Accommodation",
            "estimated_pct": 25.0,
            "estimated_amount": round(avg_annual_fees * 0.25, 2),
        },
        "transport": {
            "label": "Transport & Miscellaneous",
            "estimated_pct": 15.0,
            "estimated_amount": round(avg_annual_fees * 0.15, 2),
        },
    }

    college_count = (
        db.query(func.count(College.code))
        .filter(College.fee_structure_annual.isnot(None))
        .scalar()
        or 0
    )

    return {
        "avg_annual_fees": avg_annual_fees,
        "colleges_with_fee_data": college_count,
        "spending_categories": spending_categories,
    }


@router.get("/aid")
def get_aid(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return college affordability tiers:
    - affordable: fee < 50000
    - moderate:   fee < 100000
    - premium:    fee >= 100000
    """
    affordable_count = (
        db.query(func.count(College.code))
        .filter(
            College.fee_structure_annual.isnot(None),
            College.fee_structure_annual < 50000,
        )
        .scalar()
        or 0
    )

    moderate_count = (
        db.query(func.count(College.code))
        .filter(
            College.fee_structure_annual.isnot(None),
            College.fee_structure_annual >= 50000,
            College.fee_structure_annual < 100000,
        )
        .scalar()
        or 0
    )

    premium_count = (
        db.query(func.count(College.code))
        .filter(
            College.fee_structure_annual.isnot(None),
            College.fee_structure_annual >= 100000,
        )
        .scalar()
        or 0
    )

    tiers = [
        {
            "tier": "affordable",
            "label": "Affordable (< ₹50,000)",
            "count": affordable_count,
        },
        {
            "tier": "moderate",
            "label": "Moderate (₹50,000 - ₹1,00,000)",
            "count": moderate_count,
        },
        {
            "tier": "premium",
            "label": "Premium (≥ ₹1,00,000)",
            "count": premium_count,
        },
    ]

    return {"tiers": tiers}


@router.get("/metrics")
def get_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return financial metrics:
    - avg_fee by college type
    - avg_placement_rate by fee tier
    - roi_score (placement_rate / fee * 10000)
    """
    # Average fee by college type
    fee_by_type_rows = (
        db.query(
            College.type,
            func.avg(College.fee_structure_annual).label("avg_fee"),
            func.count(College.code).label("count"),
        )
        .filter(College.fee_structure_annual.isnot(None))
        .group_by(College.type)
        .order_by(College.type)
        .all()
    )

    avg_fee_by_type = [
        {
            "type": r.type,
            "avg_fee": round(float(r.avg_fee), 2) if r.avg_fee else None,
            "college_count": r.count,
        }
        for r in fee_by_type_rows
    ]

    # Average placement rate by fee tier
    placement_by_tier_rows = (
        db.query(
            case(
                (College.fee_structure_annual < 50000, "affordable"),
                (College.fee_structure_annual < 100000, "moderate"),
                else_="premium",
            ).label("tier"),
            func.avg(College.placement_rate_pct).label("avg_placement_rate"),
            func.count(College.code).label("count"),
        )
        .filter(
            College.fee_structure_annual.isnot(None),
            College.placement_rate_pct.isnot(None),
        )
        .group_by("tier")
        .order_by("tier")
        .all()
    )

    avg_placement_by_tier = [
        {
            "tier": r.tier,
            "avg_placement_rate": round(float(r.avg_placement_rate), 2)
            if r.avg_placement_rate
            else None,
            "college_count": r.count,
        }
        for r in placement_by_tier_rows
    ]

    # ROI score: placement_rate / fee * 10000
    roi_rows = (
        db.query(
            College.code,
            College.name,
            College.type,
            College.fee_structure_annual,
            College.placement_rate_pct,
        )
        .filter(
            College.fee_structure_annual.isnot(None),
            College.fee_structure_annual > 0,
            College.placement_rate_pct.isnot(None),
        )
        .order_by(College.name)
        .all()
    )

    college_roi = []
    for c in roi_rows:
        roi = round(
            (float(c.placement_rate_pct) / float(c.fee_structure_annual)) * 10000, 4
        )
        college_roi.append(
            {
                "code": c.code,
                "name": c.name,
                "type": c.type,
                "fee_structure_annual": c.fee_structure_annual,
                "placement_rate_pct": c.placement_rate_pct,
                "roi_score": roi,
            }
        )

    # Sort by ROI descending
    college_roi.sort(key=lambda x: x["roi_score"], reverse=True)

    return {
        "avg_fee_by_type": avg_fee_by_type,
        "avg_placement_by_tier": avg_placement_by_tier,
        "college_roi": college_roi,
    }