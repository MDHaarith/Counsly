from __future__ import annotations

import zlib
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tnea_lib.raw_stream import (
    decode_hex_string,
    extract_blocks_from_pdf,
    text_quality_score,
)


def test_decode_hex_string_decodes_and_skips_zero_chunks() -> None:
    assert decode_hex_string("0024zzzz00000025") == "AB"


def test_text_quality_score_blank_text_is_zero() -> None:
    assert text_quality_score("   ") == 0.0


def test_extract_blocks_from_pdf_decodes_hex_and_ascii(tmp_path: Path) -> None:
    stream_payload = b"BT <00240025> ( COLLEGE ) ET"
    compressed = zlib.compress(stream_payload)
    pdf_bytes = b"%PDF-1.4\nstream\n" + compressed + b"\nendstream\n"

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(pdf_bytes)

    blocks = extract_blocks_from_pdf(pdf_path)

    assert len(blocks) == 1
    assert "AB" in blocks[0]
    assert "COLLEGE" in blocks[0]


def test_extract_blocks_from_pdf_respects_quality_threshold(tmp_path: Path) -> None:
    stream_payload = b"BT <0024> ET"
    compressed = zlib.compress(stream_payload)
    pdf_bytes = b"%PDF-1.4\nstream\n" + compressed + b"\nendstream\n"

    pdf_path = tmp_path / "low_quality.pdf"
    pdf_path.write_bytes(pdf_bytes)

    blocks = extract_blocks_from_pdf(pdf_path, quality_threshold=2.5)

    assert blocks == []
