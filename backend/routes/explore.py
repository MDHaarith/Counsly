from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Dict, Any, Optional
from backend.community import community_seat_payload, resolve_user_community
from backend.database import get_db
from backend.models import User, College, Branch, CollegeBranch, CommunitySeat, CutoffData, TFCLocation
from backend.schemas import CollegeSearchQuery, CollegeCompactResponse, CollegeDetailResponse, CutoffTrend
from backend.routes.auth import get_current_user
from backend.routes.maps import normalized_bus_stop_name

router = APIRouter(prefix="/explore", tags=["explore"])

@router.post("/search", response_model=List[CollegeCompactResponse])
def search_colleges(req: CollegeSearchQuery, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = current_user.workspace
    home_district = None
    if ws and ws.settings:
        home_district = ws.settings.default_district
    user_community = resolve_user_community(req.community, current_user, db)
        
    query = db.query(College)
    
    # 1. Apply filters
    if req.district:
        query = query.filter(College.district == req.district)
    if req.type:
        query = query.filter(College.type == req.type)
    if req.is_autonomous is not None:
        query = query.filter(College.is_autonomous == req.is_autonomous)
    if req.min_placement_rate is not None:
        query = query.filter(College.placement_rate_pct >= req.min_placement_rate)
    if req.search:
        search_pat = f"%{req.search}%"
        query = query.filter(
            or_(
                College.name.like(search_pat),
                College.code.like(search_pat),
                College.district.like(search_pat)
            )
        )
        
    if req.branch_code:
        # Join with college_branches
        query = query.join(CollegeBranch, CollegeBranch.college_code == College.code).filter(
            CollegeBranch.branch_code == req.branch_code
        )
        
    colleges = query.offset(req.offset).limit(req.limit).all()
    
    response = []
    for c in colleges:
        # Compute dynamic Fit Score (0-100)
        fit_score = 50.0
        
        # 1. District preference (home district matches)
        if home_district and c.district.lower() == home_district.lower():
            fit_score += 15.0
            
        # 2. Autonomous benefits
        if c.is_autonomous:
            fit_score += 10.0
            
        # 3. Accreditation
        if c.nba_accredited:
            fit_score += 10.0
            
        # 4. Placements premium
        if c.placement_rate_pct:
            fit_score += (c.placement_rate_pct / 10.0)  # max +10 points
            
        if c.avg_package_lpa:
            fit_score += min(15.0, c.avg_package_lpa * 1.5)  # max +15 points
            
        fit_score = min(100.0, max(0.0, fit_score))
        
        branch_code = req.branch_code
        college_branch = None
        if branch_code:
            college_branch = db.query(CollegeBranch).filter(
                and_(
                    CollegeBranch.college_code == c.code,
                    CollegeBranch.branch_code == branch_code,
                )
            ).first()
        else:
            college_branch = db.query(CollegeBranch).filter(
                CollegeBranch.college_code == c.code
            ).order_by(CollegeBranch.branch_code.asc()).first()
            branch_code = college_branch.branch_code if college_branch else None

        branch = db.query(Branch).filter(Branch.code == branch_code).first() if branch_code else None
        cutoff = None
        seat_count = None
        if branch_code:
            cutoff = db.query(CutoffData).filter(
                and_(
                    CutoffData.college_code == c.code,
                    CutoffData.branch_code == branch_code,
                    CutoffData.community == user_community,
                )
            ).order_by(CutoffData.year.desc()).first()
            seats = db.query(CommunitySeat).filter(
                and_(
                    CommunitySeat.college_code == c.code,
                    CommunitySeat.branch_code == branch_code,
                )
            ).first()
            if seats:
                seat_count = community_seat_payload(seats, user_community)["available"]

        response.append(CollegeCompactResponse(
            code=c.code,
            name=c.name,
            district=c.district,
            type=c.type,
            is_autonomous=c.is_autonomous,
            fee_structure_annual=c.fee_structure_annual,
            placement_rate_pct=c.placement_rate_pct,
            fit_score=round(fit_score, 1),
            branch_code=branch_code,
            branch_name=branch.name if branch else None,
            cutoff_mark_2025=cutoff.cutoff_mark if cutoff else None,
            cutoff_rank_2025=cutoff.cutoff_rank if cutoff else None,
            seats=seat_count,
        ))
        
    # Sort response by fit_score descending
    response.sort(key=lambda x: x.fit_score, reverse=True)
    return response

@router.get("/{college_code}", response_model=CollegeDetailResponse)
def get_college_details(
    college_code: str,
    community: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    college = db.query(College).filter(College.code == college_code).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    user_community = resolve_user_community(community, current_user, db)
        
    # Retrieve branches mapping
    cb_mappings = db.query(CollegeBranch).filter(CollegeBranch.college_code == college_code).all()
    
    branches_list = []
    for cb in cb_mappings:
        branch = db.query(Branch).filter(Branch.code == cb.branch_code).first()
        seats = db.query(CommunitySeat).filter(
            and_(
                CommunitySeat.college_code == college_code,
                CommunitySeat.branch_code == cb.branch_code
            )
        ).first()
        
        if seats:
            seats_dict = community_seat_payload(seats, user_community)
        else:
            seats_dict = {
                "community": user_community,
                "available": 0,
                "total": cb.approved_intake or 0,
            }
            
        branches_list.append({
            "code": cb.branch_code,
            "name": branch.name if branch else "Unknown Branch",
            "duration_years": branch.duration_years if branch else 4,
            "approved_intake": cb.approved_intake,
            "year_starting": cb.year_starting,
            "nba_accredited": cb.nba_accredited,
            "seats": seats_dict
        })
        
    # Retrieve cutoff trends filtered by the resolved community
    cutoffs = db.query(CutoffData).filter(
        and_(
            CutoffData.college_code == college_code,
            CutoffData.community == user_community
        )
    ).order_by(CutoffData.year.desc()).all()
    
    trends_dict: Dict[str, List[CutoffTrend]] = {}
    for cut in cutoffs:
        if cut.branch_code not in trends_dict:
            trends_dict[cut.branch_code] = []
            
        # Include community cutoffs based on user community preference
        trends_dict[cut.branch_code].append(CutoffTrend(
            year=cut.year,
            cutoff_mark=cut.cutoff_mark,
            cutoff_rank=cut.cutoff_rank,
            seats_allotted=cut.seats_allotted
        ))
        
    nearest_tfc = None
    home_district = current_user.workspace.settings.default_district if current_user.workspace and current_user.workspace.settings else college.district
    tfc = db.query(TFCLocation).filter(TFCLocation.district == home_district).first() or db.query(TFCLocation).first()
    if tfc:
        nearest_tfc = {
            "centre_name": tfc.centre_name,
            "district": tfc.district,
            "address": tfc.address,
            "phone": tfc.phone,
        }
            
    bus_stop_name = normalized_bus_stop_name(college)

    return CollegeDetailResponse(
        code=college.code,
        name=college.name,
        district=college.district,
        type=college.type,
        address=college.address,
        latitude=college.latitude,
        longitude=college.longitude,
        hostel_available=college.hostel_available,
        transport_available=college.transport_available,
        website=college.website,
        is_autonomous=college.is_autonomous,
        nba_accredited=college.nba_accredited,
        fee_structure_annual=college.fee_structure_annual,
        placement_rate_pct=college.placement_rate_pct,
        avg_package_lpa=college.avg_package_lpa,
        nearest_railway_station=college.nearest_railway_station,
        nearest_railway_station_latitude=college.nearest_railway_station_latitude,
        nearest_railway_station_longitude=college.nearest_railway_station_longitude,
        nearest_railway_distance_km=college.nearest_railway_distance_km,
        nearest_express_station=college.nearest_express_station,
        nearest_express_station_latitude=college.nearest_express_station_latitude,
        nearest_express_station_longitude=college.nearest_express_station_longitude,
        nearest_express_station_distance_km=college.nearest_express_station_distance_km,
        nearest_bus_station=college.nearest_bus_station,
        nearest_bus_station_latitude=college.nearest_bus_station_latitude,
        nearest_bus_station_longitude=college.nearest_bus_station_longitude,
        nearest_bus_station_distance_km=college.nearest_bus_station_distance_km,
        nearest_bus_stop=bus_stop_name,
        nearest_bus_stop_latitude=college.nearest_bus_stop_latitude if bus_stop_name else None,
        nearest_bus_stop_longitude=college.nearest_bus_stop_longitude if bus_stop_name else None,
        nearest_bus_stop_distance_km=college.nearest_bus_stop_distance_km if bus_stop_name else None,
        nearest_tfc=nearest_tfc,
        branches=branches_list,
        cutoff_trends=trends_dict,
        details_raw=college.details_raw
    )
