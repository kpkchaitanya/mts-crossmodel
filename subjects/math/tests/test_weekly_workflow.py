"""Focused Gate 1 planning tests for the Math Weekly Worksheet workflow."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
MATH = REPO / "subjects" / "math"
sys.path.insert(0, str(REPO / "src" / "runtime"))
sys.path.insert(0, str(MATH / "src"))
import policy
import subject_module
import weekly_workflow


MATH_MODULE = subject_module.MathSubjectModule(MATH)
WEEKLY_POLICY = policy.resolve(
    {"subject": "math", "worksheet_type": "weekly-worksheet"},
    repository_root=REPO,
)


def test_scope_review_resolves_all_math_weekly_plans():
    review = weekly_workflow.prepare_scope_review(
        WEEKLY_POLICY,
        on_date="2026-08-24",
        subject_module=MATH_MODULE,
    )
    assert review["gate"] == "scope_review"
    assert review["status"] == "pending"
    assert [plan["grade_or_course"] for plan in review["worksheet_plans"]] == [
        "grade_1", "grade_4", "grade_5", "grade_6", "grade_9_10"
    ]
    assert len(review["worksheet_plans"]) == 5


def test_weekly_counts_sections_and_high_school_split_are_preserved():
    review = weekly_workflow.prepare_scope_review(
        WEEKLY_POLICY,
        on_date="2026-08-24",
        subject_module=MATH_MODULE,
    )
    plans = {entry["grade_or_course"]: entry for entry in review["worksheet_plans"]}
    assert WEEKLY_POLICY["sections"] and len(WEEKLY_POLICY["sections"]) == 5
    assert plans["grade_1"]["plan"]["question_count"] == 50
    assert plans["grade_4"]["plan"]["question_count"] == 50
    assert plans["grade_5"]["plan"]["question_count"] == 50
    assert plans["grade_6"]["plan"]["question_count"] == 40
    high_school = plans["grade_9_10"]
    assert high_school["plan"]["question_count"] == 50
    assert high_school["plan"]["grade_split"] == {"math_1": 25, "math_2": 25}
    assert [scope["grade_or_course"] for scope in high_school["curriculum_scopes"]] == ["math_1", "math_2"]


def test_scope_review_keeps_cache_provenance_and_rejects_unknown_grade():
    review = weekly_workflow.prepare_scope_review(
        WEEKLY_POLICY,
        on_date="2026-08-24",
        subject_module=MATH_MODULE,
        grade_ids=["grade_6"],
    )
    scope = review["worksheet_plans"][0]["curriculum_scopes"][0]
    assert scope["cache_hit"] is True
    assert scope["source"] == "weekly_cache"
    try:
        weekly_workflow.prepare_scope_review(
            WEEKLY_POLICY,
            on_date="2026-08-24",
            subject_module=MATH_MODULE,
            grade_ids=["grade_99"],
        )
    except weekly_workflow.WeeklyWorkflowError as error:
        assert "not enabled" in str(error)
    else:
        raise AssertionError("Unknown grade must not produce a Weekly plan.")


def main():
    tests = [
        test_scope_review_resolves_all_math_weekly_plans,
        test_weekly_counts_sections_and_high_school_split_are_preserved,
        test_scope_review_keeps_cache_provenance_and_rejects_unknown_grade,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
