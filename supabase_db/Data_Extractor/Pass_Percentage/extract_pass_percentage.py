"""
General-purpose Pass Percentage PDF Extractor for Anna University exam result PDFs.

Works with any "PERCENTAGE OF STUDENTS PASSED IN UNIVERSITY EXAMINATIONS" PDF
from Anna University, regardless of exam period (April/May, Nov/Dec, etc.).

Handles the custom hex-encoded PDFs where numbers are concatenated without
spaces. Uses constraint-based splitting to recover individual values.

Usage:
    python extract_pass_percentage.py
    python extract_pass_percentage.py /path/to/specific.pdf
    python extract_pass_percentage.py /path/to/folder/with/pdfs
"""

from __future__ import annotations

import json
import os
import re
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tnea_lib.raw_stream import decode_hex_string, extract_blocks_from_pdf, text_quality_score

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PDF text extraction (shared raw stream parser)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Number splitting utilities
# ---------------------------------------------------------------------------

def split_main_number_line(num_str: str) -> Tuple[int, int, float]:
    """Split concatenated appeared+passed+pass% into components.

    Example: "87448455.38" -> (874, 484, 55.38)

    Strategy: scan every position for a valid pass percentage (0-100 float),
    then try splitting the prefix into appeared+passed using the ratio constraint.
    """
    for pos in range(len(num_str)):
        pct_match = re.match(r"(\d{1,3}\.\d{1,2})", num_str[pos:])
        if not pct_match:
            continue
        pass_pct = float(pct_match.group(1))
        if not (0 <= pass_pct <= 100):
            continue

        prefix = num_str[:pos]

        # No prefix means 0 appeared, 0 passed (e.g., "0.00")
        if not prefix:
            return 0, 0, pass_pct

        # Try every split point of prefix into appeared + passed
        for i in range(1, len(prefix)):
            try:
                a = int(prefix[:i])
                b = int(prefix[i:])
            except ValueError:
                continue
            if a <= 0 or b > a:
                continue
            if abs(b / a * 100.0 - pass_pct) < 0.015:
                return a, b, pass_pct

    # Fallback: couldn't find valid split
    return 0, 0, 0.0


def find_sem_split(
    s: str, total_app: int, total_pass: int, n_sems: int
) -> Optional[List[Tuple[int, int]]]:
    """Backtracking solver to split concatenated semester data.

    Constraint: sum of appeared values = total_app,
                sum of passed values = total_pass,
                passed <= appeared per semester.
    """
    results: List[List[Tuple[int, int]]] = []

    def backtrack(
        sem_idx: int,
        remaining: str,
        app_sum: int,
        pass_sum: int,
        sems: List[Tuple[int, int]],
    ) -> None:
        if sem_idx == n_sems:
            if not remaining and app_sum == total_app and pass_sum == total_pass:
                results.append(list(sems))
            return

        if not remaining:
            if app_sum == total_app and pass_sum == total_pass:
                results.append(list(sems) + [(0, 0)] * (n_sems - sem_idx))
            return

        # Try app/pass pairs for this semester (max 4 digits each)
        for app_end in range(1, min(len(remaining) + 1, 5)):
            app_s = remaining[:app_end]
            if app_s.startswith("0") and len(app_s) > 1:
                continue
            app_val = int(app_s)
            if app_sum + app_val > total_app:
                break

            rest = remaining[app_end:]
            if not rest:
                if pass_sum == total_pass and app_sum + app_val == total_app:
                    results.append(
                        list(sems) + [(app_val, 0)]
                        + [(0, 0)] * (n_sems - sem_idx - 1)
                    )
                continue

            for pass_end in range(1, min(len(rest) + 1, 5)):
                pass_s = rest[:pass_end]
                if pass_s.startswith("0") and len(pass_s) > 1:
                    continue
                pass_val = int(pass_s)
                if pass_sum + pass_val > total_pass:
                    break
                if pass_val > app_val:
                    continue

                sems.append((app_val, pass_val))
                backtrack(sem_idx + 1, rest[pass_end:], app_sum + app_val, pass_sum + pass_val, sems)
                sems.pop()

        # Also try 0/0 for this semester (skip)
        sems.append((0, 0))
        backtrack(sem_idx + 1, remaining, app_sum, pass_sum, sems)
        sems.pop()

    backtrack(0, s, 0, 0, [])
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Block classification
# ---------------------------------------------------------------------------

