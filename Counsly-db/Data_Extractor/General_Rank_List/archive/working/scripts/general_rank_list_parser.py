#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


YEAR_RE = re.compile(r"TAMILNADU ENGINEERING ADMISSIONS?\s*-?\s*(\d{4})", re.IGNORECASE)
DATE_RE = re.compile(r"\d{1,2}[-/]\d{1,2}[-/]\d{4}")
MARK_RE = re.compile(r"\d+(?:\.\d+)?")
PAGE_OF_RE = re.compile(r"Page\s+\d+\s+of\s+\d+", re.IGNORECASE)
RECORD_START_RE = re.compile(r"^\s*\d+\s+\d{6}\b")
COMMUNITY_RE = re.compile(r"[A-Z]+")
ATTACHED_DATE_RE = re.compile(r"^(.*?)(\d{1,2}[-/]\d{1,2}[-/]\d{4})$")
ATTACHED_MARK_RE = re.compile(r"^(.*?)(\d+(?:\.\d+)?)$")
COMMUNITY_VALUES = {
    "OC",
    "BC",
    "BCM",
    "MBC",
    "MBCV",
    "MBCDNC",
    "MBC/DNC",
    "SC",
    "SCA",
    "ST",
}

BUNDLES_DIRNAME = "bundles"
MERGED_DIRNAME = "merged"
REPORTS_DIRNAME = "reports"

STANDARDIZED_HEADERS = [
    "S NO",
    "GENERAL RANK",
    "APPLICATION NUMBER",
    "NAME OF THE CANDIDATE",
    "DATE OF BIRTH",
    "AGGREGATE MARK",
    "COMMUNITY",
    "COMMUNITY RANK",
]


@dataclass
class ParsedRecord:
    year: str
    layout_type: str
    s_no: str
    general_rank: str
    application_number: str
    candidate_name: str
    date_of_birth: str
    aggregate_mark: str
    community: str
    community_rank: str


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def remove_if_exists(path: Path) -> None:
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def run_pdftotext(pdf_path: Path) -> str:
    if shutil.which("pdftotext") is None:
        raise RuntimeError("`pdftotext` is required but not installed.")

    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.stdout


def split_pages(full_text: str) -> list[str]:
    pages = [page.rstrip("\n") for page in full_text.split("\f")]
    return [page for page in pages if page.strip()]


def infer_year(first_page_lines: list[str], pdf_path: Path) -> str:
    for line in first_page_lines[:8]:
        match = YEAR_RE.search(line)
        if match:
            return match.group(1)

    for part in pdf_path.parts:
        match = re.search(r"(\d{4})", part)
        if match:
            return match.group(1)

    raise RuntimeError(f"Unable to infer year from {pdf_path}")


def classify_line(text: str) -> str:
    stripped = text.strip()
    normalized = normalize_space(stripped).upper()

    if not stripped:
        return "blank"
    if stripped.isdigit():
        return "footer_page_number"
    if PAGE_OF_RE.fullmatch(stripped):
        return "footer_page_of"
    if "TAMILNADU ENGINEERING ADMISSION" in normalized:
        return "header_title"
    if "DIRECTORATE OF TECHNICAL EDUCATION" in normalized:
        return "header_department"
    if (
        "PROVISIONAL RANK LIST" in normalized
        or "ACADEMIC RANK LIST" in normalized
        or "GENERAL RANK LIST" in normalized
    ):
        return "header_list_title"
    if normalized.startswith("**") or "HONORABLE HIGH COURT" in normalized or "WRIT PETITION" in normalized:
        return "footnote_annotation"
    if normalized.startswith("S NO"):
        return "header_columns"
    if normalized == "RANK":
        return "header_columns"
    if "APPLICATION" in normalized or "NUMBER" == normalized:
        return "header_columns"
    if "NAME OF THE CANDIDATE" in normalized:
        return "header_columns"
    if "DATE OF BIRTH" in normalized or normalized == "DOB":
        return "header_columns"
    if "AGGREGATE" in normalized or "CUTOFF" in normalized:
        return "header_columns"
    if "MARK" in normalized and ("NUMBER" in normalized or "RANK" in normalized):
        return "header_columns"
    if "COMMUNITY" in normalized:
        return "header_columns"
    return "other"


