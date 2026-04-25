"""
Universal Seat Matrix Extractor — Dual-mode parser.

Automatically detects and handles both:
  - Text-based PDFs (via pdfplumber)
  - Scanned/image-based PDFs (via PyMuPDF + Tesseract OCR)

Usage:
  python3 extractor.py                              # Auto-detect PDFs in current dir
  python3 extractor.py path/to/file.pdf             # Single PDF
  python3 extractor.py path/to/folder/              # All PDFs in folder
"""

import json
import os
import re
import sys
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    pytesseract = None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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
    digits = re.sub(r"\D", "", str(value))
    return int(digits) if digits else 0


def build_record(
    cells: List[str], row_counter: int, pdf_name: str, timestamp: str
) -> Optional[Dict[str, Any]]:
    """Build a single record dict from a list of cell strings."""
    while len(cells) < 11:
        cells.append("0")

    college_code = parse_int(cells[0])
    if college_code == 0:
        return None

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

    return {
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
        "source_file": pdf_name,
        "extraction_date": timestamp,
    }


def is_header_row(cells: List[str]) -> bool:
    """Check if a row is a header (not data)."""
    first = clean_cell(cells[0]).upper()
    return "COLLEGE" in first or "CODE" in first or not clean_cell(cells[0]).isdigit()


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------

def detect_pdf_mode(pdf_path: str) -> str:
    """
    Detect whether a PDF is text-based or scanned.

    Tries pdfplumber text extraction on the first page.
    If text is sparse or empty, classifies as scanned.
    """
    if pdfplumber is None:
        if fitz is not None:
            return "scanned"
        print("Error: Neither pdfplumber nor PyMuPDF available.")
        sys.exit(1)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return "scanned"
            text = pdf.pages[0].extract_text() or ""
            # Check if we get meaningful text
            alpha_chars = sum(1 for c in text if c.isalpha())
            if alpha_chars > 50:
                return "text"
            return "scanned"
    except Exception:
        return "scanned"


# ---------------------------------------------------------------------------
# Text-based extraction (pdfplumber)
# ---------------------------------------------------------------------------

def extract_from_text_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract seat matrix rows from a text-based PDF using pdfplumber."""
    if pdfplumber is None:
        print("Error: pdfplumber not installed. Run: pip install pdfplumber")
        return []

    timestamp = datetime.now().isoformat(timespec="seconds")
    pdf_name = os.path.basename(pdf_path)
    records: List[Dict[str, Any]] = []
    row_counter = 0

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing {total_pages} pages (text mode)...")

        for page_num, page in enumerate(pdf.pages, 1):
            table = page.extract_table()
            if not table:
                continue

            for row in table:
                cells = [clean_cell(c) for c in row]
                if is_header_row(cells):
                    continue

                row_counter += 1
                record = build_record(cells, row_counter, pdf_name, timestamp)
                if record:
                    records.append(record)

            if page_num % 50 == 0:
                print(f"  Page {page_num}/{total_pages} — {row_counter} rows so far")

    return records


# ---------------------------------------------------------------------------
# Scanned/image-based extraction (PyMuPDF + Tesseract OCR)
# ---------------------------------------------------------------------------

def preprocess_image(img: Image.Image) -> Image.Image:
    """Preprocess a page image for better OCR accuracy."""
    # Convert to grayscale
    img = img.convert("L")
    # Increase contrast with auto-contrast
    from PIL import ImageOps
    img = ImageOps.autocontrast(img, cutoff=2)
    # Scale up for better OCR (if small)
    w, h = img.size
    if w < 2000:
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    # Binarize (threshold to black & white)
    img = img.point(lambda x: 255 if x > 140 else 0, "1")
    return img.convert("RGB")


def parse_ocr_page_text(text: str) -> List[List[str]]:
    """
    Parse OCR'd text from a seat matrix page into rows of cell values.

    Tries to identify the 11-column structure:
    college_code, college_name, branch_code, branch_name, oc, bc, bcm, mbc, sc, sca, st
    """
    rows: List[List[str]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        # Skip title/header lines
        upper = line.upper()
        if any(kw in upper for kw in [
            "TAMILNADU", "DIRECTORATE", "GENERAL ACADEMIC", "VACANCY",
            "COLLEGE CODE", "COLLEGE NAME", "BRANCH CODE", "BRANCH NAME",
            "PAGE ", "PAGE:"
        ]):
            continue
        if upper.strip() in ("OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"):
            continue

        # Try to match a data line: starts with a number (college code)
        match = re.match(
            r"^(\d{1,4})\s+"          # college_code
            r"(.+?)\s+"                # college_name (greedy-ish)
            r"([A-Z]{1,4})\s+"         # branch_code
            r"(.+?)\s+"                # branch_name
            r"(\d+)\s+"                # OC
            r"(\d+)\s+"                # BC
            r"(\d+)\s+"                # BCM
            r"(\d+)\s+"                # MBC
            r"(\d+)\s+"                # SC
            r"(\d+)\s+"                # SCA
            r"(\d+)\s*$",              # ST
            line,
        )
        if match:
            rows.append(list(match.groups()))
            continue

        # Fallback: split on multiple spaces and try to extract
        parts = re.split(r"\s{2,}", line)
        if len(parts) >= 6 and parts[0].strip().isdigit():
            # Try to reconstruct 11 columns from parts
            if len(parts) >= 11:
                rows.append([p.strip() for p in parts[:11]])

    return rows


def extract_from_scanned_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract seat matrix rows from a scanned/image-based PDF using OCR."""
    if fitz is None:
        print("Error: PyMuPDF not installed. Run: pip install PyMuPDF")
        return []
    if pytesseract is None:
        print("Error: pytesseract/Pillow not installed. Run: pip install pytesseract Pillow")
        return []

    timestamp = datetime.now().isoformat(timespec="seconds")
    pdf_name = os.path.basename(pdf_path)
    records: List[Dict[str, Any]] = []
    row_counter = 0

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Processing {total_pages} pages (OCR mode)...")

    for page_num in range(total_pages):
        page = doc[page_num]
        # Render at 300 DPI for good OCR quality
        pix = page.get_pixmap(dpi=300)
        img = Image.open(BytesIO(pix.tobytes("png")))

        # Preprocess
        img = preprocess_image(img)

        # OCR
        ocr_text = pytesseract.image_to_string(img, config="--psm 6")

        # Parse OCR text into rows
        parsed_rows = parse_ocr_page_text(ocr_text)

        for cells in parsed_rows:
            cleaned = [clean_cell(c) for c in cells]
            row_counter += 1
            record = build_record(cleaned, row_counter, pdf_name, timestamp)
            if record:
                records.append(record)

        if (page_num + 1) % 10 == 0:
            print(f"  Page {page_num + 1}/{total_pages} — {row_counter} rows so far")

    doc.close()
    return records


