from types import SimpleNamespace

from backend.routes.maps import build_transit_points


def test_build_transit_points_groups_available_rail_and_bus_access():
    college = SimpleNamespace(
        nearest_railway_station="Coimbatore Junction",
        nearest_railway_station_latitude=11.0018,
        nearest_railway_station_longitude=76.9661,
        nearest_railway_distance_km=4.4,
        nearest_express_station="Tiruppur",
        nearest_express_station_latitude=11.1085,
        nearest_express_station_longitude=77.3411,
        nearest_express_station_distance_km=42.0,
        nearest_bus_station="Gandhipuram Town Bus Stand",
        nearest_bus_station_latitude=11.0167,
        nearest_bus_station_longitude=76.9674,
        nearest_bus_station_distance_km=5.1,
        nearest_bus_stop="Peelamedu Bus Stop",
        nearest_bus_stop_latitude=11.033,
        nearest_bus_stop_longitude=77.028,
        nearest_bus_stop_distance_km=1.8,
    )

    points = build_transit_points(college)

    assert [point["id"] for point in points] == [
        "railway_local",
        "railway_express",
        "bus_terminus",
        "bus_stop",
    ]
    assert points[0] == {
        "id": "railway_local",
        "kind": "railway_local",
        "label": "Local Railway",
        "name": "Coimbatore Junction",
        "latitude": 11.0018,
        "longitude": 76.9661,
        "distance_km": 4.4,
        "available": True,
    }
    assert points[3]["label"] == "Local Bus Stop"


def test_build_transit_points_omits_missing_names():
    college = SimpleNamespace(
        nearest_railway_station="",
        nearest_railway_station_latitude=None,
        nearest_railway_station_longitude=None,
        nearest_railway_distance_km=None,
        nearest_express_station=None,
        nearest_express_station_latitude=None,
        nearest_express_station_longitude=None,
        nearest_express_station_distance_km=None,
        nearest_bus_station="Central Bus Stand",
        nearest_bus_station_latitude=None,
        nearest_bus_station_longitude=None,
        nearest_bus_station_distance_km=None,
        nearest_bus_stop=None,
        nearest_bus_stop_latitude=None,
        nearest_bus_stop_longitude=None,
        nearest_bus_stop_distance_km=None,
    )

    points = build_transit_points(college)

    assert points == [
        {
            "id": "bus_terminus",
            "kind": "bus_terminus",
            "label": "Bus Terminus",
            "name": "Central Bus Stand",
            "latitude": None,
            "longitude": None,
            "distance_km": None,
            "available": True,
        }
    ]


def test_build_transit_points_omits_synthetic_bus_stop_names():
    college = SimpleNamespace(
        name="Sample Engineering College",
        nearest_railway_station=None,
        nearest_railway_station_latitude=None,
        nearest_railway_station_longitude=None,
        nearest_railway_distance_km=None,
        nearest_express_station=None,
        nearest_express_station_latitude=None,
        nearest_express_station_longitude=None,
        nearest_express_station_distance_km=None,
        nearest_bus_station="Central Bus Stand",
        nearest_bus_station_latitude=11.1,
        nearest_bus_station_longitude=77.1,
        nearest_bus_station_distance_km=4.0,
        nearest_bus_stop="Sample Engineering College Bypass Bus Stop",
        nearest_bus_stop_latitude=11.004,
        nearest_bus_stop_longitude=77.004,
        nearest_bus_stop_distance_km=0.65,
    )

    points = build_transit_points(college)

    assert [point["id"] for point in points] == ["bus_terminus"]


def test_build_transit_points_relabels_unnamed_osm_bus_stop_without_inventing_college_name():
    college = SimpleNamespace(
        name="Sample Engineering College",
        nearest_railway_station=None,
        nearest_railway_station_latitude=None,
        nearest_railway_station_longitude=None,
        nearest_railway_distance_km=None,
        nearest_express_station=None,
        nearest_express_station_latitude=None,
        nearest_express_station_longitude=None,
        nearest_express_station_distance_km=None,
        nearest_bus_station=None,
        nearest_bus_station_latitude=None,
        nearest_bus_station_longitude=None,
        nearest_bus_station_distance_km=None,
        nearest_bus_stop="Sample Engineering College Bus Stop",
        nearest_bus_stop_latitude=11.004,
        nearest_bus_stop_longitude=77.004,
        nearest_bus_stop_distance_km=0.65,
    )

    points = build_transit_points(college)

    assert points == [
        {
            "id": "bus_stop",
            "kind": "bus_stop",
            "label": "Local Bus Stop",
            "name": "Unnamed OSM bus stop near campus",
            "latitude": 11.004,
            "longitude": 77.004,
            "distance_km": 0.65,
            "available": True,
        }
    ]
