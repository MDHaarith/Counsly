from backend.routes.compare import build_structural_explanation
from backend.routes.guidance import MIN_ELIGIBLE_AGGREGATE, build_ai_guidance, compute_aggregate
from backend.routes.rounds import build_round_phase, build_tfc_guidance_message
from backend.schemas import CollegeCompareColumn


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


def test_ai_guidance_falls_back_to_deterministic_strategy_without_provider():
    response = build_ai_guidance(
        marks_total=194.5,
        community="OC",
        district="Chennai",
        preferred_branches=["CS", "IT"],
        provider_enabled=False,
    )

    assert response["ai_available"] is False
    assert "CS, IT" in response["strategy_note"]
    assert "data-only" in response["strategy_note"].lower()


def test_round_phase_and_tfc_guidance_cover_current_year_flow():
    phase = build_round_phase(seconds_remaining=3600, active_phase="confirmation")
    message = build_tfc_guidance_message("Accept_and_Upward", "Chennai")

    assert phase["label"] == "Confirmation window"
    assert phase["urgent"] is True
    assert "TFC" in message
    assert "Chennai" in message
