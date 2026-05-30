from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import College, TFCLocation, User
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/maps", tags=["maps"])


UNNAMED_OSM_BUS_STOP_NAME = "Unnamed OSM bus stop near campus"


def normalized_bus_stop_name(college: College) -> str | None:
    name = getattr(college, "nearest_bus_stop", None)
    if not name:
        return None

    stop_name = name.strip()
    college_name = (getattr(college, "name", "") or "").strip()
    if stop_name.endswith("Bypass Bus Stop"):
        return None
    if college_name and stop_name == f"{college_name} Bus Stop":
        if getattr(college, "nearest_bus_stop_latitude", None) is None or getattr(college, "nearest_bus_stop_longitude", None) is None:
            return None
        return UNNAMED_OSM_BUS_STOP_NAME
    return stop_name


def build_transit_points(college: College) -> List[dict]:
    specs = [
        (
            "railway_local",
            "railway_local",
            "Local Railway",
            "nearest_railway_station",
            "nearest_railway_station_latitude",
            "nearest_railway_station_longitude",
            "nearest_railway_distance_km",
        ),
        (
            "railway_express",
            "railway_express",
            "Express Railway",
            "nearest_express_station",
            "nearest_express_station_latitude",
            "nearest_express_station_longitude",
            "nearest_express_station_distance_km",
        ),
        (
            "bus_terminus",
            "bus_terminus",
            "Bus Terminus",
            "nearest_bus_station",
            "nearest_bus_station_latitude",
            "nearest_bus_station_longitude",
            "nearest_bus_station_distance_km",
        ),
        (
            "bus_stop",
            "bus_stop",
            "Local Bus Stop",
            "nearest_bus_stop",
            "nearest_bus_stop_latitude",
            "nearest_bus_stop_longitude",
            "nearest_bus_stop_distance_km",
        ),
    ]

    points = []
    for point_id, kind, label, name_attr, lat_attr, lng_attr, distance_attr in specs:
        name = normalized_bus_stop_name(college) if point_id == "bus_stop" else getattr(college, name_attr, None)
        if not name:
            continue

        points.append(
            {
                "id": point_id,
                "kind": kind,
                "label": label,
                "name": name,
                "latitude": getattr(college, lat_attr, None),
                "longitude": getattr(college, lng_attr, None),
                "distance_km": getattr(college, distance_attr, None),
                "available": True,
            }
        )
    return points


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
            "nearest_express_station": c.nearest_express_station,
            "nearest_express_station_latitude": c.nearest_express_station_latitude,
            "nearest_express_station_longitude": c.nearest_express_station_longitude,
            "nearest_express_station_distance_km": c.nearest_express_station_distance_km,
            "nearest_bus_station": c.nearest_bus_station,
            "nearest_bus_station_latitude": c.nearest_bus_station_latitude,
            "nearest_bus_station_longitude": c.nearest_bus_station_longitude,
            "nearest_bus_station_distance_km": c.nearest_bus_station_distance_km,
            "nearest_bus_stop": getattr(c, "nearest_bus_stop", None),
            "nearest_bus_stop_latitude": getattr(c, "nearest_bus_stop_latitude", None),
            "nearest_bus_stop_longitude": getattr(c, "nearest_bus_stop_longitude", None),
            "nearest_bus_stop_distance_km": getattr(c, "nearest_bus_stop_distance_km", None),
            "transit_points": build_transit_points(c),
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