"""Focused tests for target immutable Worksheet Spec loader/writer behavior."""
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from mts.worksheets.spec_loader import SpecLoader
from mts.worksheets.spec_writer import SpecWriteError, SpecWriter


def sample_spec():
    return {
        "worksheet": {"grade": "Grade 4", "week_start": "2026-09-07", "question_count": 1},
        "sections": [{"id": "monday", "questions": [{"number": 1, "prompt": "Find 2 + 2.", "answer": 4}]}],
        "verification": {"status": "PENDING"},
    }


def test_spec_writer_and_loader_use_entity_hierarchy_and_reject_overwrite(tmp_path):
    identity = {
        "subject": "math",
        "grade": "grade_4",
        "cycle_id": "2026-09-07",
        "batch_id": "weekly_math_sample",
        "worksheet_type": "weekly_worksheet",
        "revision": 1,
    }
    writer = SpecWriter(tmp_path)
    loader = SpecLoader(tmp_path)
    path = writer.write_revision(sample_spec(), **identity)

    assert path.relative_to(tmp_path).as_posix() == (
        "transactions/subjects/math/grades/grade_4/cycles/2026-09-07/"
        "batches/weekly_math_sample/worksheets/weekly_worksheet/specs/r1.json"
    )
    assert loader.load_revision(**identity) == sample_spec()

    changed = sample_spec()
    changed["sections"][0]["questions"][0]["answer"] = 5
    try:
        writer.write_revision(changed, **identity)
    except SpecWriteError as error:
        assert "Refusing to overwrite" in str(error)
    else:
        raise AssertionError("A Spec revision must not be overwritten.")
