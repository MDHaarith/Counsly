from __future__ import annotations

from pathlib import Path
import re
import zlib


def decode_hex_string(hex_str: str) -> str:
    """Decode a 4-digit-chunk hex string with +29 shift."""
    clean = re.sub(r"[^0-9A-Fa-f]", "", hex_str or "")
    decoded: list[str] = []
    for i in range(0, len(clean), 4):
        chunk = clean[i : i + 4]
        if len(chunk) < 4:
            continue
        try:
            val = int(chunk, 16)
        except ValueError:
            continue
        if val == 0:
            continue
        char_code = val + 29
        if 0 <= char_code <= 0x10FFFF:
            decoded.append(chr(char_code))
    return "".join(decoded)


def text_quality_score(text: str) -> float:
    """Heuristic score for how 'real' a piece of decoded text is."""
    if not text or not text.strip():
        return 0.0
    sample = text[:8000]
    length = max(len(sample), 1)
    printable = sum(1 for c in sample if c.isprintable()) / length
    alpha = sum(1 for c in sample if c.isalpha()) / length
    spaces = sample.count(" ") / length
    keywords = ["ENGINEERING", "COLLEGE", "UNIVERSITY", "TECHNOLOGY", "DISTRICT"]
    kw_hits = sum(1 for kw in keywords if kw in sample) * 0.08
    return printable + alpha + spaces + kw_hits


def extract_blocks_from_pdf(pdf_path: str | Path, *, quality_threshold: float = 0.0) -> list[str]:
    """Extract decoded text blocks from a PDF using the raw stream parser."""
    path = Path(pdf_path)
    with path.open("rb") as f:
        data = f.read()

    blocks: list[str] = []
    idx = 0
    stream_count = 0

    while stream_count < 3000:
        idx = data.find(b"stream", idx)
        if idx == -1:
            break
        idx += 6
        start = idx
        if start + 2 <= len(data) and data[start : start + 2] == b"\r\n":
            start += 2
        elif start + 1 <= len(data) and data[start : start + 1] in (b"\n", b"\r"):
            start += 1

        try:
            decompressed = zlib.decompressobj().decompress(data[start : start + 5_000_000])
        except Exception:
            idx += 1
            stream_count += 1
            continue

        text_objects = re.findall(b"BT(.*?)ET", decompressed, re.DOTALL)
        if not text_objects and (b"Tj" in decompressed or b"TJ" in decompressed):
            text_objects = [decompressed]

        for obj in text_objects:
            parts = re.split(b"(<[0-9A-Fa-f]+>)", obj)
            text_parts: list[str] = []
            for part in parts:
                if part.startswith(b"<") and part.endswith(b">"):
                    decoded = decode_hex_string(part[1:-1].decode("ascii", errors="ignore"))
                    if decoded:
                        text_parts.append(decoded)
                else:
                    for m in re.findall(rb"\((.*?)\)", part):
                        text_parts.append(
                            m.replace(b"\\(", b"(").replace(b"\\)", b")").decode("latin1", errors="ignore")
                        )
            candidate = "".join(text_parts).strip()
            if not candidate:
                continue
            if quality_threshold > 0.0 and text_quality_score(candidate) <= quality_threshold:
                continue
            blocks.append(candidate)

        idx += 1
        stream_count += 1

    return blocks
