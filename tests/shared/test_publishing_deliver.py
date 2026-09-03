"""Focused tests for the Final Delivery policy and the Deliver Worksheets utility."""
from pathlib import Path
import json
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.publishing import deliver  # noqa: E402

NAMING = {
    "document_name_pattern": "{{PREFIX}}-{{WEEK_OF}}",
    "answer_key_suffix": "_KEY",
    "prefix_by_grade": {
        "grade_1": "MTS-Math-1stGrade-WeeklyWorksheet",
        "grade_6": "MTS-Math-6thGrade-WeeklyWorksheet",
    },
}

CONFIG = {
    "calendar": {"week_1_start": "2026-08-17"},
    "naming": {"weekly": NAMING},
    "publishing": {
        "staging": {"approved_folder_id": "staging-approved"},
        "final_delivery": {
            "enabled": True,
            "week_folder_pattern": "Week_{{WEEK_OF}}",
            "mode": "copy",
            "deliver_answer_key": True,
            "destinations_by_grade": {
                "grade_1": {"folder_id": "parent-1", "label": "1st Grade"},
                "grade_6": {"folder_id": "parent-6", "label": "6th Grade"},
            },
        },
    },
}


class FakeAdapter:
    def __init__(self, files=None, deliver_error_on=None):
        self.files = files or {}
        self.deliver_error_on = deliver_error_on
        self.week_folders = []
        self.deliveries = []

    def list_child_files(self, folder_id):
        return [dict(item) for item in self.files.get(folder_id, [])]

    def ensure_child_folder(self, parent_id, name):
        self.week_folders.append((parent_id, name))
        return {"id": f"week-of-{parent_id}", "name": name, "created": True}

    def deliver_pair(self, student, answer_key, destination_id, *, mode="copy", deliver_answer_key=True):
        if destination_id == self.deliver_error_on:
            raise RuntimeError("Drive rate limit exceeded")
        self.deliveries.append((student["document"]["id"], answer_key["document"]["id"], destination_id, mode))
        return {
            "status": "delivered",
            "student_worksheet": {"document": {"id": student["document"]["id"], "webViewLink": "https://docs/s"}},
            "answer_key": {"document": {"id": answer_key["document"]["id"], "webViewLink": "https://docs/k"}},
        }


def doc(file_id, name):
    return {"id": file_id, "name": name, "webViewLink": f"https://docs/{file_id}"}


def staging_for(week="2026-08-31", extra=()):
    return {
        "staging-approved": [
            doc("g1", f"MTS-Math-1stGrade-WeeklyWorksheet-{week}"),
            doc("g1k", f"MTS-Math-1stGrade-WeeklyWorksheet-{week}_KEY"),
            doc("g6", f"MTS-Math-6thGrade-WeeklyWorksheet-{week}"),
            doc("g6k", f"MTS-Math-6thGrade-WeeklyWorksheet-{week}_KEY"),
            *extra,
        ]
    }


def test_week_resolution_accepts_current_a_week_number_and_a_mid_week_date():
    calendar = CONFIG["calendar"]
    assert deliver.resolve_week_of("1", calendar) == "2026-08-17"
    assert deliver.resolve_week_of("3", calendar) == "2026-08-31"
    # Any date resolves to its own week's Monday.
    assert deliver.resolve_week_of("2026-09-03", calendar) == "2026-08-31"


def test_destination_resolution_fails_closed_on_an_unconfigured_grade():
    settings = CONFIG["publishing"]["final_delivery"]
    assert [d["grade_id"] for d in deliver.resolve_destinations(settings, "all")] == ["grade_1", "grade_6"]
    assert [d["folder_id"] for d in deliver.resolve_destinations(settings, "grade-6")] == ["parent-6"]
    with pytest.raises(deliver.DeliveryError, match="No configured Final Delivery destination"):
        deliver.resolve_destinations(settings, "grade_9_10")