def looks_like_date(token: str) -> bool:
    return bool(DATE_RE.fullmatch(token))


def looks_like_mark(token: str) -> bool:
    return bool(MARK_RE.fullmatch(token))


def looks_like_community(token: str) -> bool:
    normalized = token.upper()
    if normalized in COMMUNITY_VALUES:
        return True
    return normalized.replace("/", "") in COMMUNITY_VALUES


def split_attached_date_tokens(tokens: list[str]) -> list[str]:
    expanded: list[str] = []
    for token in tokens:
        match = ATTACHED_DATE_RE.fullmatch(token)
        if match and match.group(1):
            expanded.append(match.group(1))
            expanded.append(match.group(2))
        else:
            expanded.append(token)
    return expanded


def split_attached_mark_tokens(tokens: list[str]) -> list[str]:
    expanded: list[str] = []
    for token in tokens:
        match = ATTACHED_MARK_RE.fullmatch(token)
        if not match or not match.group(1) or looks_like_mark(token):
            expanded.append(token)
            continue

        mark = match.group(2)
        try:
            mark_value = float(mark)
        except ValueError:
            expanded.append(token)
            continue

        if 50 <= mark_value <= 200 and any(char.isalpha() for char in match.group(1)):
            expanded.append(match.group(1))
            expanded.append(mark)
        else:
            expanded.append(token)
    return expanded


def parse_2025_record(compact: str) -> ParsedRecord:
    match = re.fullmatch(
        r"(\d+)\s+(\d{6})\s+(\d+(?:\.\d+)?)\s+(\d+)\s+([A-Z]+)(?:\s+(\d+))?",
        compact,
    )
    if not match:
        raise ValueError(f"Unrecognized 2025 record layout: {compact}")

    s_no, application_number, aggregate_mark, general_rank, community, community_rank = match.groups()
    return ParsedRecord(
        year="2025",
        layout_type="2025_no_name_no_dob",
        s_no=s_no,
        general_rank=general_rank,
        application_number=application_number,
        candidate_name="",
        date_of_birth="",
        aggregate_mark=aggregate_mark,
        community=community,
        community_rank=community_rank or "",
    )


