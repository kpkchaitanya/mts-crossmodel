"""Integration check for Policy Resolver, Run Repository, and Gate Controller."""
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "runtime"))
import gates
import policy
import run_repository


def test_math_class_run_scope_review_and_invalidation():
    request = {"subject": "math", "worksheet_type": "class-worksheet"}
    resolved_policy = policy.resolve(request, repository_root=REPO)

    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = run_repository.RunRepository(Path(temporary_directory) / "runs")
        manifest = repository.create_or_resume(request, resolved_policy, run_id="run-integration-001")
        approved = gates.record_approval(
            manifest,
            gate="scope_review",
            artifact_revision="scope-grade-6-r1",
            status="approved",
            reviewer="teacher",
        )
        assert gates.require_approval(
            approved,
            gate="scope_review",
            artifact_revision="scope-grade-6-r1",
        ) == "worksheet_prepared"

        invalidated = gates.invalidate(
            approved,
            change="scope",
            reason="Grade 6 weekly curriculum changed.",
        )
        assert invalidated["status"] == "scope_invalidated"
        try:
            gates.require_approval(
                invalidated,
                gate="scope_review",
                artifact_revision="scope-grade-6-r1",
            )
        except gates.GateError as error:
            assert "Stale" in str(error)
        else:
            raise AssertionError("Changed scope must invalidate the previous Scope Review approval.")


def main():
    test_math_class_run_scope_review_and_invalidation()
    print("PASS test_math_class_run_scope_review_and_invalidation")
    print("ALL_PASS 1/1")


if __name__ == "__main__":
    main()