SERIAL_CODE_RE = re.compile(r"^(\d{1,3})(\d{4})$")
HAS_DECIMAL_RE = re.compile(r"\d+\.\d+")
ALL_DIGITS_RE = re.compile(r"^\d+$")
SEM_HEADER_RE = re.compile(r"SEM\s+(\d+)")
EXAM_PERIOD_RE = re.compile(
    r"(APRIL\s*/\s*MAY\s+\d{4}|NOVEMBER\s*/\s*DECEMBER\s+\d{4})"
)
HEADER_KEYWORDS = {
    "ANNA UNIVERSITY",
    "PERCENTAGE OF STUDENTS PASSED",
    "B.E./ B.Tech. DEGREE PROGRAMMES",
    "NON-AUTONOMOUS AFFILIATED COLLEGES",
    "Number of Students in Each Semester",
}
SKIP_PATTERNS = [
    re.compile(r"^Sl\."),
    re.compile(r"^No\."),
    re.compile(r"^TNEA$"),
    re.compile(r"^Code$"),
    re.compile(r"^Name of the College"),
    re.compile(r"^District$"),
    re.compile(r"^Total$"),
    re.compile(r"^Appeared$"),
    re.compile(r"^Passed$"),
    re.compile(r"^% of$"),
    re.compile(r"^Pass$"),
    re.compile(r"^SEM\s+\d"),
    re.compile(r"^Appd\.?\s*Pass"),
]