def parse_name_based_record(year: str, compact: str) -> ParsedRecord:
    tokens = split_attached_mark_tokens(split_attached_date_tokens(compact.split()))
    if len(tokens) < 5:
        raise ValueError(f"Too few tokens for {year} record: {compact}")
    if not tokens[0].isdigit():
        raise ValueError(f"Missing rank token for {year} record: {compact}")
    if not re.fullmatch(r"\d{6}", tokens[1]):
        raise ValueError(f"Missing application number for {year} record: {compact}")

    date_index = next((index for index, token in enumerate(tokens) if looks_like_date(token)), None)
    if date_index is None:
        raise ValueError(f"Missing DOB token for {year} record: {compact}")

    general_rank = tokens[0]
    application_number = tokens[1]
    community_rank = ""

    if year == "2021":
        if date_index < 3:
            raise ValueError(f"Unexpected 2021 layout around DOB: {compact}")
        aggregate_mark = tokens[date_index - 1]
        if not looks_like_mark(aggregate_mark):
            raise ValueError(f"Invalid aggregate mark in 2021 record: {compact}")
        candidate_name_tokens = tokens[2 : date_index - 1]
        tail = tokens[date_index + 1 :]
        if len(tail) < 1:
            raise ValueError(f"Missing community in 2021 record: {compact}")
        community = tail[0]
        if not looks_like_community(community):
            raise ValueError(f"Invalid community in 2021 record: {compact}")
        extra_name_tokens: list[str] = []
        if len(tail) > 1 and tail[1].isdigit():
            community_rank = tail[1]
            extra_name_tokens = tail[2:]
        else:
            extra_name_tokens = tail[1:]
        candidate_name_tokens.extend(extra_name_tokens)
    else:
        candidate_name_tokens = tokens[2:date_index]
        tail = tokens[date_index + 1 :]
        if year == "2020":
            community_index = next(
                (index for index in range(len(tail) - 1, -1, -1) if looks_like_community(tail[index])),
                None,
            )
            if community_index is None:
                raise ValueError(f"Missing community in {year} record: {compact}")
            community = tail[community_index]
            extra_name_tokens = tail[:community_index]
            after_community = tail[community_index + 1 :]
            if len(after_community) < 1:
                raise ValueError(f"Missing aggregate mark in {year} record: {compact}")
            aggregate_mark = after_community[0]
            if len(after_community) > 1:
                community_rank = after_community[1]
            if len(after_community) > 2:
                raise ValueError(f"Unexpected trailing tokens in {year} record: {compact}")
        else:
            community_index = next(
                (index for index in range(len(tail) - 1, -1, -1) if looks_like_community(tail[index])),
                None,
            )
            if community_index is None or community_index == 0:
                raise ValueError(f"Missing community/mark pair in {year} record: {compact}")
            aggregate_mark = tail[community_index - 1]
            community = tail[community_index]
            extra_name_tokens = tail[: community_index - 1]
            after_community = tail[community_index + 1 :]
            trailing_name_tokens: list[str] = []
            if after_community and after_community[0].isdigit():
                community_rank = after_community[0]
                trailing_name_tokens = after_community[1:]
            else:
                trailing_name_tokens = after_community
            extra_name_tokens.extend(trailing_name_tokens)
        if not looks_like_community(community):
            raise ValueError(f"Invalid community in {year} record: {compact}")
        if not looks_like_mark(aggregate_mark):
            raise ValueError(f"Invalid aggregate mark in {year} record: {compact}")
        candidate_name_tokens.extend(extra_name_tokens)

    return ParsedRecord(
        year=year,
        layout_type=f"{year}_name_based",
        s_no="",
        general_rank=general_rank,
        application_number=application_number,
        candidate_name=" ".join(candidate_name_tokens),
        date_of_birth=tokens[date_index],
        aggregate_mark=aggregate_mark,
        community=community,
        community_rank=community_rank,
    )


def parse_record(year: str, raw_record_text: str) -> ParsedRecord:
    compact = normalize_space(raw_record_text)
    if year == "2025":
        parsed = parse_2025_record(compact)
    else:
        parsed = parse_name_based_record(year, compact)

    if parsed.community.upper() == "OC" and not parsed.community_rank.strip():
        parsed.community_rank = parsed.general_rank

    return parsed


def has_inline_name_2021(start_line: str) -> bool:
    tokens = split_attached_mark_tokens(split_attached_date_tokens(normalize_space(start_line).split()))
    if len(tokens) < 5:
        return False
    if not tokens[0].isdigit() or not re.fullmatch(r"\d{6}", tokens[1]):
        return False
    date_index = next((index for index, token in enumerate(tokens) if looks_like_date(token)), None)
    if date_index is None or date_index < 3:
        return False
    aggregate_mark = tokens[date_index - 1]
    if not looks_like_mark(aggregate_mark):
        return False
    return bool(tokens[2 : date_index - 1])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def derive_bundle_dir(output_root: Path, year: str, pdf_path: Path) -> Path:
    return output_root / BUNDLES_DIRNAME / f"{year}__{pdf_path.stem}"


