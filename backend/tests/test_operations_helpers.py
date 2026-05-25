from backend.routes.admin import build_admin_update_summary
from backend.routes.compare import build_ai_compare_reasoning
from backend.routes.scraping import build_scraping_job_status


def test_ai_compare_reasoning_has_deterministic_fallback():
    reasoning = build_ai_compare_reasoning(
        colleges=["College of Engineering, Guindy", "PSG College of Technology"],
        metrics=["fees", "cutoff pressure"],
        provider_enabled=False,
    )

    assert reasoning["ai_available"] is False
    assert "No AI reasoning" in reasoning["headline"]
    assert "fees" in reasoning["reasoning"]


def test_admin_update_summary_keeps_manual_updates_auditable():
    summary = build_admin_update_summary(
        dataset="cutoff_data",
        source_url="https://example.edu/cutoffs.pdf",
        rows_inserted=10,
        rows_updated=2,
        rows_rejected=1,
    )

    assert summary["dataset"] == "cutoff_data"
    assert summary["status"] == "needs_review"
    assert "10 inserted" in summary["summary"]
    assert "1 rejected" in summary["summary"]


def test_scraping_status_surfaces_freshness_without_news():
    status = build_scraping_job_status(
        dataset="seat_matrix",
        source_url="https://example.edu/seats.pdf",
        status="success",
        row_count=420,
    )

    assert status["dataset"] == "seat_matrix"
    assert status["job_type"] == "real_time_scraping"
    assert status["row_count"] == 420
    assert "news" not in status
