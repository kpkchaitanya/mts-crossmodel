"""Integration check for Effective Config Resolver, Run Loader/Writer, and Gate Controller."""
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.setup_project.configure import resolve_effective_config
from mts.workflow_management import gates
from mts.workflow_management.run_writer import RunWriter


def test_math_class_run_scope_review_and_invalidation():
    request = {"subject": "math", "worksheet_type": "class-worksheet"}
    effective_config = resolve_effective_config(request, repository_root=REPO)

    with tempfile.TemporaryDirectory() as temporary_directory:
        writer = RunWriter(Path(temporary_directory) / "data")
        writer.write_effective_config("run-integration-001", effective_config)
        manifest = {"run_id": "run-integration-001", "subject": "math", "worksheet_type": "class-worksheet", "status": "initialized", "approvals": []}
        writer.write_manifest(manifest)
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
        writer.write_manifest(invalidated)
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