# ---------------------------------------------------------------------------
# Unified extraction entry point
# ---------------------------------------------------------------------------

def extract_pdf(pdf_path: str, force_mode: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract seat matrix data from any PDF.

    Args:
        pdf_path: Path to the PDF file.
        force_mode: "text", "scanned", or None (auto-detect).

    Returns:
        List of record dictionaries.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return []

    mode = force_mode or detect_pdf_mode(pdf_path)
    print(f"Detected mode: {mode}")

    if mode == "text":
        return extract_from_text_pdf(pdf_path)
    else:
        return extract_from_scanned_pdf(pdf_path)


# ---------------------------------------------------------------------------
# Output & summary
# ---------------------------------------------------------------------------

def get_output_path(pdf_path: str, output_dir: str) -> str:
    """Derive output JSON path from input PDF name."""
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    # Clean the name for filesystem
    safe_name = re.sub(r"[^A-Za-z0-9_\-]+", "_", stem).lower()
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, f"{safe_name}_data.json")


def print_summary(records: List[Dict[str, Any]], pdf_path: str) -> None:
    """Print extraction summary statistics."""
    if not records:
        print(f"No records extracted from {os.path.basename(pdf_path)}.")
        return

    colleges = set(r["college_code"] for r in records)
    branches = set(r["branch_code"] for r in records)
    total_seats = sum(r["total"] for r in records)

    print(f"\n{'='*50}")
    print(f"  {os.path.basename(pdf_path)}")
    print(f"{'='*50}")
    print(f"  Total rows:       {len(records)}")
    print(f"  Unique colleges:  {len(colleges)}")
    print(f"  Unique branches:  {len(branches)}")
    print(f"  Total vacancies:  {total_seats}")
    print(f"{'='*50}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def find_pdfs_in_dir(directory: str) -> List[str]:
    """Find all PDF files in a directory."""
    pdfs = []
    for f in sorted(os.listdir(directory)):
        if f.lower().endswith(".pdf"):
            pdfs.append(os.path.join(directory, f))
    return pdfs


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")

    # Determine input
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        # Auto-detect PDFs in current directory
        pdfs = find_pdfs_in_dir(script_dir)
        if not pdfs:
            print("No PDF files found. Usage: python3 extractor.py <pdf_or_folder>")
            sys.exit(1)
        if len(pdfs) == 1:
            input_path = pdfs[0]
        else:
            print(f"Found {len(pdfs)} PDFs. Processing all...")
            input_path = None

    # Force mode flag
    force_mode = None
    if "--text" in sys.argv:
        force_mode = "text"
    elif "--ocr" in sys.argv:
        force_mode = "scanned"

    # Collect PDFs to process
    if input_path:
        if os.path.isdir(input_path):
            pdf_list = find_pdfs_in_dir(input_path)
        else:
            pdf_list = [input_path]
    else:
        pdf_list = find_pdfs_in_dir(script_dir)

    if not pdf_list:
        print("No PDF files found to process.")
        sys.exit(1)

    # Process each PDF
    all_results = {}
    for pdf_path in pdf_list:
        print(f"\n{'─'*50}")
        print(f"Extracting: {os.path.basename(pdf_path)}")
        print(f"{'─'*50}")

        records = extract_pdf(pdf_path, force_mode=force_mode)

        if not records:
            print(f"Extraction failed — no records found in {os.path.basename(pdf_path)}")
            continue

        print_summary(records, pdf_path)

        out_path = get_output_path(pdf_path, output_dir)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        print(f"Saved to: {out_path}")
        all_results[os.path.basename(pdf_path)] = len(records)

    # Final summary
    if len(all_results) > 1:
        print(f"\n{'='*50}")
        print("Batch Summary")
        print(f"{'='*50}")
        for name, count in all_results.items():
            print(f"  {name}: {count} records")
        print(f"  Total: {sum(all_results.values())} records from {len(all_results)} files")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
