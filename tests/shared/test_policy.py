"""Focused tests for shared policy resolution."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "runtime"))
import policy


def test_active_class_worksheet_resolves():
    resolved = policy.resolve(
        {"subject": "math", "worksheet_type": "class-worksheet"},
        repository_root=REPO,
    )
    assert resolved["subject"] == "math"
    assert resolved["worksheet_type_id"] == "class-worksheet"
    assert resolved["status"] == "active"
    assert resolved["project"]["timezone"] == "America/New_York"
    assert resolved["publishing"]["target"] == "outputs/math"
    assert resolved["grade_defaults"]["grade_6"]["question_count"] == 32


def test_request_override_has_highest_precedence_and_snapshot_is_immutable():
    resolved = policy.resolve(
        {
            "subject": "math",
            "worksheet_type": "class-worksheet",
            "overrides": {"duration_minutes": 20},
        },
        repository_root=REPO,
    )
    assert resolved["duration_minutes"] == 20
    assert resolved["run_overrides"]["duration_minutes"] == 20
    try:
        resolved["duration_minutes"] = 30
    except TypeError:
        pass
    else:
        raise AssertionError("Resolved policy must be immutable.")


def test_active_weekly_worksheet_resolves_all_math_grades():
    resolved = policy.resolve(
        {"subject": "math", "worksheet_type": "weekly-worksheet"},
        repository_root=REPO,
    )
    assert resolved["status"] == "active"
    assert resolved["compatible_subjects"] == ("math",)
    assert resolved["grade_defaults"]["grade_1"]["question_count"] == 50
    assert resolved["grade_defaults"]["grade_4"]["question_count"] == 50
    assert resolved["grade_defaults"]["grade_5"]["question_count"] == 50
    assert resolved["grade_defaults"]["grade_6"]["question_count"] == 40
    assert resolved["grade_defaults"]["grade_9_10"]["grade_split"] == {"math_1": 25, "math_2": 25}


def test_draft_homework_type_is_rejected():
    try:
        policy.resolve(
            {"subject": "math", "worksheet_type": "homework-4-day"},
            repository_root=REPO,
        )
    except policy.PolicyError as error:
        assert "not active" in str(error)
    else:
        raise AssertionError("Draft Homework Worksheet Type must be rejected.")


def test_draft_compact_unbranded_type_is_rejected():
    try:
        policy.resolve(
            {"subject": "math", "worksheet_type": "compact-unbranded"},
            repository_root=REPO,
        )
    except policy.PolicyError as error:
        assert "not active" in str(error)
    else:
        raise AssertionError("Draft Compact/Unbranded Worksheet Type must be rejected.")


def test_unknown_and_incompatible_requests_are_rejected():
    for request, expected in [
        ({"subject": "science", "worksheet_type": "class-worksheet"}, "Configuration file not found"),
        ({"subject": "ela", "worksheet_type": "class-worksheet"}, "not compatible"),
        ({"subject": "math", "worksheet_type": "missing-type"}, "Configuration file not found"),
    ]:
        try:
            policy.resolve(request, repository_root=REPO)
        except policy.PolicyError as error:
            assert expected in str(error)
        else:
            raise AssertionError(f"Request must be rejected: {request}")


def main():
    tests = [
        test_active_class_worksheet_resolves,
        test_request_override_has_highest_precedence_and_snapshot_is_immutable,
        test_active_weekly_worksheet_resolves_all_math_grades,
        test_draft_homework_type_is_rejected,
        test_draft_compact_unbranded_type_is_rejected,
        test_unknown_and_incompatible_requests_are_rejected,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
