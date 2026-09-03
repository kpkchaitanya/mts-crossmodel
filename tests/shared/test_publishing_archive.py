"""Focused tests for the Archive Folder publishing utility (policy and orchestration)."""
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.publishing import archive  # noqa: E402


CONFIG = {
    "publishing": {
        "staging": {"approved_folder_id": "staging-approved"},
        "final_delivery": {
            "week_folder_pattern": "Week_{{WEEK_OF}}",
            "destinations_by_grade": {
                "grade_1": {"folder_id": "parent-1", "label": "1st Grade"},
                "grade_6": {"folder_id": "parent-6", "label": "6th Grade"},
            },
        },
        "archive": {
            "enabled": True,
            "archive_folder_name": "Archive",
            "targets": {
                "staging": {"folder_type": "folder", "source": "publishing.staging.approved_folder_id"},
                "publish": {
                    "folder_type": "parent",
                    "source": "publishing.final_delivery.destinations_by_grade",
                    "default_folder_date": "latest",
                },
            },
            "auto_archive": {"before_render": False, "before_delivery": False},
        },
    }
}


class FakeAdapter:
    """Minimal stand-in exposing only the three adapter primitives the utility uses."""

    def __init__(self, files=None, folders=None, move_error_on=None):
        self.files = files or {}
        self.folders = folders or {}
        self.move_error_on = move_error_on
        self.moves = []
        self.created_folders = []

    def list_child_files(self, folder_id):
        return [dict(item) for item in self.files.get(folder_id, [])]

    def list_child_folders(self, folder_id):
        return [dict(item) for item in self.folders.get(folder_id, [])]

    def ensure_child_folder(self, parent_id, name):
        for folder in self.folders.get(parent_id, []):
            if folder["name"] == name:
                return {**folder, "created": False}
        created = {"id": f"archive-of-{parent_id}", "name": name, "webViewLink": "https://drive/new"}
        self.folders.setdefault(parent_id, []).append(created)
        self.created_folders.append(created)
        return {**created, "created": True}

    def move_file(self, file_id, destination_id):
        if file_id == self.move_error_on:
            raise RuntimeError("Drive permission denied")
        self.moves.append((file_id, destination_id))
        return {"id": file_id, "parents": [destination_id], "webViewLink": f"https://docs/{file_id}"}


def file_entry(file_id, name):
    return {"id": file_id, "name": name, "webViewLink": f"https://docs/{file_id}"}


def folder_entry(folder_id, name):
    return {"id": folder_id, "name": name, "webViewLink": f"https://drive/{folder_id}"}


def test_parse_folder_reference_accepts_preset_id_and_url():
    assert archive.parse_folder_reference("staging") == "staging"
    assert archive.parse_folder_reference("1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS") == "1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS"
    url = "https://drive.google.com/drive/u/0/folders/10tSM2SwAxzGkzuYT47vNCo16K9TtPZre"
    assert archive.parse_folder_reference(url) == "10tSM2SwAxzGkzuYT47vNCo16K9TtPZre"


def test_staging_preset_resolves_to_the_canonical_approved_folder():
    targets = archive.resolve_targets({"folder": "staging"}, CONFIG)
    assert targets == [{"label": "staging", "folder_id": "staging-approved", "folder_type": "folder"}]


def test_publish_preset_expands_per_grade_and_honors_a_grade_restriction():
    every = archive.resolve_targets({"folder": "publish"}, CONFIG)
    assert [target["grade_id"] for target in every] == ["grade_1", "grade_6"]
    assert all(target["folder_type"] == "parent" for target in every)

    restricted = archive.resolve_targets({"folder": "publish", "grades": "grade-6"}, CONFIG)
    assert [target["folder_id"] for target in restricted] == ["parent-6"]


def test_unconfigured_grade_and_unknown_preset_fail_closed():
    with pytest.raises(archive.ArchiveError, match="No configured destination"):
        archive.resolve_targets({"folder": "publish", "grades": "grade_9_10"}, CONFIG)
    with pytest.raises(archive.ArchiveError, match="not a known preset"):
        archive.resolve_targets({"folder": "nope"}, CONFIG)


def test_raw_folder_id_requires_an_explicit_folder_type():
    with pytest.raises(archive.ArchiveError, match="folder_type is required"):
        archive.resolve_targets({"folder": "1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS"}, CONFIG)
    resolved = archive.resolve_targets(
        {"folder": "1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS", "folder_type": "folder"}, CONFIG
    )
    assert resolved[0]["folder_type"] == "folder"


def test_folder_date_is_refused_in_folder_mode():
    with pytest.raises(archive.ArchiveError, match="parent mode only"):
        archive.resolve_targets({"folder": "staging", "folder_date": "latest"}, CONFIG)


def test_select_effective_folder_prefers_latest_and_never_the_archive_folder():
    folders = [folder_entry("archive-1", "Archive"), folder_entry("week-2", "Week_2026-08-31"), folder_entry("week-1", "Week_2026-08-24")]
    selected = archive.select_effective_folder(
        folders, folder_date="latest", archive_folder_name="Archive", week_folder_pattern="Week_{{WEEK_OF}}"
    )
    assert selected["id"] == "week-2"


