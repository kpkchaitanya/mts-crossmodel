"""Focused tests for Run Manifest persistence and safe resume."""
from pathlib import Path
import json
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "runtime"))
import policy
import run_repository


def resolved_class_policy():
    return policy.resolve(
        {"subject": "math", "worksheet_type": "class-worksheet"},
        repository_root=REPO,
    )


def test_new_run_persists_manifest_and_policy_separately():
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = run_repository.RunRepository(Path(temporary_directory) / "runs")
        manifest = repository.create_or_resume(
            {"subject": "math", "worksheet_type": "class-worksheet"},
            resolved_class_policy(),
            run_id="run-test-001",
        )
        run_dir = Path(temporary_directory) / "runs" / "math" / "run-test-001"
        assert manifest["status"] == "initialized"
        assert manifest["policy_snapshot_path"] == "resolved-policy.json"
        assert manifest["spec_references"] == []
        assert (run_dir / "run-manifest.json").is_file()
        assert (run_dir / "resolved-policy.json").is_file()
        persisted_policy = json.loads((run_dir / "resolved-policy.json").read_text(encoding="utf-8"))
        assert persisted_policy["worksheet_type_id"] == "class-worksheet"
        assert "questions" not in manifest


def test_compatible_run_resumes_and_checkpoint_persists():
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = run_repository.RunRepository(Path(temporary_directory) / "runs")
        request = {"subject": "math", "worksheet_type": "class-worksheet"}
        created = repository.create_or_resume(request, resolved_class_policy(), run_id="run-test-002")
        resumed = repository.create_or_resume(request, resolved_class_policy(), run_id="run-test-002")
        assert resumed["started_at"] == created["started_at"]
        checkpointed = repository.add_checkpoint("run-test-002", "math", "scope_resolved")
        assert checkpointed["checkpoints"][0]["name"] == "scope_resolved"


def test_changed_request_or_policy_rejects_resume():
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = run_repository.RunRepository(Path(temporary_directory) / "runs")
        request = {"subject": "math", "worksheet_type": "class-worksheet"}
        repository.create_or_resume(request, resolved_class_policy(), run_id="run-test-003")

        changed_request = {"subject": "math", "worksheet_type": "class-worksheet", "grade": "grade_6"}
        try:
            repository.create_or_resume(changed_request, resolved_class_policy(), run_id="run-test-003")
        except run_repository.RunRepositoryError as error:
            assert "request" in str(error)
        else:
            raise AssertionError("Changed request must not resume an existing run.")

        changed_policy = policy.resolve(
            {"subject": "math", "worksheet_type": "class-worksheet", "overrides": {"duration_minutes": 20}},
            repository_root=REPO,
        )
        try:
            repository.create_or_resume(request, changed_policy, run_id="run-test-003")
        except run_repository.RunRepositoryError as error:
            assert "policy" in str(error)
        else:
            raise AssertionError("Changed policy must not resume an existing run.")


def main():
    tests = [
        test_new_run_persists_manifest_and_policy_separately,
        test_compatible_run_resumes_and_checkpoint_persists,
        test_changed_request_or_policy_rejects_resume,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
