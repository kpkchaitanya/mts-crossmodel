"""Focused tests for revision-scoped gate approval and invalidation."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.workflow_management import gates


def manifest():
    return {"run_id": "run-test", "status": "initialized", "approvals": []}


def test_approved_revision_allows_only_matching_transition():
    updated = gates.record_approval(
        manifest(),
        gate="scope_review",
        artifact_revision="scope-r1",
        status="approved",
        reviewer="teacher",
    )
    assert gates.require_approval(updated, gate="scope_review", artifact_revision="scope-r1") == "worksheet_prepared"
    try:
        gates.require_approval(updated, gate="scope_review", artifact_revision="scope-r2")
    except gates.GateError as error:
        assert "Missing" in str(error)
    else:
        raise AssertionError("Approval must not apply to a newer revision.")


def test_rejected_and_missing_approvals_fail_closed():
    rejected = gates.record_approval(
        manifest(),
        gate="question_review",
        artifact_revision="spec-r1",
        status="rejected",
    )
    for current, expected in [(manifest(), "Missing"), (rejected, "Rejected")]:
        try:
            gates.require_approval(current, gate="question_review", artifact_revision="spec-r1")
        except gates.GateError as error:
            assert expected in str(error)
        else:
            raise AssertionError("Unapproved transition must fail closed.")


def test_question_change_invalidates_only_dependent_approvals():
    updated = manifest()
    for gate, revision in [
        ("scope_review", "scope-r1"),
        ("question_review", "spec-r1"),
        ("verification_review", "verification-r1"),
        ("formatting_review", "render-r1"),
        ("publish_approval", "qa-r1"),
    ]:
        updated = gates.record_approval(updated, gate=gate, artifact_revision=revision, status="approved")

    invalidated = gates.invalidate(updated, change="question", reason="Question 4 was edited.")
    assert invalidated["status"] == "question_invalidated"
    assert invalidated["approvals"][0].get("invalidated_at") is None
    assert all(approval.get("invalidated_at") for approval in invalidated["approvals"][1:])
    assert gates.require_approval(invalidated, gate="scope_review", artifact_revision="scope-r1") == "worksheet_prepared"
    try:
        gates.require_approval(invalidated, gate="verification_review", artifact_revision="verification-r1")
    except gates.GateError as error:
        assert "Stale" in str(error)
    else:
        raise AssertionError("Question change must invalidate verification approval.")


def test_template_change_preserves_scope_and_question_approvals():
    updated = gates.record_approval(manifest(), gate="scope_review", artifact_revision="scope-r1", status="approved")
    updated = gates.record_approval(updated, gate="question_review", artifact_revision="spec-r1", status="approved")
    updated = gates.record_approval(updated, gate="formatting_review", artifact_revision="render-r1", status="approved")
    invalidated = gates.invalidate(updated, change="template", reason="Template revision changed.")
    assert invalidated["status"] == "template_invalidated"
    assert not invalidated["approvals"][0].get("invalidated_at")
    assert not invalidated["approvals"][1].get("invalidated_at")
    assert invalidated["approvals"][2].get("invalidated_at")


def test_question_review_requires_persisted_spec_reference():
    manifest = {"approvals": [{"gate": "question_review", "artifact_revision": "questions-r1", "status": "approved"}]}
    try:
        gates.require_question_review(manifest, artifact_revision="questions-r1")
    except gates.GateError as error:
        assert "persisted Worksheet Spec" in str(error)
    else:
        raise AssertionError("Gate 2 must not advance without a persisted Worksheet Spec.")

    manifest["spec_references"] = [{"worksheet_id": "grade-4", "spec_path": "specs/grade-4/r1.json"}]
    assert gates.require_question_review(manifest, artifact_revision="questions-r1") == "verification_in_progress"


def main():
    tests = [
        test_approved_revision_allows_only_matching_transition,
        test_rejected_and_missing_approvals_fail_closed,
        test_question_change_invalidates_only_dependent_approvals,
        test_template_change_preserves_scope_and_question_approvals,
        test_question_review_requires_persisted_spec_reference,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
