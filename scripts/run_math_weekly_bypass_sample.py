"""Create the standard offline Math Weekly bypass sample run through the unified runner."""
from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from generate_worksheet import generate_math_weekly


def main() -> int:
    result = generate_math_weekly(
        {
            "subject": "math",
            "worksheettype": "weekly",
            "week": "2026-09-07",
            "gates": "bypass all",
            "render": "no",
            "publish": "no",
            "deliver": "no",
            "delivery_dry_run": "no",
            "run": "run-2026-09-07-weekly-bypass-sample",
        }
    )
    print(
        f"SAMPLE_RUN_PASS {result['run_id']} "
        f"worksheets={result['worksheets']} gates_bypassed={result['gates_bypassed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())