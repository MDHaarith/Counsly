from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from backend.database import get_db
from backend.models import (
    College, Branch, CommunitySeat, CutoffData, TNEARollNumber,
    TFCLocation, DataFreshness, User
)
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("/overview")
def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_colleges = db.query(func.count(College.code)).scalar() or 0
    total_branches = db.query(func.count(Branch.code)).scalar() or 0
    total_cutoff_records = db.query(func.count(CutoffData.id)).scalar() or 0
    total_students = db.query(func.count(TNEARollNumber.roll_number)).scalar() or 0
    total_tfc_locations = db.query(func.count(TFCLocation.tfc_id)).scalar() or 0

    freshness_rows = db.query(DataFreshness).order_by(DataFreshness.last_refreshed.desc()).all()
    data_freshness = [
        {
            "dataset_key": f.dataset_key,
            "last_refreshed": f.last_refreshed.isoformat() if f.last_refreshed else None,
            "row_count": f.row_count,
            "notes": f.notes,
        }
        for f in freshness_rows
    ]

    return {
        "total_colleges": total_colleges,
        "total_branches": total_branches,
        "total_cutoff_records": total_cutoff_records,
        "total_students": total_students,
        "total_tfc_locations": total_tfc_locations,
        "data_freshness": data_freshness,
    }


@router.get("/fees")
def get_fees(
    district: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(College)
    if district:
        q = q.filter(College.district == district)
    if type:
        q = q.filter(College.type == type)

    colleges = q.order_by(College.name).offset(offset).limit(limit).all()

    return [
        {
            "code": c.code,
            "name": c.name,
            "fee_structure_annual": c.fee_structure_annual,
            "type": c.type,
            "district": c.district,
            "hostel_available": c.hostel_available,
            "transport_available": c.transport_available,
        }
        for c in colleges
    ]


@router.get("/transport")
def get_transport(
    district: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    hostel_available: Optional[bool] = Query(None),
    transport_available: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(College)
    if district:
        q = q.filter(College.district == district)
    if type:
        q = q.filter(College.type == type)
    if hostel_available is not None:
        q = q.filter(College.hostel_available == hostel_available)
    if transport_available is not None:
        q = q.filter(College.transport_available == transport_available)

    colleges = q.order_by(College.name).offset(offset).limit(limit).all()

    return [
        {
            "code": c.code,
            "name": c.name,
            "district": c.district,
            "hostel_available": c.hostel_available,
            "transport_available": c.transport_available,
            "nearest_railway_station": c.nearest_railway_station,
            "nearest_railway_distance_km": c.nearest_railway_distance_km,
            "website": c.website,
        }
        for c in colleges
    ]


@router.get("/district-state")
def get_district_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            College.district,
            func.count(College.code).label("college_count"),
            func.avg(College.fee_structure_annual).label("avg_fees"),
            func.avg(College.placement_rate_pct).label("avg_placement_rate"),
            func.group_concat(College.code).label("college_codes"),
        )
        .group_by(College.district)
        .order_by(College.district)
        .all()
    )

    result = []
    for r in rows:
        # Resolve college names from codes
        codes = r.college_codes.split(",") if r.college_codes else []
        names = []
        if codes:
            name_rows = (
                db.query(College.name)
                .filter(College.code.in_(codes))
                .order_by(College.name)
                .all()
            )
            names = [nr[0] for nr in name_rows]

        result.append(
            {
                "district": r.district,
                "college_count": r.college_count,
                "avg_fees": round(float(r.avg_fees), 2) if r.avg_fees else None,
                "avg_placement_rate": round(float(r.avg_placement_rate), 2)
                if r.avg_placement_rate
                else None,
                "college_list": names,
            }
        )

    return result


@router.get("/master")
def get_master(
    district: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(College)
    if district:
        q = q.filter(College.district == district)
    if type:
        q = q.filter(College.type == type)

    colleges = q.order_by(College.name).offset(offset).limit(limit).all()

    return [
        {
            "code": c.code,
            "name": c.name,
            "district": c.district,
            "type": c.type,
            "address": c.address,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "hostel_available": c.hostel_available,
            "transport_available": c.transport_available,
            "website": c.website,
            "is_autonomous": c.is_autonomous,
            "nba_accredited": c.nba_accredited,
            "nearest_railway_station": c.nearest_railway_station,
            "nearest_railway_distance_km": c.nearest_railway_distance_km,
            "fee_structure_annual": c.fee_structure_annual,
            "placement_rate_pct": c.placement_rate_pct,
            "avg_package_lpa": c.avg_package_lpa,
        }
        for c in colleges
    ]


@router.get("/distribution")
def get_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Group by type
    type_rows = (
        db.query(College.type, func.count(College.code).label("count"))
        .group_by(College.type)
        .order_by(College.type)
        .all()
    )
    colleges_by_type = [{"type": r.type, "count": r.count} for r in type_rows]

    # Group by district
    district_rows = (
        db.query(College.district, func.count(College.code).label("count"))
        .group_by(College.district)
        .order_by(College.district)
        .all()
    )
    colleges_by_district = [
        {"district": r.district, "count": r.count} for r in district_rows
    ]

    return {
        "colleges_by_type": colleges_by_type,
        "colleges_by_district": colleges_by_district,
    }


@router.get("/credit-hours")
def get_credit_hours(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    branches = db.query(Branch).order_by(Branch.name).all()
    return [
        {
            "code": b.code,
            "name": b.name,
            "duration_years": b.duration_years,
        }
        for b in branches
    ]