def parse_pdf(
    pdf_path: Path,
    output_root: Path,
    input_root: Path,
    *,
    max_pages: int | None = None,
    with_audit_files: bool = False,
) -> dict[str, str | int]:
    raw_text = run_pdftotext(pdf_path)
    pages = split_pages(raw_text)
    if max_pages is not None:
        pages = pages[:max_pages]

    if not pages:
        raise RuntimeError(f"No text extracted from {pdf_path}")

    first_page_lines = [line.rstrip() for line in pages[0].splitlines() if line.strip()]
    year = infer_year(first_page_lines, pdf_path)
    bundle_dir = derive_bundle_dir(output_root, year, pdf_path)
    audit_dir = bundle_dir / "audit"

    ensure_dir(bundle_dir)
    for stale_path in [
        bundle_dir / "records.csv",
        bundle_dir / "meta.json",
        audit_dir / "records_full.csv",
        audit_dir / "unparsed_lines.csv",
        output_root / REPORTS_DIRNAME / "batch_manifest.csv",
    ]:
        remove_if_exists(stale_path)
    if not with_audit_files:
        remove_if_exists(audit_dir)
    else:
        ensure_dir(audit_dir)

    relative_source = str(pdf_path.resolve())
    try:
        relative_source = str(pdf_path.resolve().relative_to(input_root.resolve()))
    except ValueError:
        pass

    sha256 = compute_sha256(pdf_path)
    file_size_bytes = pdf_path.stat().st_size

    clean_rows: list[dict[str, str]] = []
    full_rows: list[dict[str, str]] = []
    unparsed_rows: list[dict[str, str]] = []
    parse_error_count = 0
    total_record_blocks = 0

    for page_number, page_text in enumerate(pages, start=1):
        lines = page_text.splitlines()
        record_start_indexes = [
            index for index, line in enumerate(lines) if RECORD_START_RE.match(line)
        ]
        assigned_indexes: set[int] = set()
        previous_end_index = 0
        carried_name_lines: list[str] = []
        carried_name_line_numbers: list[int] = []

        for block_pos, start_index in enumerate(record_start_indexes):
            end_index = (
                record_start_indexes[block_pos + 1]
                if block_pos + 1 < len(record_start_indexes)
                else len(lines)
            )
            leading_name_lines: list[str] = carried_name_lines[:]
            leading_name_line_numbers: list[int] = carried_name_line_numbers[:]
            carried_name_lines = []
            carried_name_line_numbers = []
            for line_index in range(previous_end_index, start_index):
                line = lines[line_index]
                if not line.strip():
                    continue
                classification = classify_line(line)
                if classification.startswith("header_") or classification.startswith("footer_"):
                    continue
                if classification == "footnote_annotation":
                    continue
                if any(char.isdigit() for char in line):
                    continue
                leading_name_lines.append(normalize_space(line))
                leading_name_line_numbers.append(line_index + 1)

            raw_lines: list[str] = []
            raw_line_numbers: list[int] = []
            next_record_name_lines: list[str] = []
            next_record_name_line_numbers: list[int] = []
            start_line_has_inline_name = year == "2021" and has_inline_name_2021(lines[start_index])
            for line_index in range(start_index, end_index):
                line = lines[line_index]
                if not line.strip():
                    continue
                classification = classify_line(line)
                if line_index != start_index and classification.startswith("header_"):
                    continue
                if line_index != start_index and classification.startswith("footer_"):
                    continue
                if line_index != start_index and classification == "footnote_annotation":
                    break
                if (
                    year == "2021"
                    and line_index != start_index
                    and start_line_has_inline_name
                    and not any(char.isdigit() for char in line)
                ):
                    next_record_name_lines.append(normalize_space(line))
                    next_record_name_line_numbers.append(line_index + 1)
                    continue
                raw_lines.append(line.rstrip())
                raw_line_numbers.append(line_index + 1)

            previous_end_index = end_index
            carried_name_lines = next_record_name_lines
            carried_name_line_numbers = next_record_name_line_numbers

            if not raw_lines:
                continue

            total_record_blocks += 1
            raw_record_text = "\n".join(raw_lines)
            normalized_record_text = normalize_space(raw_record_text)

            try:
                parsed = parse_record(year, raw_record_text)
                if leading_name_lines:
                    merged_name_parts = leading_name_lines[:]
                    if parsed.candidate_name:
                        merged_name_parts.append(parsed.candidate_name)
                    parsed.candidate_name = " ".join(merged_name_parts).strip()
                clean_rows.append(
                    {
                        "S NO": parsed.s_no,
                        "GENERAL RANK": parsed.general_rank,
                        "APPLICATION NUMBER": parsed.application_number,
                        "NAME OF THE CANDIDATE": parsed.candidate_name,
                        "DATE OF BIRTH": parsed.date_of_birth,
                        "AGGREGATE MARK": parsed.aggregate_mark,
                        "COMMUNITY": parsed.community,
                        "COMMUNITY RANK": parsed.community_rank,
                    }
                )
                full_rows.append(
                    {
                        "source_pdf_abs_path": str(pdf_path.resolve()),
                        "source_pdf_rel_path": relative_source,
                        "pdf_sha256": sha256,
                        "file_size_bytes": str(file_size_bytes),
                        "pdf_year": year,
                        "page_number": str(page_number),
                        "record_sequence": str(len(full_rows) + 1),
                        "layout_type": parsed.layout_type,
                        "record_line_numbers": ",".join(str(n) for n in raw_line_numbers),
                        "s_no": parsed.s_no,
                        "general_rank": parsed.general_rank,
                        "application_number": parsed.application_number,
                        "candidate_name": parsed.candidate_name,
                        "date_of_birth": parsed.date_of_birth,
                        "aggregate_mark": parsed.aggregate_mark,
                        "community": parsed.community,
                        "community_rank": parsed.community_rank,
                        "raw_record_text": raw_record_text,
                        "normalized_record_text": normalized_record_text,
                    }
                )
                assigned_indexes.update(line_number - 1 for line_number in raw_line_numbers)
                assigned_indexes.update(line_number - 1 for line_number in leading_name_line_numbers)
            except ValueError as exc:
                parse_error_count += 1
                unparsed_rows.append(
                    {
                        "source_pdf_abs_path": str(pdf_path.resolve()),
                        "source_pdf_rel_path": relative_source,
                        "pdf_sha256": sha256,
                        "pdf_year": year,
                        "page_number": str(page_number),
                        "record_line_numbers": ",".join(str(n) for n in raw_line_numbers),
                        "classification": "parse_error",
                        "text": raw_record_text,
                        "error": str(exc),
                    }
                )
                assigned_indexes.update(line_number - 1 for line_number in raw_line_numbers)

        footnote_started = False
        for line_index, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            classification = classify_line(line)
            if classification == "footnote_annotation":
                footnote_started = True
            if footnote_started:
                continue
            if line_index - 1 in assigned_indexes:
                continue
            if RECORD_START_RE.match(line):
                continue
            if classification in {
                "blank",
                "header_title",
                "header_department",
                "header_list_title",
                "header_columns",
                "footer_page_of",
                "footer_page_number",
                "footnote_annotation",
            }:
                continue
            unparsed_rows.append(
                {
                    "source_pdf_abs_path": str(pdf_path.resolve()),
                    "source_pdf_rel_path": relative_source,
                    "pdf_sha256": sha256,
                    "pdf_year": year,
                    "page_number": str(page_number),
                    "record_line_numbers": str(line_index),
                    "classification": classification,
                    "text": line.rstrip(),
                    "error": "",
                }
            )

    if not clean_rows:
        raise RuntimeError(f"No records parsed from {pdf_path}")

    records_path = bundle_dir / "records.csv"
    meta_path = bundle_dir / "meta.json"
    write_csv(records_path, clean_rows, STANDARDIZED_HEADERS)
    if with_audit_files:
        write_csv(
            audit_dir / "records_full.csv",
            full_rows,
            [
                "source_pdf_abs_path",
                "source_pdf_rel_path",
                "pdf_sha256",
                "file_size_bytes",
                "pdf_year",
                "page_number",
                "record_sequence",
                "layout_type",
                "record_line_numbers",
                "s_no",
                "general_rank",
                "application_number",
                "candidate_name",
                "date_of_birth",
                "aggregate_mark",
                "community",
                "community_rank",
                "raw_record_text",
                "normalized_record_text",
            ],
        )
        write_csv(
            audit_dir / "unparsed_lines.csv",
            unparsed_rows,
            [
                "source_pdf_abs_path",
                "source_pdf_rel_path",
                "pdf_sha256",
                "pdf_year",
                "page_number",
                "record_line_numbers",
                "classification",
                "text",
                "error",
            ],
        )

    max_general_rank = max(
        (int(row["GENERAL RANK"]) for row in clean_rows if row["GENERAL RANK"].isdigit()),
        default=0,
    )
    max_s_no = max((int(row["S NO"]) for row in clean_rows if row["S NO"].isdigit()), default=0)
    meta = {
        "source_pdf_abs_path": str(pdf_path.resolve()),
        "source_pdf_rel_path": relative_source,
        "pdf_sha256": sha256,
        "file_size_bytes": file_size_bytes,
        "pdf_year": year,
        "parsed_pages": len(pages),
        "parsed_records": len(clean_rows),
        "record_blocks_seen": total_record_blocks,
        "parse_error_count": parse_error_count,
        "non_record_unparsed_line_count": len([row for row in unparsed_rows if not row["error"]]),
        "max_general_rank": max_general_rank,
        "max_s_no": max_s_no,
        "general_rank_matches_record_count": max_general_rank == len(clean_rows),
        "s_no_matches_record_count": (max_s_no == len(clean_rows)) if year == "2025" else True,
    }
    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2)

    return meta


