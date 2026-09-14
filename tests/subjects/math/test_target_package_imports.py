from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))


def test_effective_config_resolver_uses_target_package_name():
    from mts.setup_project.configure import resolve_effective_config

    resolved = resolve_effective_config(
        {"subject": "math", "worksheet_type": "weekly-worksheet"},
        repository_root=REPO,
    )
    assert resolved["subject"] == "math"
    assert resolved["worksheet_type_id"] == "weekly-worksheet"
    assert resolved["template_selection"]["template_registry"] == "data/master/templates/registry.json"
    assert resolved["template_selection"]["template_manifest"] == "data/master/subjects/math/template_manifests/weekly-worksheet.json"


def test_math_subject_behavior_is_available_from_target_package():
    from mts.subjects.math.generation import MathGeneration

    math = MathGeneration()
    scope = math.resolve_curriculum({"grade_or_course": "grade_6", "on_date": "2026-09-07"})
    assert scope["grade_or_course"] == "grade_6"
    assert "week_start" in scope

    plan = math.build_week_plan(
        sections=[{"id": "monday"}, {"id": "tuesday"}],
        primary_skills=["ratios", "unit_rates"],
        spiral_skills=["fractions"],
        slots_per_day=4,
        difficulty="medium_plus",
        diversity="medium",
    )
    assert set(plan) == {"monday", "tuesday"}
    assert len(plan["monday"]) == 4


def test_gate_and_run_loader_writer_imports_use_target_package():
    from mts.workflow_management.gates import record_approval, require_approval
    from mts.workflow_management.run_loader import RunLoader
    from mts.workflow_management.run_writer import RunWriter

    assert RunLoader.__name__ == "RunLoader"
    assert RunWriter.__name__ == "RunWriter"
    manifest = {"approvals": []}
    manifest = record_approval(
        manifest,
        gate="scope_review",
        artifact_revision="scope-r1",
        status="approved",
        reviewer="sample-bypass",
    )
    assert require_approval(manifest, gate="scope_review", artifact_revision="scope-r1") == "worksheet_prepared"


def test_inactive_target_worksheet_type_is_rejected():
    from mts.setup_project.configure import EffectiveConfigError, resolve_effective_config

    try:
        resolve_effective_config(
            {"subject": "math", "worksheet_type": "homework-4-day"},
            repository_root=REPO,
        )
    except EffectiveConfigError as error:
        assert "not active" in str(error)
    else:
        raise AssertionError("Draft Worksheet Type must be rejected by the target resolver.")
