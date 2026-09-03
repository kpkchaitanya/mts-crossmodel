import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.extend([str(REPO / "src" / "runtime"), str(REPO / "subjects" / "math" / "src")])

import gates
import run_repository
import subject_module

RUN_ID = "run-6a70560dea0c4f8eb92173e99d32722d"
RUNS = REPO / "runs"


def main():
    repository = run_repository.RunRepository(RUNS)
    manifest_path = RUNS / "math" / RUN_ID / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for reference in manifest["spec_references"]:
        revision = f"{reference['worksheet_id']}-questions-r1"
        already_approved = any(
            approval.get("gate") == "question_review"
            and approval.get("artifact_revision") == revision
            for approval in manifest.get("approvals", [])
        )
        if not already_approved:
            manifest = gates.record_approval(
                manifest,
                gate="question_review",
                artifact_revision=revision,
                status="approved",
                reviewer="current_user",
                notes="User approved Question Review on 2026-08-30.",
            )
        gates.require_question_review(manifest, artifact_revision=revision)

    math = subject_module.MathSubjectModule(REPO / "subjects" / "math")
    results = {}
    for reference in manifest["spec_references"]:
        spec = json.loads((RUNS / reference["spec_path"]).read_text(encoding="utf-8"))
        result = math.verify_spec(spec)
        if result["status"] != "PASS":
            raise RuntimeError(f"Formal verification failed for {reference['worksheet_id']}: {result}")
        results[reference["worksheet_id"]] = result

    manifest["status"] = "verification_in_progress"
    manifest["verification"] = {"revision": "verification-2026-08-31-r1", "results": results}
    repository.save_manifest(manifest)
    summary = {
        grade: {
            "status": result["status"],
            "questions": result["questions"],
            "deterministic_checked": result["deterministic_checked"],
            "reasoning_required": result["reasoning_required"],
            "failures": result["failures"],
        }
        for grade, result in results.items()
    }
    print(json.dumps({"run_id": RUN_ID, "status": manifest["status"], "verification": summary}, indent=2))


if __name__ == "__main__":
    main()