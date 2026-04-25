#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from general_rank_list_parser import discover_pdfs, parse_pdf


COMPACT_HEADERS = [
    "YEAR",
    "GENERAL RANK",
    "AGGREGATE MARK",
    "COMMUNITY",
    "COMMUNITY RANK",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def bundle_records_path(output_root: Path, year: str, pdf_path: Path) -> Path:
    return output_root / "bundles" / f"{year}__{pdf_path.stem}" / "records.csv"


def run_workflow(input_root: Path, output_root: Path) -> dict[str, object]:
    pdf_paths = discover_pdfs(input_root)
    if not pdf_paths:
        raise RuntimeError(f"No GRL PDFs found under {input_root}")

    summaries: list[dict[str, object]] = []
    merged_rows: list[dict[str, str]] = []

    for pdf_path in pdf_paths:
        meta = parse_pdf(pdf_path, output_root, input_root, with_audit_files=False)
        year = str(meta["pdf_year"])
        records_path = bundle_records_path(output_root, year, pdf_path)

        with records_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                merged_rows.append(
                    {
                        "YEAR": year,
                        "GENERAL RANK": row.get("GENERAL RANK", "").strip(),
                        "AGGREGATE MARK": row.get("AGGREGATE MARK", "").strip(),
                        "COMMUNITY": row.get("COMMUNITY", "").strip(),
                        "COMMUNITY RANK": row.get("COMMUNITY RANK", "").strip(),
                    }
                )

        summaries.append(
            {
                "pdf": str(pdf_path.relative_to(input_root)),
                "year": year,
                "records": int(meta["parsed_records"]),
                "errors": int(meta["parse_error_count"]),
            }
        )

    merged_output = output_root / "merged" / "merged_general_rank_list_all_years.csv"
    write_csv(merged_output, merged_rows, COMPACT_HEADERS)

    report = {
        "input_root": str(input_root),
        "output_root": str(output_root),
        "pdf_count": len(pdf_paths),
        "merged_record_count": len(merged_rows),
        "merged_output": str(merged_output),
        "files": summaries,
    }
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Single PDF-only workflow for General Rank List data: parse every GRL PDF "
            "and write the compact merged CSV."
        )
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path.cwd(),
        help="Folder that contains GRL-<year>/GRL-<year>.pdf inputs. Default: current directory.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd() / "processed",
        help="Destination root for bundles and merged output. Default: ./processed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_workflow(args.input_root.resolve(), args.output_root.resolve())
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