def load_bundle_manifest(meta_path: Path) -> dict[str, str]:
    with meta_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected object in {meta_path}")
    return {str(key): str(value) for key, value in payload.items()}


def collect_record_sources(output_root: Path) -> list[tuple[Path, str]]:
    bundles_root = output_root / BUNDLES_DIRNAME
    sources: list[tuple[Path, str]] = []
    if not bundles_root.exists():
        return sources

    for bundle_dir in sorted(path for path in bundles_root.iterdir() if path.is_dir()):
        records_path = bundle_dir / "records.csv"
        meta_path = bundle_dir / "meta.json"
        if not records_path.exists() or not meta_path.exists():
            continue
        manifest = load_bundle_manifest(meta_path)
        sources.append((records_path.resolve(), manifest.get("pdf_year", "")))
    return sources


def merge_clean_csvs(output_root: Path, destination: Path | None = None) -> Path:
    output_root = output_root.resolve()
    if destination is None:
        destination = output_root / MERGED_DIRNAME / "merged_general_rank_list_all_years.csv"
    else:
        destination = destination.resolve()

    merged_rows: list[dict[str, str]] = []
    for records_path, year in collect_record_sources(output_root):
        with records_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                merged_rows.append(
                    {
                        "YEAR": year,
                        "S NO": row.get("S NO", ""),
                        "GENERAL RANK": row.get("GENERAL RANK", ""),
                        "APPLICATION NUMBER": row.get("APPLICATION NUMBER", ""),
                        "NAME OF THE CANDIDATE": row.get("NAME OF THE CANDIDATE", ""),
                        "DATE OF BIRTH": row.get("DATE OF BIRTH", ""),
                        "AGGREGATE MARK": row.get("AGGREGATE MARK", ""),
                        "COMMUNITY": row.get("COMMUNITY", ""),
                        "COMMUNITY RANK": row.get("COMMUNITY RANK", ""),
                    }
                )

    if not merged_rows:
        raise RuntimeError(f"No records.csv files found under {output_root / BUNDLES_DIRNAME}")

    write_csv(destination, merged_rows, ["YEAR", *STANDARDIZED_HEADERS])
    return destination


