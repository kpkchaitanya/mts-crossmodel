import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO / "scripts"))

import render_weekly_specs_to_drive as renderer

RUN_ID = "run-6a70560dea0c4f8eb92173e99d32722d"


def main():
    run_root = REPO / "runs" / "math" / RUN_ID
    manifest = json.loads((run_root / "run-manifest.json").read_text(encoding="utf-8"))
    for reference in manifest["spec_references"]:
        spec = json.loads((REPO / "runs" / reference["spec_path"]).read_text(encoding="utf-8"))
        student_projection = renderer.projection(spec, False)
        answer_key_projection = renderer.projection(spec, True)
        if "Monday" not in student_projection or "Friday" not in student_projection:
            raise RuntimeError(f"Missing weekly section title in {reference['worksheet_id']} student projection.")
        if "ANSWER KEY" not in answer_key_projection:
            raise RuntimeError(f"Missing answer-key heading in {reference['worksheet_id']} projection.")
    print("RENDER_PREFLIGHT_PASS")


if __name__ == "__main__":
    main()