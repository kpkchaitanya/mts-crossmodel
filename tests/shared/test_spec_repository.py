"""Focused tests for immutable Worksheet Spec persistence."""
from pathlib import Path
import json
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "runtime"))
import spec_repository


def sample_spec():
    return {
        "worksheet": {"grade": "Grade 4", "week_start": "2026-08-24", "question_count": 1, "duration_minutes": 15},
        "curriculum": {"current": ["NC.4.OA.1"], "confidence": "inferred"},
        "sections": [{"id": "monday", "title": "Foundation", "questions": [{
            "number": 1, "prompt": "Find 2 + 2.", "answer": 4, "skill": "arithmetic", "difficulty": "easy",
        }]}],
        "verification": {"status": "PENDING"},
    }


def test_write_revision_persists_json_and_rejects_mutation():
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = spec_repository.SpecRepository(Path(temporary_directory) / "runs")
        manifest = {"run_id": "run-test", "subject": "math"}
        reference = repository.write_revision(manifest, sample_spec(), worksheet_id="grade-4", revision="r1")
        path = Path(temporary_directory) / "runs" / reference["spec_path"]
        assert path.is_file()
        assert json.loads(path.read_text(encoding="utf-8"))["worksheet"]["question_count"] == 1
        repository.write_revision(manifest, sample_spec(), worksheet_id="grade-4", revision="r1")
        changed = sample_spec()
        changed["sections"][0]["questions"][0]["answer"] = 5
        try:
            repository.write_revision(manifest, changed, worksheet_id="grade-4", revision="r1")
        except spec_repository.SpecRepositoryError as error:
            assert "immutable" in str(error)
        else:
            raise AssertionError("A Spec revision must not be overwritten.")


def test_write_revision_rejects_count_mismatch():
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = spec_repository.SpecRepository(Path(temporary_directory) / "runs")
        invalid = sample_spec()
        invalid["worksheet"]["question_count"] = 2
        try:
            repository.write_revision({"run_id": "run-test", "subject": "math"}, invalid, worksheet_id="grade-4", revision="r1")
        except spec_repository.SpecRepositoryError as error:
            assert "question_count" in str(error)
        else:
            raise AssertionError("A Spec count mismatch must be rejected.")


def main():
    tests = [test_write_revision_persists_json_and_rejects_mutation, test_write_revision_rejects_count_mismatch]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()