def test_document_names_follow_the_configured_pattern():
    assert deliver.document_names(NAMING, "grade_6", "2026-08-31") == (
        "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31",
        "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31_KEY",
    )


def test_staging_pairing_matches_each_grade_by_name():
    pairs, issues = deliver.pair_from_staging(
        staging_for()["staging-approved"], week_of="2026-08-31", naming=NAMING, grade_ids=["grade_1", "grade_6"]
    )
    assert pairs["grade_6"]["student_worksheet"]["id"] == "g6"
    assert pairs["grade_6"]["answer_key"]["id"] == "g6k"
    assert issues == []


def test_staging_pairing_refuses_a_duplicate_name_instead_of_choosing():
    files = staging_for(extra=[doc("g6-dupe", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31")])["staging-approved"]
    pairs, issues = deliver.pair_from_staging(
        files, week_of="2026-08-31", naming=NAMING, grade_ids=["grade_6"]
    )
    assert "grade_6" not in pairs
    assert issues[0]["reason"] == "ambiguous_name"
    assert sorted(issues[0]["documents"]["student_worksheet"]) == ["g6", "g6-dupe"]


def test_staging_pairing_reports_a_missing_answer_key():
    files = [doc("g6", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31")]
    pairs, issues = deliver.pair_from_staging(files, week_of="2026-08-31", naming=NAMING, grade_ids=["grade_6"])
    assert pairs == {}
    assert issues[0]["reason"] == "incomplete_pair"
    assert issues[0]["found"] == {"student_worksheet": True, "answer_key": False}


def test_staging_pairing_reports_unmatched_files_such_as_manual_copies():
    files = staging_for(extra=[doc("copy", "Copy of MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31")])["staging-approved"]
    _, issues = deliver.pair_from_staging(files, week_of="2026-08-31", naming=NAMING, grade_ids=["grade_1", "grade_6"])
    unmatched = [issue for issue in issues if issue["reason"] == "unmatched_files"][0]
    assert [entry["id"] for entry in unmatched["documents"]] == ["copy"]


def test_a_different_week_matches_nothing_rather_than_delivering_the_wrong_week():
    pairs, issues = deliver.pair_from_staging(
        staging_for()["staging-approved"], week_of="2026-09-07", naming=NAMING, grade_ids=["grade_6"]
    )
    assert pairs == {}
    assert issues[0]["reason"] == "incomplete_pair"


def test_delivery_creates_one_week_folder_per_grade_and_copies_the_pair():
    adapter = FakeAdapter(files=staging_for())
    record = deliver.run_deliver({"week": "2026-08-31"}, CONFIG, adapter, dry_run=False)

    assert record["status"] == "delivered"
    assert record["week_folder_name"] == "Week_2026-08-31"
    assert adapter.week_folders == [("parent-1", "Week_2026-08-31"), ("parent-6", "Week_2026-08-31")]
    assert adapter.deliveries == [
        ("g1", "g1k", "week-of-parent-1", "copy"),
        ("g6", "g6k", "week-of-parent-6", "copy"),
    ]


def test_a_dry_run_creates_no_folder_and_delivers_nothing():
    adapter = FakeAdapter(files=staging_for())
    record = deliver.run_deliver({"week": "2026-08-31"}, CONFIG, adapter, dry_run=True)

    assert record["status"] == "dry_run"
    assert adapter.week_folders == [] and adapter.deliveries == []
    assert record["targets"][0]["pair"]["student_worksheet"]["name"].endswith("2026-08-31")


def test_a_missing_grade_is_skipped_by_default_so_available_grades_still_deliver():
    adapter = FakeAdapter(
        files={"staging-approved": [
            doc("g6", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31"),
            doc("g6k", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31_KEY"),
        ]}
    )
    record = deliver.run_deliver(
        {"week": "2026-08-31", "grades": "grade_1,grade_6"}, CONFIG, adapter, dry_run=False
    )

    statuses = {target["grade_id"]: target["status"] for target in record["targets"]}
    assert statuses == {"grade_1": "skipped", "grade_6": "delivered"}
    assert record["status"] == "delivered"
    assert adapter.deliveries == [("g6", "g6k", "week-of-parent-6", "copy")]


def test_on_missing_fail_blocks_when_a_requested_grade_is_absent():
    adapter = FakeAdapter(files={"staging-approved": []})
    record = deliver.run_deliver(
        {"week": "2026-08-31", "grades": "grade_6", "on_missing": "fail"}, CONFIG, adapter, dry_run=True
    )

    assert record["status"] == "failed"
    assert record["targets"][0]["status"] == "failed"


def test_a_broad_request_skips_grades_with_no_staged_pair():
    adapter = FakeAdapter(
        files={"staging-approved": [
            doc("g6", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31"),
            doc("g6k", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31_KEY"),
        ]}
    )
    record = deliver.run_deliver({"week": "2026-08-31"}, CONFIG, adapter, dry_run=True)

    statuses = {target["grade_id"]: target["status"] for target in record["targets"]}
    assert statuses == {"grade_1": "skipped", "grade_6": "dry_run"}
    assert record["status"] == "dry_run"


def test_one_failing_grade_does_not_prevent_the_others():
    adapter = FakeAdapter(files=staging_for(), deliver_error_on="week-of-parent-1")
    record = deliver.run_deliver({"week": "2026-08-31"}, CONFIG, adapter, dry_run=False)

    statuses = {target["grade_id"]: target["status"] for target in record["targets"]}
    assert statuses == {"grade_1": "failed", "grade_6": "delivered"}
    assert record["status"] == "failed"


def test_a_run_root_supplies_exact_pairs_and_bypasses_name_matching(tmp_path):
    (tmp_path / "published-artifacts.json").write_text(
        json.dumps({
            "pairs": {
                "grade_6": {
                    "student_worksheet": {"id": "exact-6", "name": "anything at all"},
                    "answer_key": {"id": "exact-6k", "name": "anything at all_KEY"},
                }
            }
        }),
        encoding="utf-8",
    )
    # Staging holds a conflicting duplicate that would block name-based pairing.
    adapter = FakeAdapter(files=staging_for(extra=[doc("g6-dupe", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31")]))
    record = deliver.run_deliver(
        {"week": "2026-08-31", "grades": "grade_6"}, CONFIG, adapter, dry_run=False, run_root=tmp_path
    )

    assert record["status"] == "delivered"
    assert adapter.deliveries == [("exact-6", "exact-6k", "week-of-parent-6", "copy")]
    assert record["source"] == "published-artifacts.json"


def test_delivery_is_refused_when_disabled_or_given_an_unknown_mode():
    disabled = {**CONFIG, "publishing": {**CONFIG["publishing"], "final_delivery": {**CONFIG["publishing"]["final_delivery"], "enabled": False}}}
    with pytest.raises(deliver.DeliveryError, match="disabled"):
        deliver.run_deliver({"week": "current"}, disabled, FakeAdapter(), dry_run=True)
    with pytest.raises(deliver.DeliveryError, match="mode must be"):
        deliver.run_deliver({"week": "current", "mode": "link"}, CONFIG, FakeAdapter(), dry_run=True)


def test_the_cli_script_holds_no_decision_logic():
    source = (REPO / "scripts" / "deliver_folder.py").read_text(encoding="utf-8")
    assert source.count("run_deliver(") == 1
    for leaked in ("prefix_by_grade", "destinations_by_grade", "week_folder_pattern", "deliver_pair", "_KEY"):
        assert leaked not in source


def test_the_shipped_math_configuration_defines_naming_for_every_delivered_grade():
    from mts.setup_project.configure import resolve_effective_config

    resolved = resolve_effective_config(
        {"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO
    )
    naming = deliver.naming_settings(resolved)
    destinations = resolved["publishing"]["final_delivery"]["destinations_by_grade"]
    assert set(destinations) <= set(naming["prefix_by_grade"])
