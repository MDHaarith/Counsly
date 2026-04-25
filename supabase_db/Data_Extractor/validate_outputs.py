#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def csv_row_count(path: Path) -> int:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_allotement(errors: list[str], summary: list[str]) -> None:
    training_csv = ROOT / "Allotement/data/processed/merged/merged_records_all_years_rounds_training_ready.csv"
    rankings_csv = ROOT / "Allotement/data/rankings/college_rankings.csv"

    require(training_csv.exists(), f"Missing training CSV: {training_csv}", errors)
    require(rankings_csv.exists(), f"Missing rankings CSV: {rankings_csv}", errors)
    if not training_csv.exists() or not rankings_csv.exists():
        return

    train_rows = csv_row_count(training_csv)
    rank_rows = csv_row_count(rankings_csv)
    require(train_rows > 0, "Training CSV has no rows", errors)
    require(rank_rows > 0, "Rankings CSV has no rows", errors)

    summary.append(f"Allotement training rows: {train_rows}")
    summary.append(f"Allotement ranking rows: {rank_rows}")


def validate_general_rank_list(errors: list[str], summary: list[str]) -> None:
    merged_csv = ROOT / "General_Rank_List/processed/merged/merged_general_rank_list_all_years.csv"
    require(merged_csv.exists(), f"Missing GRL merged CSV: {merged_csv}", errors)
    if not merged_csv.exists():
        return

    rows = csv_row_count(merged_csv)
    require(rows > 0, "GRL merged CSV has no rows", errors)
    summary.append(f"General Rank List rows: {rows}")


def validate_college_info(errors: list[str], summary: list[str]) -> None:
    raw_json = ROOT / "College_Info_Done/output.json"
    filtered_json = ROOT / "College_Info_Done/output_present_non_architecture.json"

    require(raw_json.exists(), f"Missing college info JSON: {raw_json}", errors)
    require(filtered_json.exists(), f"Missing filtered college info JSON: {filtered_json}", errors)
    if not raw_json.exists() or not filtered_json.exists():
        return

    raw = load_json(raw_json)
    filtered = load_json(filtered_json)
    require(isinstance(raw, list), "College info JSON is not a list", errors)
    require(isinstance(filtered, list), "Filtered college info JSON is not a list", errors)
    if not isinstance(raw, list) or not isinstance(filtered, list):
        return

    require(len(raw) > 0, "College info JSON is empty", errors)
    require(len(filtered) > 0, "Filtered college info JSON is empty", errors)
    require(len(filtered) <= len(raw), "Filtered college count exceeds raw college count", errors)

    summary.append(f"College info raw count: {len(raw)}")
    summary.append(f"College info filtered count: {len(filtered)}")


def validate_optional_outputs(summary: list[str]) -> None:
    for rel in [
        "Pass_Percentage/output",
        "Seat_Matrix/output",
    ]:
        path = ROOT / rel
        if path.exists() and path.is_dir():
            count = sum(1 for _ in path.iterdir())
            summary.append(f"{rel} files: {count}")


def main() -> int:
    errors: list[str] = []
    summary: list[str] = []

    validate_allotement(errors, summary)
    validate_general_rank_list(errors, summary)
    validate_college_info(errors, summary)
    validate_optional_outputs(summary)

    print("Validation summary:")
    for line in summary:
        print(f"- {line}")

    if errors:
        print("\nValidation errors:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
