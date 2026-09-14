from pathlib import Path
import json

import yaml


REPO = Path(__file__).resolve().parents[1]


def test_target_config_layout_exists_and_parses():
    expected_yaml = [
        "data/config/project/base.yaml",
        "data/config/subjects/math.yaml",
        "data/config/subjects/ela.yaml",
        "data/config/worksheet_types/weekly_worksheet.yaml",
        "data/config/worksheet_types/class_worksheet.yaml",
        "data/config/worksheet_types/homework_4_day.yaml",
        "data/config/worksheet_types/compact_unbranded.yaml",
    ]
    for relative_path in expected_yaml:
        path = REPO / relative_path
        assert path.is_file(), relative_path
        assert isinstance(yaml.safe_load(path.read_text(encoding="utf-8")) or {}, dict)


def test_target_master_layout_exists_and_parses():
    expected_json = [
        "data/master/subjects/math/grade_course_catalog.json",
        "data/master/subjects/math/master_data_index.json",
        "data/master/subjects/math/question_form_compatibility.json",
        "data/master/subjects/math/curriculum_sources.json",
        "data/master/subjects/math/curriculum/ccs-2026-2027/pacing.json",
        "data/master/subjects/math/curriculum/nc-math/standards-cache.json",
        "data/master/subjects/math/curriculum/progressive/progressive-math-backbone.json",
        "data/master/subjects/math/template_manifests/weekly-worksheet.json",
        "data/master/templates/registry.json",
    ]
    for relative_path in expected_json:
        path = REPO / relative_path
        assert path.is_file(), relative_path
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


def test_target_template_registry_manifest_references_resolve():
    registry_path = REPO / "data" / "master" / "templates" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    active_entries = [entry for entry in registry["entries"] if entry.get("status") == "active"]
    assert active_entries
    for entry in active_entries:
        manifest_path = entry["manifest_path"]
        assert not manifest_path.startswith("../../subjects/"), manifest_path
        assert (registry_path.parent / manifest_path).resolve().is_file(), manifest_path


def test_target_transaction_sample_layout_exists():
    run_root = REPO / "data" / "transactions" / "runs" / "run-2026-09-07-weekly-bypass-sample"
    assert (run_root / "run_manifest.json").is_file()
    assert (run_root / "effective_config.json").is_file()
    assert (run_root / "entity_references.json").is_file()
