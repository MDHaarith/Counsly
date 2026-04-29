"""Validate local Supabase extractor or seed-source data before seeding Counsly."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[2] / "supabase_db" / "Data_Extractor"
DEFAULT_SEED_ROOT = Path(__file__).resolve().parents[2] / "supabase_db" / "seed_data"
REQUIRED_COMMUNITIES = {"OC", "BC", "BCM", "MBC", "SC", "ST"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for _ in reader)


def validate(root: Path) -> dict[str, Any]:
    if (root / "College_Info_Done").exists():
        paths = {
            "colleges": root / "College_Info_Done" / "output_present_non_architecture.json",
            "college_details": root / "College_Info_Done" / "output.json",
            "seat_matrix": root / "Seat_Matrix" / "output" / "seat_matrix_data.json",
            "cutoffs": root / "Allotement" / "data" / "processed" / "merged" / "merged_records_all_years_rounds_training_ready.csv",
            "geo": root / "geo_integration" / "active" / "v4go_intermediate" / "college_names_only_core_430_allotement_clean_output.json",
            "rank_lookup_source": root / "General_Rank_List" / "processed" / "merged" / "merged_general_rank_list_all_years.csv",
            "tfc": root / "TFC" / "tfc_locations.json",
        }
    else:
        paths = {
            "colleges": root / "colleges" / "colleges.json",
            "college_details": root / "colleges" / "college_details_raw.json",
            "seat_matrix": root / "community_seats" / "seat_matrix_2025_round_1.json",
            "cutoffs": root / "cutoff_data" / "cutoffs_2020_2025_training_ready.csv",
            "geo": root / "colleges" / "college_geo.json",
            "rank_lookup_source": root / "rank_lookup" / "general_rank_list_2020_2025.csv",
            "tfc": root / "tfc_locations" / "tfc_locations.json",
        }
    missing = [name for name, path in paths.items() if not path.exists()]
    report: dict[str, Any] = {"ok": not missing, "missing": missing, "datasets": {}}
    if missing:
        return report

    colleges = load_json(paths["colleges"])
    seat_matrix = load_json(paths["seat_matrix"])
    geo = load_json(paths["geo"])
    tfc = load_json(paths["tfc"])
    cutoff_rows = count_csv_rows(paths["cutoffs"])
    rank_lookup_source_rows = count_csv_rows(paths["rank_lookup_source"])

    report["datasets"] = {
        "colleges": len(colleges) if isinstance(colleges, list) else len(colleges.keys()),
        "seat_matrix": len(seat_matrix) if isinstance(seat_matrix, list) else len(seat_matrix.keys()),
        "cutoff_rows": cutoff_rows,
        "geo_rows": len(geo) if isinstance(geo, list) else len(geo.keys()),
        "rank_lookup_source_rows": rank_lookup_source_rows,
        "tfc_rows": len(tfc) if isinstance(tfc, list) else len(tfc.keys()),
    }
    failures: list[str] = []
    if report["datasets"]["colleges"] < 430:
        failures.append("Expected at least 430 non-architecture colleges")
    if report["datasets"]["seat_matrix"] < 3000:
        failures.append("Expected at least 3000 seat-matrix rows")
    if report["datasets"]["cutoff_rows"] < 500000:
        failures.append("Expected at least 500000 historical cutoff rows")
    if report["datasets"]["rank_lookup_source_rows"] < 500000:
        failures.append("Expected at least 500000 general-rank-list source rows")
    if report["datasets"]["tfc_rows"] < 100:
        failures.append("Expected at least 100 TFC rows")

    report["ok"] = not failures
    report["failures"] = failures
    report["required_communities"] = sorted(REQUIRED_COMMUNITIES)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local Supabase extractor or seed-source data for Counsly readiness")
    parser.add_argument("--root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--seed-data", action="store_true", help="Validate the compact supabase_db/seed_data snapshot.")
    args = parser.parse_args()
    root = DEFAULT_SEED_ROOT if args.seed_data else args.root
    report = validate(root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
