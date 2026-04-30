#!/usr/bin/env python3
"""
Standalone launcher for the honest TNEA college ranking algorithm.

This is a separate storage entrypoint that delegates to the canonical ranking
implementation under scripts/, so the working algorithm is preserved in one
place and can still be run from this isolated folder.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[1]
CANONICAL_SCRIPT = PROJECT_ROOT / "scripts" / "college_ranking.py"


def _load_canonical_main():
    spec = importlib.util.spec_from_file_location(
        "canonical_college_ranking",
        CANONICAL_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load canonical ranking script: {CANONICAL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def main() -> int:
    return _load_canonical_main()()


if __name__ == "__main__":
    raise SystemExit(main())
