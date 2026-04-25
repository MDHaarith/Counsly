#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from qa.report_utils import ensure_dir, pct, read_csv_rows, write_json, write_text

ROOT = Path(__file__).resolve().parents[1]
TRAINING_CSV = ROOT / "Allotement/data/processed/merged/merged_records_all_years_rounds_training_ready.csv"
RANKINGS_CSV = ROOT / "Allotement/data/rankings/college_rankings.csv"
REPORT_DIR = ROOT / "qa/reports"
JSON_OUT = REPORT_DIR / "allotement_summary.json"
MD_OUT = REPORT_DIR / "allotement_summary.md"
VALID_COMMUNITIES = {"OC", "BC", "BCM", "MBC", "SC", "ST"}


def summarize_training(rows: list[dict[str, str]]) -> dict:
    years = Counter()
    rounds = Counter()
    communities = Counter()
    branch_codes = Counter()
    college_codes = Counter()
    invalid_community_rows = 0
    non_numeric_rank_rows = 0

    for row in rows:
        years[row.get("YEAR", "").strip()] += 1
        rounds[row.get("ROUND", "").strip()] += 1
        communities[row.get("COMMUNITY", "").strip()] += 1
        branch_codes[row.get("BRANCH CODE", "").strip()] += 1
        college_codes[row.get("COLLEGE CODE", "").strip()] += 1

        if row.get("COMMUNITY", "").strip() not in VALID_COMMUNITIES:
            invalid_community_rows += 1
        if not row.get("RANK", "").strip().isdigit():
            non_numeric_rank_rows += 1

    return {
        "row_count": len(rows),
        "year_counts": dict(sorted(years.items())),
        "round_counts": dict(sorted(rounds.items())),
        "community_counts": dict(sorted(communities.items())),
        "unique_colleges": len([k for k in college_codes if k]),
        "unique_branches": len([k for k in branch_codes if k]),
        "top_10_branch_codes": branch_codes.most_common(10),
        "invalid_community_rows": invalid_community_rows,
        "non_numeric_rank_rows": non_numeric_rank_rows,
    }


def summarize_rankings(rows: list[dict[str, str]]) -> dict:
    missing_district = 0
    score_bounds_violations = 0

    for row in rows:
        if not row.get("district", "").strip():
            missing_district += 1
        for field in [
            "composite_score",
            "selectivity_score",
            "academic_quality_score",
            "branch_strength_score",
            "institutional_quality_score",
            "web_reputation_score",
            "trend_score",
        ]:
            try:
                value = float(row.get(field, ""))
            except ValueError:
                score_bounds_violations += 1
                continue
            if value < 0 or value > 100:
                score_bounds_violations += 1

    return {
        "row_count": len(rows),
        "missing_district_rows": missing_district,
        "missing_district_pct": pct(missing_district, len(rows)),
        "score_bounds_violations": score_bounds_violations,
        "top_10": rows[:10],
    }


def main() -> int:
    ensure_dir(REPORT_DIR)
    training_rows = read_csv_rows(TRAINING_CSV)
    ranking_rows = read_csv_rows(RANKINGS_CSV)

    summary = {
        "training": summarize_training(training_rows),
        "rankings": summarize_rankings(ranking_rows),
    }
    write_json(JSON_OUT, summary)

    md = []
    md.append("# Allotement QA Summary")
    md.append("")
    md.append(f"- Training rows: {summary['training']['row_count']}")
    md.append(f"- Ranking rows: {summary['rankings']['row_count']}")
    md.append(f"- Unique colleges in training: {summary['training']['unique_colleges']}")
    md.append(f"- Unique branches in training: {summary['training']['unique_branches']}")
    md.append(f"- Invalid community rows: {summary['training']['invalid_community_rows']}")
    md.append(f"- Non-numeric rank rows: {summary['training']['non_numeric_rank_rows']}")
    md.append(f"- Ranking rows missing district: {summary['rankings']['missing_district_rows']} ({summary['rankings']['missing_district_pct']}%)")
    md.append(f"- Score bound violations: {summary['rankings']['score_bounds_violations']}")
    md.append("")
    md.append("## Year counts")
    for year, count in summary['training']['year_counts'].items():
        md.append(f"- {year}: {count}")
    md.append("")
    md.append("## Community counts")
    for community, count in summary['training']['community_counts'].items():
        md.append(f"- {community}: {count}")
    md.append("")
    md.append("## Top branch codes")
    for branch, count in summary['training']['top_10_branch_codes']:
        md.append(f"- {branch}: {count}")

    write_text(MD_OUT, "\n".join(md) + "\n")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
