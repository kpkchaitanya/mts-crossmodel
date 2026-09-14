"""Focused behavior-preservation tests for the Math subject-module adapter."""
from pathlib import Path
import json
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from mts.subjects.math import subject_module


MODULE = subject_module.MathSubjectModule()
TYPE_CONFIG = {
    "worksheet_type_id": "class-worksheet",
    "duration_minutes": 15,
    "grade_defaults": {"grade_6": {"questions_per_worksheet": 32}},
    "template_selection": {"template_manifest": "data/master/subjects/math/template_manifests/class-worksheet.json"},
}


def sample_spec():
    return {
        "worksheet": {"grade": "Grade 6", "title": "MTS - CLASS WORKSHEET", "question_count": 1},
        "sections": [{"id": "A", "questions": [
            {"number": 1, "prompt": "Find 3 + 4.", "answer": 7, "skill": "arithmetic", "difficulty": "easy",
             "verification": {"method": "arithmetic_expression", "inputs": {"expression": "3+4"}}}
        ]}],
    }


def test_resolve_curriculum_preserves_p0_cache_behavior():
    scope = MODULE.resolve_curriculum({"grade_or_course": "grade_6", "on_date": "2026-08-24"})
    assert scope["cache_hit"] is True
    assert scope["source"] == "weekly_cache"
    assert "NC.6.RP.1" in scope["current"]
    assert scope["progressive_context"]["official_ccs_pacing"] is False
    assert scope["standards_context"]["source"] == "nc_standards_cache"


def test_blueprint_uses_worksheet_type_defaults():
    plan = MODULE.prepare_blueprint({"grade_or_course": "grade_6"}, TYPE_CONFIG, {})
    assert plan["worksheet_type"] == "class-worksheet"
    assert plan["grade_display_name"] == "Grade 6"
    assert plan["questions_per_worksheet"] == 32
    assert plan["duration_minutes"] == 15


def test_verification_and_output_qa_delegate_to_p0_runtime():
    spec = sample_spec()
    verification = MODULE.verify_spec(spec)
    assert verification["status"] == "PASS"
    artifacts = {
        "student_worksheet": "MTS - CLASS WORKSHEET\nGrade 6\n1. Find 3 + 4.",
        "answer_key": "MTS - CLASS WORKSHEET\nGrade 6\nANSWER KEY\n1. 7",
    }
    qa = MODULE.validate_subject_output(artifacts, spec)
    assert qa["student_worksheet"]["status"] == "PASS"
    assert qa["answer_key"]["status"] == "PASS"


def test_build_spec_requires_generated_candidate():
    candidate = sample_spec()
    assert MODULE.build_spec({"subject": "math"}, {"spec": candidate}) == candidate
    try:
        MODULE.build_spec({"subject": "math"}, {})
    except subject_module.MathSubjectError as error:
        assert "candidate spec" in str(error)
    else:
        raise AssertionError("A Math candidate spec is required.")


def test_build_week_plan_and_check_diversity_and_progression_delegate_to_question_plan():
    sections = [{"id": "monday"}, {"id": "tuesday"}]
    plan = MODULE.build_week_plan(
        sections, ["skill_a", "skill_b"], None, 4,
        difficulty="high", diversity="low",
        topic_overrides=[{"topic": "override_topic", "kind": "count", "value": 2}],
    )
    assert set(plan) == {"monday", "tuesday"}
    assert sum(1 for entry in plan["monday"] if entry.get("topic_override")) == 2

    spec = {"sections": [{"id": "monday", "questions": [
        {"number": i + 1, "skill": entry["skill"], "difficulty": entry["difficulty"]}
        for i, entry in enumerate(plan["monday"])
    ]}]}
    result = MODULE.check_diversity_and_progression(spec, diversity="low")
    assert result["status"] == "PASS"


def main():
    tests = [
        test_resolve_curriculum_preserves_p0_cache_behavior,
        test_blueprint_uses_worksheet_type_defaults,
        test_verification_and_output_qa_delegate_to_p0_runtime,
        test_build_spec_requires_generated_candidate,
        test_build_week_plan_and_check_diversity_and_progression_delegate_to_question_plan,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()

