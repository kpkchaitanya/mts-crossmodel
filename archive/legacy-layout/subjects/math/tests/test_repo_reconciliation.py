from pathlib import Path
import json


REPO = Path(__file__).resolve().parents[3]
MATH = REPO / "subjects" / "math"

ROOT_EXPECTED = [
    "AGENTS.md",
    "README.md",
    "constitution.md",
    "specs/generate_math_worksheets/01. intent/requirements.md",
    "specs/generate_math_worksheets/03. design/design.md",
    "config/base.yaml",
    "config/math.yaml",
    "config/ela.yaml",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    "schemas/worksheet-spec.schema.json",
    "schemas/run-manifest.schema.json",
    "schemas/worksheet-type.schema.json",
    "config/worksheet-types/class-worksheet.yaml",
    "config/worksheet-types/weekly-worksheet.yaml",
    "config/worksheet-types/homework-4-day.yaml",
    "config/worksheet-types/compact-unbranded.yaml",
    "templates/by-worksheet-type/template-manifest.json",
    "src/rendering/google_docs_adapter.py",
    "tests/integration/test_google_docs_adapter.py",
    "tests/integration/test_math_class_lifecycle.py",
    "tests/integration/test_weekly_math_lifecycle.py",
]

MATH_EXPECTED = [
    "README.md",
    "requirements.md",
    "MIGRATION.md",
    "docs/curriculum-source-guidance.md",
    "docs/plan.md",
    "config/archive/mts-math-worksheet-config.yaml",
    "config/template-manifest.json",
    "config/template-manifests/weekly-worksheet.json",
    "skills/worksheet-generation.md",
    "skills/verification.md",
    "commands/generate-weekly-classworksheets.md",
    "commands/verify-worksheet.md",
    "templates/template-links.md",
    "knowledge/curriculum/progressive/progressive-math-backbone.json",
    "knowledge/curriculum/nc-math/standards-cache.json",
    "knowledge/curriculum/ccs-2026-2027/pacing.json",
    "knowledge/sources.json",
    "knowledge/grade-course-catalog.json",
    "knowledge/master-data-index.json",
    "schemas/worksheet-spec.schema.json",
    "schemas/run-manifest.schema.json",
    "src/p0_runtime.py",
    "src/subject_module.py",
    "src/weekly_workflow.py",
    "tests/test_subject_module.py",
    "tests/test_weekly_workflow.py",
]


def read_root(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def read_math(rel):
    return (MATH / rel).read_text(encoding="utf-8")


def test_expected_structure():
    missing_root = [p for p in ROOT_EXPECTED if not (REPO / p).exists()]
    missing_math = [p for p in MATH_EXPECTED if not (MATH / p).exists()]
    assert not missing_root, missing_root
    assert not missing_math, missing_math


def test_single_agents_contract():
    active_agents = [p.relative_to(REPO).as_posix() for p in REPO.rglob("AGENTS.md")]
    assert active_agents == ["AGENTS.md"], active_agents
    agents = read_root("AGENTS.md")
    assert "only canonical `AGENTS.md`" in agents
    assert "subjects/math/**" in agents
    assert "subjects/ela/**" in agents


def test_harness_adapters_are_thin():
    copilot = read_root(".github/copilot-instructions.md")
    claude = read_root("CLAUDE.md")
    for adapter in (copilot, claude):
        assert "AGENTS.md" in adapter
        assert "constitution.md" in adapter
        normalized = adapter.lower()
        assert "independent governing" in normalized or "canonical behavior" in normalized


def test_math_config_retains_behavior_paths():
    cfg = read_math("config/archive/mts-math-worksheet-config.yaml")
    for path in [
        "src/p0_runtime.py",
        "schemas/worksheet-spec.schema.json",
        "config/template-manifest.json",
        "knowledge/curriculum/progressive/progressive-math-backbone.json",
        "knowledge/curriculum/ccs-2026-2027/pacing.json",
    ]:
        assert path in cfg
    assert "gate_5_publish: true" in cfg
    weekly = read_root("config/worksheet-types/weekly-worksheet.yaml")
    assert "subjects/math/config/template-manifests/weekly-worksheet.json" in weekly


def test_json_assets_parse():
    math_assets = [
        "config/template-manifest.json",
        "knowledge/sources.json",
        "knowledge/curriculum/progressive/progressive-math-backbone.json",
        "knowledge/curriculum/nc-math/standards-cache.json",
        "knowledge/curriculum/ccs-2026-2027/pacing.json",
        "schemas/worksheet-spec.schema.json",
        "schemas/run-manifest.schema.json",
    ]
    root_assets = [
        "schemas/worksheet-spec.schema.json",
        "schemas/run-manifest.schema.json",
        "schemas/worksheet-type.schema.json",
        "templates/by-worksheet-type/template-manifest.json",
    ]
    for rel in math_assets:
        json.loads(read_math(rel))
    for rel in root_assets:
        json.loads(read_root(rel))


def test_output_folder_semantics():
    config = read_math("config/archive/mts-math-worksheet-config.yaml")
    agents = read_root("AGENTS.md")
    assert 'target_folder_name: "outputs"' in config
    assert 'copilot_dump_folder_name: "outputs-copilot"' in config
    assert "outputs-copilot/" in agents
    assert (REPO / "outputs" / "math").is_dir()
    assert (REPO / "runs" / "math").is_dir()


def main():
    tests = [
        test_expected_structure,
        test_single_agents_contract,
        test_harness_adapters_are_thin,
        test_math_config_retains_behavior_paths,
        test_json_assets_parse,
        test_output_folder_semantics,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
