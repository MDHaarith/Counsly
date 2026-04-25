"""Validate local Data_Extractor outputs before seeding Counsly."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REQUIRED_COMMUNITIES = {"OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for _ in reader)


def validate(root: Path) -> dict[str, Any]:
    paths = {
        "colleges": root / "College_Info_Done" / "output_present_non_architecture.json",
        "college_details": root / "College_Info_Done" / "output.json",
        "seat_matrix": root / "Seat_Matrix" / "output" / "seat_matrix_data.json",
        "cutoffs": root / "Allotement" / "data" / "processed" / "merged" / "merged_records_all_years_rounds_training_ready.csv",
        "geo": root / "geo_integration" / "active" / "v4go_intermediate" / "college_names_only_core_430_allotement_clean_output.json",
        "tfc": root / "TFC" / "tfc_locations.json",
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

    report["datasets"] = {
        "colleges": len(colleges) if isinstance(colleges, list) else len(colleges.keys()),
        "seat_matrix": len(seat_matrix) if isinstance(seat_matrix, list) else len(seat_matrix.keys()),
        "cutoff_rows": cutoff_rows,
        "geo_rows": len(geo) if isinstance(geo, list) else len(geo.keys()),
        "tfc_rows": len(tfc) if isinstance(tfc, list) else len(tfc.keys()),
    }
    failures: list[str] = []
    if report["datasets"]["colleges"] < 430:
        failures.append("Expected at least 430 non-architecture colleges")
    if report["datasets"]["seat_matrix"] < 3000:
        failures.append("Expected at least 3000 seat-matrix rows")
    if report["datasets"]["cutoff_rows"] < 500000:
        failures.append("Expected at least 500000 historical cutoff rows")
    if report["datasets"]["tfc_rows"] < 100:
        failures.append("Expected at least 100 TFC rows")

    report["ok"] = not failures
    report["failures"] = failures
    report["required_communities"] = sorted(REQUIRED_COMMUNITIES)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local extractor outputs for Counsly seed readiness")
    parser.add_argument("--root", default="/home/mdhaarith/Desktop/Data_Extractor (Copy)")
    args = parser.parse_args()
    report = validate(Path(args.root))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