def discover_pdfs(input_root: Path) -> list[Path]:
    return sorted(path for path in input_root.glob("GRL-*/*.pdf") if path.is_file())


def command_parse(args: argparse.Namespace) -> int:
    pdf_path = args.pdf.resolve()
    output_root = args.output_root.resolve()
    input_root = args.input_root.resolve()
    meta = parse_pdf(
        pdf_path,
        output_root,
        input_root,
        max_pages=args.max_pages,
        with_audit_files=args.with_audit_files,
    )
    print(json.dumps(meta, indent=2))
    return 0


def command_batch(args: argparse.Namespace) -> int:
    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    pdf_paths = discover_pdfs(input_root)
    if not pdf_paths:
        raise RuntimeError(f"No GRL PDFs found under {input_root}")

    batch_rows: list[dict[str, str]] = []
    for pdf_path in pdf_paths:
        meta = parse_pdf(
            pdf_path,
            output_root,
            input_root,
            max_pages=args.max_pages,
            with_audit_files=args.with_audit_files,
        )
        batch_rows.append({key: str(value) for key, value in meta.items()})
        print(
            f"parsed {pdf_path.name}: {meta['parsed_records']} records, "
            f"errors={meta['parse_error_count']}"
        )

    batch_manifest_path = output_root / REPORTS_DIRNAME / "batch_manifest.csv"
    write_csv(
        batch_manifest_path,
        batch_rows,
        [
            "source_pdf_abs_path",
            "source_pdf_rel_path",
            "pdf_sha256",
            "file_size_bytes",
            "pdf_year",
            "parsed_pages",
            "parsed_records",
            "record_blocks_seen",
            "parse_error_count",
            "non_record_unparsed_line_count",
            "max_general_rank",
            "max_s_no",
            "general_rank_matches_record_count",
            "s_no_matches_record_count",
        ],
    )
    print(f"batch manifest written to {batch_manifest_path}")
    return 0


