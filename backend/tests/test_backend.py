from types import SimpleNamespace

from backend.routes.compare import build_structural_explanation
from backend.routes.explore import community_seat_payload
from backend.routes.guidance import MIN_ELIGIBLE_AGGREGATE, compute_aggregate
from backend.schemas import CollegeCompareColumn, CollegeSearchQuery, CompareRequest


def make_column(name: str) -> CollegeCompareColumn:
    return CollegeCompareColumn(
        code=name[:4].upper(),
        name=name,
        type="Aided",
        fee_structure_annual=50000,
        placement_rate_pct=90.0,
        avg_package_lpa=6.0,
        district="Chennai",
        is_autonomous=True,
        nba_accredited=True,
        hostel_available=True,
        transport_available=True,
        nearest_railway_station="Central",
        nearest_railway_distance_km=5.0,
        cutoff_2025=190.0,
        cutoff_rank_2025=5000,
        cutoff_marks_last_three=[188.0, 189.0, 190.0],
    )


def test_aggregate_gate_block():
    assert compute_aggregate(40, 20, 10) < MIN_ELIGIBLE_AGGREGATE


def test_aggregate_gate_matches_frontend_threshold():
    assert MIN_ELIGIBLE_AGGREGATE == 78.0
    assert compute_aggregate(40, 20, 18) >= MIN_ELIGIBLE_AGGREGATE


def test_search_and_compare_requests_preserve_community():
    search_req = CollegeSearchQuery(branch_code="CS", community="bc")
    compare_req = CompareRequest(college_codes=["1", "2006"], branch_codes=["CS"], community="sc")

    assert search_req.community == "BC"
    assert compare_req.community == "SC"


def test_community_seat_payload_hides_other_communities():
    seats = SimpleNamespace(oc=11, bc=22, bcm=3, mbc=18, sc=12, sca=2, st=1, total=69)

    payload = community_seat_payload(seats, "bc")

    assert payload == {"community": "BC", "available": 22, "total": 69}
    assert "oc" not in payload
    assert "sc" not in payload


def test_structural_explanation_uses_top_two_differences():
    c1 = make_column("College One")
    c2 = make_column("College Two")

    explanation = build_structural_explanation(
        c1,
        c2,
        [
            "fees difference (₹25,000/year lower at College One)",
            "district fit (Chennai versus Coimbatore)",
        ],
    )

    assert "fees difference" in explanation
    assert "district fit" in explanation
    assert "tie-breakers" in explanation

