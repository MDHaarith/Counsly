"""
Standalone extractor for General Academic Seat Matrix PDFs.

Uses pdfplumber to extract tabular data from landscape PDFs
generated via Microsoft Print to PDF from Excel.
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List

try:
    import pdfplumber
except ImportError:
    print("pdfplumber is required. Install with: pip install pdfplumber")
    sys.exit(1)


def clean_cell(cell: str) -> str:
    """Replace newlines in multi-line cells and strip whitespace."""
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell)).strip()


def fix_branch_code(code: str) -> str:
    """Strip leading '- ' artifact from branch codes."""
    if code.startswith("- "):
        return code[2:]
    return code


def parse_int(value: str) -> int:
    """Extract digits and convert to int."""
    digits = re.sub(r"\D", "", value)
    return int(digits) if digits else 0


def extract_seat_matrix(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract all seat matrix rows from a PDF file."""
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return []

    timestamp = datetime.now().isoformat(timespec="seconds")
    records: List[Dict[str, Any]] = []
    row_counter = 0

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing {total_pages} pages...")

        for page_num, page in enumerate(pdf.pages, 1):
            table = page.extract_table()
            if not table:
                continue

            for row in table:
                # Skip header rows (contain "COLLEGE" or "CODE")
                first_cell = clean_cell(row[0])
                if "COLLEGE" in first_cell.upper() or "CODE" in first_cell.upper():
                    continue

                # Clean all cells
                cells = [clean_cell(c) for c in row]

                # Skip rows that don't start with a number (college code)
                if not cells[0].isdigit():
                    continue

                # Pad row to 11 columns if needed
                while len(cells) < 11:
                    cells.append("0")

                college_code = parse_int(cells[0])
                college_name = cells[1]
                branch_code = fix_branch_code(cells[2])
                branch_name = cells[3]
                oc = parse_int(cells[4])
                bc = parse_int(cells[5])
                bcm = parse_int(cells[6])
                mbc = parse_int(cells[7])
                sc = parse_int(cells[8])
                sca = parse_int(cells[9])
                st = parse_int(cells[10])

                row_counter += 1
                records.append({
                    "s_no": row_counter,
                    "college_code": college_code,
                    "college_name": college_name,
                    "branch_code": branch_code,
                    "branch_name": branch_name,
                    "oc": oc,
                    "bc": bc,
                    "bcm": bcm,
                    "mbc": mbc,
                    "sc": sc,
                    "sca": sca,
                    "st": st,
                    "total": oc + bc + bcm + mbc + sc + sca + st,
                    "source_file": os.path.basename(pdf_path),
                    "extraction_date": timestamp,
                })

            if page_num % 50 == 0:
                print(f"  Page {page_num}/{total_pages} — {row_counter} rows so far")

    return records


def print_summary(records: List[Dict[str, Any]]) -> None:
    """Print extraction summary statistics."""
    if not records:
        print("No records extracted.")
        return

    colleges = set(r["college_code"] for r in records)
    branches = set(r["branch_code"] for r in records)
    total_seats = sum(r["total"] for r in records)

    print(f"\n{'='*50}")
    print(f"Extraction Summary")
    print(f"{'='*50}")
    print(f"  Total rows:       {len(records)}")
    print(f"  Unique colleges:  {len(colleges)}")
    print(f"  Unique branches:  {len(branches)}")
    print(f"  Total vacancies:  {total_seats}")
    print(f"{'='*50}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(
        script_dir, "GENERAL_ACADEMIC_SEAT_MATRIX_2025_AFTER_ROUND_1.pdf"
    )

    # Allow passing a different PDF via command line
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]

    print(f"Extracting: {pdf_path}")
    records = extract_seat_matrix(pdf_path)

    if not records:
        print("Extraction failed — no records found.")
        sys.exit(1)

    print_summary(records)

    # Save output
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "seat_matrix_data.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
