"""
Format and write ranking outputs.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import RANKINGS_DIR, WEIGHTS

logger = logging.getLogger(__name__)


def generate_output(
    overall: pd.DataFrame,
    community_rankings: dict[str, pd.DataFrame],
    branch_rankings: dict[str, pd.DataFrame],
    district_rankings: dict[str, pd.DataFrame],
    college_info: pd.DataFrame,
    scraped_data: dict[str, dict] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Write the overall ranking JSON and a flat CSV of the overall ranking."""
    out = output_path or RANKINGS_DIR / "college_rankings.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    lookup = _build_college_lookup(college_info)
    result = {
        "metadata": {
            "algorithm_version": "4.3",
            "generation_date": datetime.now().isoformat(),
            "total_colleges_ranked": int(len(overall)),
            "dimension_weights": WEIGHTS,
            "methodology": {
                "selectivity": "Recency-weighted round-1 admitted-rank percentiles across 2023-2025",
                "academic_quality": "Recency-weighted aggregate-mark percentiles across 2023-2025 round-1 admissions",
                "branch_strength": "Branch-wise peer comparison using branch closing-rank percentiles where peer counts are sufficient",
                "institutional_quality": "NBA accreditation depth, placement record, and autonomy as a capped support signal",
                "web_reputation": "NAAC, NIRF, placement, CTC, faculty, and research signals extracted from college websites",
                "trend": "Improvement or decline in selectivity from 2020-2025",
            },
        },
        "rankings": {
            "overall": _format_ranking(overall, lookup, scraped_data or {}),
            "by_community": {
                community: _format_ranking(df, lookup, scraped_data or {})
                for community, df in community_rankings.items()
            },
            "by_branch": {
                branch: _format_ranking(df, lookup, scraped_data or {})
                for branch, df in branch_rankings.items()
            },
            "by_district": {
                district: _format_ranking(df, lookup, scraped_data or {})
                for district, df in district_rankings.items()
            },
        },
    }

    with out.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False, default=str)

    flat_csv = out.with_suffix(".csv")
    _write_overall_csv(flat_csv, overall, lookup)

    logger.info("Ranking JSON written to %s", out)
    logger.info("Ranking CSV written to %s", flat_csv)
    return out


def _build_college_lookup(college_info: pd.DataFrame) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for _, row in college_info.iterrows():
        code = str(row.get("college_code", "")).strip()
        if not code:
            continue
        lookup[code] = {
            "college_name": row.get("college_name", ""),
            "district": row.get("district_clean", ""),
            "website": row.get("website", ""),
            "approved_intake_total": row.get("approved_intake_total", ""),
            "num_branches": row.get("num_branches", ""),
            "placement_pct": row.get("placement_pct", ""),
            "nba_accredited_ratio": row.get("nba_accredited_ratio", ""),
            "is_autonomous": bool(row.get("is_autonomous", False)),
        }
    return lookup


def _format_ranking(
    df: pd.DataFrame,
    lookup: dict[str, dict],
    scraped_data: dict[str, dict],
) -> list[dict]:
    entries: list[dict] = []
    for _, row in df.iterrows():
        code = str(row.get("college_code", ""))
        info = lookup.get(code, {})
        scraped = scraped_data.get(code, {})
        entry = {
            "rank": int(row.get("rank", 0)),
            "college_code": code,
            "college_name": info.get("college_name", ""),
            "district": info.get("district", ""),
            "composite_score": round(float(row.get("composite_score", 0)), 2),
            "dimension_scores": {},
            "key_stats": {
                "website": info.get("website", ""),
                "approved_intake_total": _safe_number(info.get("approved_intake_total")),
                "num_branches": _safe_number(info.get("num_branches"), integer=True),
                "placement_record_pct": _safe_number(info.get("placement_pct")),
                "nba_accredited_ratio": _safe_number(info.get("nba_accredited_ratio")),
                "autonomous": bool(info.get("is_autonomous", False)),
                "trend_direction": _trend_direction(row.get("trend_score", 50)),
                "scraped": bool(scraped.get("scraped")),
                "naac_grade": scraped.get("naac_grade"),
                "nirf_rank": _safe_number(scraped.get("nirf_rank"), integer=True),
                "placement_pct_web": _safe_number(scraped.get("placement_pct_web")),
                "avg_ctc_lpa": _safe_number(scraped.get("avg_ctc")),
                "faculty_count": _safe_number(scraped.get("faculty_count"), integer=True),
                "research_count": _safe_number(scraped.get("research_count"), integer=True),
            },
        }

        for dimension in WEIGHTS:
            score_col = f"{dimension}_score"
            entry["dimension_scores"][dimension] = round(
                float(row.get(score_col, 0)),
                2,
            )

        entries.append(entry)

    return entries


def _write_overall_csv(
    path: Path,
    overall: pd.DataFrame,
    lookup: dict[str, dict],
) -> None:
    rows = []
    for _, row in overall.iterrows():
        code = str(row.get("college_code", ""))
        info = lookup.get(code, {})
        item = {
            "rank": int(row.get("rank", 0)),
            "college_code": code,
            "college_name": info.get("college_name", ""),
            "district": info.get("district", ""),
            "composite_score": round(float(row.get("composite_score", 0)), 4),
        }
        for dimension in WEIGHTS:
            item[f"{dimension}_score"] = round(
                float(row.get(f"{dimension}_score", 0)),
                4,
            )
        rows.append(item)

    pd.DataFrame(rows).to_csv(path, index=False)


def _safe_number(value, integer: bool = False):
    if value in ("", None):
        return None
    try:
        return int(value) if integer else round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _trend_direction(score) -> str:
    try:
        value = float(score)
    except (TypeError, ValueError):
        value = 50.0

    if value >= 60:
        return "improving"
    if value <= 40:
        return "declining"
    return "stable"
