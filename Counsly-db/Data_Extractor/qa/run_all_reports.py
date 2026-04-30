#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "qa/allotement_report.py",
    ROOT / "qa/college_info_report.py",
    ROOT / "qa/grl_report.py",
    ROOT / "qa/geo_report.py",
]


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    for script in SCRIPTS:
        print(f"Running {script.name}...")
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT, env=env)
        if result.returncode != 0:
            return result.returncode
    print("All QA reports generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