def is_skip_block(block: str) -> bool:
    """Check if a text block is header/footer noise."""
    for kw in HEADER_KEYWORDS:
        if kw in block:
            return True
    for pat in SKIP_PATTERNS:
        if pat.search(block):
            return True
    return False


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def extract_pass_percentage(pdf_path: str) -> List[Dict[str, Any]]:
    """Main extraction function for a single PDF."""
    logger.info("Processing: %s", pdf_path)
    blocks = extract_blocks_from_pdf(pdf_path, quality_threshold=0.75)
    logger.info("Extracted %d text blocks", len(blocks))

    # Phase 1: detect semester structure and exam period from headers
    exam_period = ""
    sem_labels: List[str] = []

    for block in blocks:
        m = EXAM_PERIOD_RE.search(block)
        if m:
            exam_period = m.group(1).strip()
        for sm in SEM_HEADER_RE.finditer(block):
            sem_labels.append(f"SEM {sm.group(1)}")

    # Deduplicate and sort semester labels
    seen_sems: set = set()
    unique_labels: List[str] = []
    for label in sem_labels:
        if label not in seen_sems:
            seen_sems.add(label)
            unique_labels.append(label)
    sem_labels = sorted(unique_labels, key=lambda x: int(x.split()[-1]))

    n_sems = len(sem_labels) if sem_labels else 4
    if not sem_labels:
        sem_labels = [f"SEM {i}" for i in range(2, 2 + n_sems)]

    logger.info("Exam period: %s, Semesters: %s", exam_period, sem_labels)

    # Phase 2: parse college entries
    entries: List[Dict[str, Any]] = []
    seen_keys: set = set()
    idx = 0

    while idx < len(blocks):
        block = blocks[idx]

        if is_skip_block(block):
            idx += 1
            continue

        m = SERIAL_CODE_RE.match(block)
        if not m:
            idx += 1
            continue

        serial_no = int(m.group(1))
        college_code = int(m.group(2))

        # Collect subsequent blocks for this entry
        text_parts: List[str] = []
        main_num_line: Optional[str] = None
        sem_num_line: Optional[str] = None
        consumed = 1
        j = idx + 1

        while j < len(blocks):
            b = blocks[j]
            if SERIAL_CODE_RE.match(b):
                break
            if "ANNA UNIVERSITY" in b:
                break
            if is_skip_block(b):
                j += 1
                consumed += 1
                continue
            if HAS_DECIMAL_RE.search(b) and main_num_line is None:
                main_num_line = b
            elif ALL_DIGITS_RE.match(b) and main_num_line is not None:
                sem_num_line = b
            else:
                text_parts.append(b)
            j += 1
            consumed += 1

        idx += consumed

        if not text_parts or main_num_line is None:
            continue

        # Split name and district
        college_name, district = split_name_district(text_parts)

        # Parse numbers
        appeared, passed, pass_pct = split_main_number_line(main_num_line)
        if appeared == 0 and passed == 0 and pass_pct == 0.0:
            continue

        # Parse semester data
        pairs = find_sem_split(sem_num_line or "", appeared, passed, n_sems)
        semesters: Dict[str, Dict[str, int]] = {}
        for i, label in enumerate(sem_labels):
            if pairs and i < len(pairs):
                semesters[label] = {"appeared": pairs[i][0], "passed": pairs[i][1]}
            else:
                semesters[label] = {"appeared": 0, "passed": 0}

        key = (serial_no, college_code)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        entries.append({
            "serial_no": serial_no,
            "college_code": college_code,
            "college_name": college_name,
            "district": district,
            "total_appeared": appeared,
            "total_passed": passed,
            "overall_pass_percentage": pass_pct,
            "exam_period": exam_period,
            "semesters": semesters,
            "source_file": os.path.basename(pdf_path),
        })

    logger.info("Extracted %d college entries", len(entries))
    return entries


def split_name_district(text_parts: List[str]) -> Tuple[str, str]:
    """Split text parts into (college_name, district)."""
    if not text_parts:
        return "", ""
    if len(text_parts) == 1:
        return text_parts[0], ""

    district = text_parts[-1].strip()
    name_keywords = ("COLLEGE", "ENGINEERING", "TECHNOLOGY", "INSTITUTE", "UNIVERSITY")
    if any(kw in district.upper() for kw in name_keywords):
        name = " ".join(text_parts)
        return re.sub(r"\s+", " ", name).strip(), ""

    name = " ".join(text_parts[:-1])
    return re.sub(r"\s+", " ", name).strip(), district


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def process_pdf(pdf_path: str, output_dir: str) -> None:
    """Process a single PDF and save JSON output."""
    entries = extract_pass_percentage(pdf_path)
    if not entries:
        logger.warning("No entries extracted from %s", pdf_path)
        return

    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(output_dir, f"{basename}.json")
    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    logger.info("Saved %d entries to %s", len(entries), output_path)


def main() -> None:
    """Entry point."""
    # Default: process all PDFs in the current directory
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    if os.path.isfile(target):
        pdfs = [target]
        if output_dir == "output":
            output_dir = "output"
    elif os.path.isdir(target):
        pdfs = sorted(
            os.path.join(target, f)
            for f in os.listdir(target)
            if f.lower().endswith(".pdf")
        )
    else:
        logger.error("Path not found: %s", target)
        sys.exit(1)

    if not pdfs:
        logger.error("No PDF files found in %s", target)
        sys.exit(1)

    logger.info("Found %d PDF(s) to process", len(pdfs))
    for pdf_path in pdfs:
        try:
            process_pdf(pdf_path, output_dir)
        except Exception as exc:
            logger.error("Failed to process %s: %s", pdf_path, exc)
            raise

    logger.info("Done!")


if __name__ == "__main__":
    main()
