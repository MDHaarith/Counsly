from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import College, TFCLocation, User
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/maps", tags=["maps"])


@router.get("/colleges")
def get_college_locations(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import json

    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    colleges = (
        db.query(College)
        .filter(College.latitude.isnot(None))
        .order_by(College.name.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for c in colleges:
        boys_hostel_available = c.hostel_available
        girls_hostel_available = c.hostel_available
        
        if c.details_raw:
            try:
                details = json.loads(c.details_raw)
                boys_h = details.get("Hostel_Boys_Permanent_or_Rental")
                girls_h = details.get("Hostel_Girls_Permanent_or_Rental")
                
                if boys_h is not None:
                    boys_hostel_available = bool(
                        boys_h and 
                        boys_h != "-" and 
                        boys_h.strip() != "" and 
                        boys_h.lower() not in ("no", "nil", "none", "null")
                    )
                if girls_h is not None:
                    girls_hostel_available = bool(
                        girls_h and 
                        girls_h != "-" and 
                        girls_h.strip() != "" and 
                        girls_h.lower() not in ("no", "nil", "none", "null")
                    )
            except Exception:
                pass

        results.append({
            "code": c.code,
            "name": c.name,
            "district": c.district,
            "type": c.type,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "hostel_available": c.hostel_available,
            "boys_hostel_available": boys_hostel_available,
            "girls_hostel_available": girls_hostel_available,
            "transport_available": c.transport_available,
            "website": c.website,
            "nearest_railway_station": c.nearest_railway_station,
            "nearest_railway_station_latitude": c.nearest_railway_station_latitude,
            "nearest_railway_station_longitude": c.nearest_railway_station_longitude,
            "nearest_railway_distance_km": c.nearest_railway_distance_km,
            "address": c.address,
        })
    return results


@router.get("/tfc-locations")
def get_tfc_locations(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    tfc_locations = (
        db.query(TFCLocation)
        .filter(TFCLocation.latitude.isnot(None))
        .order_by(TFCLocation.centre_name.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "centre_name": t.centre_name,
            "district": t.district,
            "address": t.address,
            "phone": t.phone,
            "latitude": t.latitude,
            "longitude": t.longitude,
            "google_maps_url": t.google_maps_url,
        }
        for t in tfc_locations
    ]