def test_select_effective_folder_resolves_an_iso_date_to_its_week_folder():
    folders = [folder_entry("week-2", "Week_2026-08-31"), folder_entry("week-1", "Week_2026-08-24")]
    # A mid-week date resolves to that week's Monday, matching the delivery naming contract.
    selected = archive.select_effective_folder(
        folders, folder_date="2026-08-26", archive_folder_name="Archive", week_folder_pattern="Week_{{WEEK_OF}}"
    )
    assert selected["id"] == "week-1"

    with pytest.raises(archive.ArchiveError, match="No child folder named"):
        archive.select_effective_folder(
            folders, folder_date="2026-09-07", archive_folder_name="Archive", week_folder_pattern="Week_{{WEEK_OF}}"
        )


def test_plan_archive_ignores_nothing_and_an_empty_listing_is_a_valid_no_op():
    assert archive.plan_archive([]) == []
    assert [item["id"] for item in archive.plan_archive([file_entry("d1", "A")])] == ["d1"]


def test_folder_mode_moves_every_loose_file_into_a_created_archive_folder():
    adapter = FakeAdapter(files={"staging-approved": [file_entry("d1", "Grade 6"), file_entry("d2", "Grade 6_KEY")]})
    record = archive.run_archive({"folder": "staging"}, CONFIG, adapter, dry_run=False)

    assert record["status"] == "archived"
    assert adapter.moves == [("d1", "archive-of-staging-approved"), ("d2", "archive-of-staging-approved")]
    assert record["targets"][0]["archive_folder"]["created"] is True
    assert [item["id"] for item in record["targets"][0]["moved"]] == ["d1", "d2"]
    assert record["targets"][0]["unmoved"] == []


def test_a_dry_run_mutates_nothing_and_still_reports_a_complete_plan():
    adapter = FakeAdapter(files={"staging-approved": [file_entry("d1", "Grade 6")]})
    record = archive.run_archive({"folder": "staging"}, CONFIG, adapter, dry_run=True)

    assert record["status"] == "dry_run"
    assert adapter.moves == []
    assert adapter.created_folders == []
    assert record["targets"][0]["archive_folder"]["would_create"] is True
    assert [item["id"] for item in record["targets"][0]["unmoved"]] == ["d1"]


def test_re_running_on_an_archived_folder_records_a_no_op():
    adapter = FakeAdapter(files={"staging-approved": []}, folders={"staging-approved": [folder_entry("a1", "Archive")]})
    record = archive.run_archive({"folder": "staging"}, CONFIG, adapter, dry_run=False)

    assert record["status"] == "no_op"
    assert adapter.moves == []
    assert record["targets"][0]["archive_folder"]["created"] is False


def test_parent_mode_archives_inside_the_latest_week_folder():
    adapter = FakeAdapter(
        files={"parent-6": [], "week-2": [file_entry("d1", "Grade 6")]},
        folders={"parent-6": [folder_entry("week-2", "Week_2026-08-31"), folder_entry("week-1", "Week_2026-08-24")]},
    )
    record = archive.run_archive(
        {"folder": "publish", "grades": "grade_6", "folder_date": "latest"}, CONFIG, adapter, dry_run=False
    )

    assert record["targets"][0]["effective_folder"]["id"] == "week-2"
    assert adapter.moves == [("d1", "archive-of-week-2")]


def test_parent_mode_refuses_when_the_parent_holds_loose_files():
    adapter = FakeAdapter(files={"parent-6": [file_entry("d1", "Stray")]}, folders={"parent-6": [folder_entry("week-2", "W")]})
    record = archive.run_archive({"folder": "publish", "grades": "grade_6"}, CONFIG, adapter, dry_run=False)

    assert record["status"] == "failed"
    assert "loose files" in record["targets"][0]["error"]
    assert adapter.moves == []


def test_partial_failure_splits_moved_and_unmoved_and_reports_failure():
    adapter = FakeAdapter(
        files={"staging-approved": [file_entry("d1", "A"), file_entry("d2", "B"), file_entry("d3", "C")]},
        move_error_on="d2",
    )
    record = archive.run_archive({"folder": "staging"}, CONFIG, adapter, dry_run=False)

    target = record["targets"][0]
    assert record["status"] == "failed"
    assert [item["id"] for item in target["moved"]] == ["d1"]
    assert [item["id"] for item in target["unmoved"]] == ["d2", "d3"]
    assert "permission denied" in target["error"]


def test_one_failing_grade_does_not_hide_the_others():
    adapter = FakeAdapter(
        files={"parent-1": [], "parent-6": [], "week-6": [file_entry("d1", "Grade 6")]},
        folders={"parent-1": [], "parent-6": [folder_entry("week-6", "Week_2026-08-31")]},
    )
    record = archive.run_archive({"folder": "publish"}, CONFIG, adapter, dry_run=False)

    statuses = {target.get("grade_id"): target["status"] for target in record["targets"]}
    assert statuses == {"grade_1": "failed", "grade_6": "archived"}
    assert record["status"] == "failed"


def test_archiving_is_refused_when_the_utility_is_disabled():
    disabled = {"publishing": {**CONFIG["publishing"], "archive": {**CONFIG["publishing"]["archive"], "enabled": False}}}
    with pytest.raises(archive.ArchiveError, match="disabled"):
        archive.run_archive({"folder": "staging"}, disabled, FakeAdapter(), dry_run=True)


def test_the_cli_script_holds_no_decision_logic():
    """Guards the future pipeline hook: behavior must live in run_archive, not the script."""
    source = (REPO / "scripts" / "archive_folder.py").read_text(encoding="utf-8")
    assert source.count("run_archive(") == 1
    for leaked in ("in parents", "list_child_files", "list_child_folders", "ensure_child_folder", "move_file"):
        assert leaked not in source
