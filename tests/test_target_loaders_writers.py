from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def test_run_loader_writer_round_trip(tmp_path):
    from mts.workflow_management.run_loader import RunLoader
    from mts.workflow_management.run_writer import RunWriter

    writer = RunWriter(tmp_path)
    loader = RunLoader(tmp_path)
    manifest = {"run_id": "run-test", "status": "initialized"}
    writer.write_manifest(manifest)
    writer.write_effective_config("run-test", {"subject": "math"})
    writer.write_entity_references("run-test", {"references": []})

    assert loader.load_manifest("run-test") == manifest
    assert loader.load_effective_config("run-test") == {"subject": "math"}
    assert loader.load_entity_references("run-test") == {"references": []}


def test_spec_writer_refuses_to_overwrite_revision(tmp_path):
    from mts.worksheets.spec_loader import SpecLoader
    from mts.worksheets.spec_writer import SpecWriteError, SpecWriter

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
    spec = {"worksheet": {"grade": "grade_4"}, "sections": []}
    writer.write_revision(spec, **identity)
    assert loader.load_revision(**identity) == spec

    try:
        writer.write_revision({"changed": True}, **identity)
    except SpecWriteError as error:
        assert "Refusing to overwrite" in str(error)
    else:
        raise AssertionError("Immutable Spec revisions must not be overwritten.")