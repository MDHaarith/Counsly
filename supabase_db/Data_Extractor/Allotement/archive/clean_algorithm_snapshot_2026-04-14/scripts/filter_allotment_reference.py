#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ARCHITECTURE_BRANCH_CODES = {"AR", "BA", "BP", "DA", "ID"}


def load_reference_colleges(reference_json: Path) -> list[dict]:
    with reference_json.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise RuntimeError(f"Expected a list of colleges in {reference_json}")
    return [item for item in payload if isinstance(item, dict)]


def extract_branch_codes(college: dict) -> list[str]:
    courses = college.get("courses", [])
    if not isinstance(courses, list):
        return []
    branch_codes: list[str] = []
    for course in courses:
        if not isinstance(course, dict):
            continue
        branch_code = str(course.get("Branch_Code", "")).strip()
        if branch_code:
            branch_codes.append(branch_code)
    return branch_codes


def is_architecture_only_college(college: dict) -> bool:
    branch_codes = extract_branch_codes(college)
    return bool(branch_codes) and set(branch_codes).issubset(ARCHITECTURE_BRANCH_CODES)


def build_allowed_college_codes(reference_json: Path) -> tuple[set[str], set[str]]:
    colleges = load_reference_colleges(reference_json)
    allowed_codes: set[str] = set()
    architecture_only_codes: set[str] = set()

    for college in colleges:
        college_code = str(college.get("College_Code", "")).strip()
        if not college_code:
            continue
        if is_architecture_only_college(college):
            architecture_only_codes.add(college_code)
            continue
        allowed_codes.add(college_code)

    return allowed_codes, architecture_only_codes


def default_output_csv(merged_csv: Path) -> Path:
    return merged_csv.with_name(f"{merged_csv.stem}_non_architecture.csv")


def default_removed_report(merged_csv: Path) -> Path:
    return merged_csv.with_name(f"{merged_csv.stem}_removed_rows.csv")


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Filter a merged allotment CSV to keep only non-architecture colleges "
            "from a reference JSON file."
        )
    )
    parser.add_argument(
        "reference_json",
        type=Path,
        help="Path to the source college reference JSON file",
    )
    parser.add_argument(
        "merged_csv",
        type=Path,
        help="Path to the merged allotment CSV",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional explicit path for the filtered allotment CSV",
    )
    parser.add_argument(
        "--removed-report",
        type=Path,
        default=None,
        help="Optional explicit path for the removed-rows CSV report",
    )
    parser.add_argument(
        "--drop-architecture-branches",
        action="store_true",
        help=(
            "Also remove rows whose BRANCH CODE is architecture/design-related "
            "(AR, BA, BP, DA, ID), even inside mixed colleges"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    reference_json = args.reference_json.resolve()
    merged_csv = args.merged_csv.resolve()
    output_csv = (
        args.output_csv.resolve()
        if args.output_csv is not None
        else default_output_csv(merged_csv)
    )
    removed_report = (
        args.removed_report.resolve()
        if args.removed_report is not None
        else default_removed_report(merged_csv)
    )

    allowed_codes, architecture_only_codes = build_allowed_college_codes(reference_json)
    kept_rows: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []

    with merged_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise RuntimeError(f"No headers found in {merged_csv}")

        for row in reader:
            college_code = row.get("COLLEGE CODE", "").strip()
            branch_code = row.get("BRANCH CODE", "").strip()
            if college_code in allowed_codes:
                if (
                    args.drop_architecture_branches
                    and branch_code in ARCHITECTURE_BRANCH_CODES
                ):
                    removed_row = dict(row)
                    removed_row["REMOVAL_REASON"] = "architecture_branch"
                    removed_rows.append(removed_row)
                    continue
                kept_rows.append(dict(row))
                continue

            reason = "not_in_reference_json"
            if college_code in architecture_only_codes:
                reason = "architecture_only_college"
            removed_row = dict(row)
            removed_row["REMOVAL_REASON"] = reason
            removed_rows.append(removed_row)

    if not kept_rows:
        raise RuntimeError("No rows left after filtering allotment CSV")

    write_csv(output_csv, kept_rows, list(kept_rows[0].keys()))
    write_csv(
        removed_report,
        removed_rows,
        [*list(kept_rows[0].keys()), "REMOVAL_REASON"],
    )

    print(
        json.dumps(
            {
                "reference_json": str(reference_json),
                "merged_csv": str(merged_csv),
                "output_csv": str(output_csv),
                "removed_report": str(removed_report),
                "kept_rows": len(kept_rows),
                "removed_rows": len(removed_rows),
                "drop_architecture_branches": args.drop_architecture_branches,
                "architecture_only_codes_removed": sorted(architecture_only_codes),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
