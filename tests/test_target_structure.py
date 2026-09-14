from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_target_source_capability_packages_exist():
    expected = [
        "setup_project",
        "curriculum",
        "instructional_cycles",
        "worksheets",
        "verification",
        "publishing",
        "template_management",
        "workflow_management",
        "subjects/math",
        "infrastructure/configuration",
        "infrastructure/file_system",
        "infrastructure/google_docs",
    ]
    missing = [path for path in expected if not (REPO / "src" / "mts" / path / "__init__.py").is_file()]
    assert not missing, missing


def test_target_test_subject_package_exists():
    assert (REPO / "tests" / "subjects" / "math" / "test_target_package_imports.py").is_file()


def test_legacy_active_roots_are_retired():
    retired = [
        "subjects",
        "config",
        "templates",
        "runs",
        "src/runtime",
        "src/rendering",
        "src/curriculum",
        "src/verification",
    ]
    still_active = [path for path in retired if (REPO / path).exists()]
    assert not still_active, still_active
