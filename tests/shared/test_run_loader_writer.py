"""Focused tests for target Run Manifest loader/writer behavior."""
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from mts.setup_project.configure import resolve_effective_config
from mts.workflow_management.run_loader import RunLoader
from mts.workflow_management.run_writer import RunWriteError, RunWriter


def test_run_writer_and_loader_persist_manifest_effective_config_and_references(tmp_path):
    request = {"subject": "math", "worksheet_type": "class-worksheet"}
    effective_config = resolve_effective_config(request, repository_root=REPO)
    writer = RunWriter(tmp_path)
    loader = RunLoader(tmp_path)
    manifest = {
        "run_id": "run-test-001",
        "subject": "math",
        "worksheet_type": "class-worksheet",
        "status": "initialized",
    }

    writer.write_manifest(manifest)
    writer.write_effective_config("run-test-001", effective_config)
    writer.write_entity_references("run-test-001", {"references": []})

    assert loader.load_manifest("run-test-001") == manifest
    assert loader.load_effective_config("run-test-001")["worksheet_type_id"] == "class-worksheet"
    assert loader.load_entity_references("run-test-001") == {"references": []}


def test_run_writer_requires_manifest_identity(tmp_path):
    writer = RunWriter(tmp_path)
    try:
        writer.write_manifest({"status": "initialized"})
    except RunWriteError as error:
        assert "run_id" in str(error)
    else:
        raise AssertionError("Run Manifest must include run_id.")
