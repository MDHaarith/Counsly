#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ARCHITECTURE_BRANCH_CODES = {"AR", "BA", "BP", "DA", "ID", "IF"}
SELF_FINANCING_MARKER = "(SS)"
ARCHITECTURE_NAME_MARKERS = (
    "architecture",
    "b.plan",
    "b plan",
    "interior design",
)
KEEP_NAME_MARKERS = (
    "computer science and design",
    "data science",
    "artificial intelligence",
    "machine learning",
    "cyber security",
    "computer science",
)


def load_seat_matrix(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise RuntimeError(f"Expected a list of seat-matrix rows in {path}")
    return [item for item in payload if isinstance(item, dict)]


def is_self_financing_name(branch_name: str) -> bool:
    return SELF_FINANCING_MARKER in branch_name.upper()


def is_architecture_branch(branch_code: str, branch_names: set[str]) -> bool:
    lowered_names = [name.lower() for name in branch_names]

    if any(
        keep_marker in lowered_name
        for lowered_name in lowered_names
        for keep_marker in KEEP_NAME_MARKERS
    ):
        return False

    if branch_code in ARCHITECTURE_BRANCH_CODES:
        return True

    return any(
        marker in lowered_name
        for lowered_name in lowered_names
        for marker in ARCHITECTURE_NAME_MARKERS
    )


def choose_canonical_name(names: Counter[str]) -> str:
    if not names:
        return ""
    return sorted(names.items(), key=lambda item: (-item[1], item[0]))[0][0]


def build_branch_master(rows: list[dict]) -> list[dict]:
    by_code: dict[str, Counter[str]] = defaultdict(Counter)
    college_counts: dict[str, set[str]] = defaultdict(set)
    row_counts: Counter[str] = Counter()
    seat_totals: Counter[str] = Counter()

    for row in rows:
        branch_code = str(row.get("branch_code", "")).strip()
        branch_name = str(row.get("branch_name", "")).strip()
        college_code = str(row.get("college_code", "")).strip()
        total = int(row.get("total", 0) or 0)

        if not branch_code:
            continue

        if branch_name:
            by_code[branch_code][branch_name] += 1
        if college_code:
            college_counts[branch_code].add(college_code)
        row_counts[branch_code] += 1
        seat_totals[branch_code] += total

    master: list[dict] = []
    for branch_code in sorted(by_code):
        names_counter = by_code[branch_code]
        observed_names = sorted(names_counter)
        canonical_name = choose_canonical_name(names_counter)
        self_financing = any(is_self_financing_name(name) for name in observed_names)
        architecture = is_architecture_branch(branch_code, set(observed_names))

        removal_reasons: list[str] = []
        if self_financing:
            removal_reasons.append("self_financing")
        if architecture:
            removal_reasons.append("architecture")

        master.append(
            {
                "branch_code": branch_code,
                "branch_name": canonical_name,
                "observed_names": observed_names,
                "row_count": row_counts[branch_code],
                "college_count": len(college_counts[branch_code]),
                "total_seats": seat_totals[branch_code],
                "is_self_financing": self_financing,
                "is_architecture": architecture,
                "keep": not removal_reasons,
                "removal_reasons": removal_reasons,
            }
        )

    return master


def default_output_json(input_json: Path) -> Path:
    return input_json.with_name("branch_codes_filtered.json")


def default_removed_csv(input_json: Path) -> Path:
    return input_json.with_name("branch_codes_removed.csv")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def write_removed_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "branch_code",
                "branch_name",
                "observed_names",
                "row_count",
                "college_count",
                "total_seats",
                "removal_reasons",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "branch_code": row["branch_code"],
                    "branch_name": row["branch_name"],
                    "observed_names": " | ".join(row["observed_names"]),
                    "row_count": row["row_count"],
                    "college_count": row["college_count"],
                    "total_seats": row["total_seats"],
                    "removal_reasons": "|".join(row["removal_reasons"]),
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a branch-code master from seat-matrix output and remove "
            "self-financing and architecture-related branches."
        )
    )
    parser.add_argument(
        "input_json",
        type=Path,
        nargs="?",
        default=Path(__file__).resolve().parent / "output" / "seat_matrix_data.json",
        help="Seat matrix JSON input file",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional explicit path for the kept branch master JSON",
    )
    parser.add_argument(
        "--removed-csv",
        type=Path,
        default=None,
        help="Optional explicit path for the removed branch report CSV",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    input_json = args.input_json.resolve()
    output_json = (
        args.output_json.resolve()
        if args.output_json is not None
        else default_output_json(input_json)
    )
    removed_csv = (
        args.removed_csv.resolve()
        if args.removed_csv is not None
        else default_removed_csv(input_json)
    )

    rows = load_seat_matrix(input_json)
    branch_master = build_branch_master(rows)
    kept = [row for row in branch_master if row["keep"]]
    removed = [row for row in branch_master if not row["keep"]]

    write_json(output_json, kept)
    write_removed_csv(removed_csv, removed)

    print(
        json.dumps(
            {
                "input_json": str(input_json),
                "output_json": str(output_json),
                "removed_csv": str(removed_csv),
                "total_branch_codes": len(branch_master),
                "kept_branch_codes": len(kept),
                "removed_branch_codes": len(removed),
                "removed_codes": [row["branch_code"] for row in removed],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
