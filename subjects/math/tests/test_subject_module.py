"""Focused behavior-preservation tests for the Math subject-module adapter."""
from pathlib import Path
import json
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
import subject_module


MODULE = subject_module.MathSubjectModule(REPO)
TYPE_CONFIG = {
    "worksheet_type_id": "class-worksheet",
    "duration_minutes": 15,
    "grade_defaults": {"grade_6": {"question_count": 32}},
    "template_selection": {"template_manifest": "subjects/math/config/template-manifest.json"},
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


def test_blueprint_uses_worksheet_type_defaults():
    plan = MODULE.prepare_blueprint({"grade_or_course": "grade_6"}, TYPE_CONFIG, {})
    assert plan["worksheet_type"] == "class-worksheet"
    assert plan["question_count"] == 32
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


def main():
    tests = [
        test_resolve_curriculum_preserves_p0_cache_behavior,
        test_blueprint_uses_worksheet_type_defaults,
        test_verification_and_output_qa_delegate_to_p0_runtime,
        test_build_spec_requires_generated_candidate,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