def command_merge(args: argparse.Namespace) -> int:
    output_root = args.output_root.resolve()
    destination = args.destination.resolve() if args.destination else None
    merged_path = merge_clean_csvs(output_root, destination=destination)
    print(f"merged CSV written to {merged_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse TNEA General Rank List PDFs in this folder into clean CSV outputs."
    )
    parser.set_defaults(func=None)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path.cwd(),
        help="Folder that contains the GRL-<year>/GRL-<year>.pdf inputs. Default: current directory.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd() / "processed",
        help="Destination root for bundles, merged CSVs, and reports. Default: ./processed",
    )

    subparsers = parser.add_subparsers(dest="command")

    parse_parser = subparsers.add_parser("parse", help="Parse a single PDF into one bundle.")
    parse_parser.add_argument("pdf", type=Path, help="Path to one General Rank List PDF.")
    parse_parser.add_argument("--max-pages", type=int, default=None, help="Parse only the first N pages.")
    parse_parser.add_argument(
        "--with-audit-files",
        action="store_true",
        help="Also write audit/records_full.csv and audit/unparsed_lines.csv.",
    )
    parse_parser.set_defaults(func=command_parse)

    batch_parser = subparsers.add_parser(
        "batch",
        help="Parse every GRL-<year>/GRL-<year>.pdf under the input root.",
    )
    batch_parser.add_argument("--max-pages", type=int, default=None, help="Parse only the first N pages of each PDF.")
    batch_parser.add_argument(
        "--with-audit-files",
        action="store_true",
        help="Also write audit/records_full.csv and audit/unparsed_lines.csv for each PDF.",
    )
    batch_parser.set_defaults(func=command_batch)

    merge_parser = subparsers.add_parser(
        "merge",
        help="Merge every parsed bundle records.csv into one all-years CSV.",
    )
    merge_parser.add_argument(
        "--destination",
        type=Path,
        default=None,
        help="Optional explicit merged CSV path.",
    )
    merge_parser.set_defaults(func=command_merge)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.func is None:
        parser.print_help(sys.stderr)
        return 2

    try:
        return int(args.func(args))
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
