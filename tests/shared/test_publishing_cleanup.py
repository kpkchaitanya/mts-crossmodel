"""Focused tests for the Cleanup Folder publishing utility."""
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.publishing import archive, cleanup  # noqa: E402

from test_publishing_archive import CONFIG as ARCHIVE_CONFIG, FakeAdapter, file_entry, folder_entry  # noqa: E402

CONFIG = {
    "publishing": {
        **ARCHIVE_CONFIG["publishing"],
        "cleanup": {
            "enabled": True,
            "default_scope": "files",
            "require_confirmation": True,
            "targets": ARCHIVE_CONFIG["publishing"]["archive"]["targets"],
        },
    }
}


class CleanupAdapter(FakeAdapter):
    def __init__(self, files=None, folders=None, trash_error_on=None):
        super().__init__(files=files, folders=folders)
        self.trash_error_on = trash_error_on
        self.trashed = []

    def trash_file(self, file_id):
        if file_id == self.trash_error_on:
            raise RuntimeError("Drive permission denied")
        self.trashed.append(file_id)
        return {"id": file_id, "trashed": True}


def staging_adapter(**kwargs):
    return CleanupAdapter(
        files={
            "staging-approved": [file_entry("d1", "Current A"), file_entry("d2", "Current B")],
            "archive-1": [file_entry("a1", "Old A"), file_entry("a2", "Old B"), file_entry("a3", "Old C")],
        },
        folders={"staging-approved": [folder_entry("archive-1", "Archive")]},
        **kwargs,
    )


def test_default_scope_targets_loose_files_only():
    adapter = staging_adapter()
    record = cleanup.run_cleanup({"folder": "staging"}, CONFIG, adapter, dry_run=False, confirm=2)

    assert record["scope"] == "files"
    assert adapter.trashed == ["d1", "d2"]
    assert [item["group"] for item in record["targets"][0]["deleted"]] == ["files", "files"]


def test_archive_scope_targets_only_the_archive_contents():
    adapter = staging_adapter()
    record = cleanup.run_cleanup({"folder": "staging", "scope": "archive"}, CONFIG, adapter, dry_run=False, confirm=3)

    assert adapter.trashed == ["a1", "a2", "a3"]
    assert {item["group"] for item in record["targets"][0]["deleted"]} == {"archive"}


def test_both_scope_targets_each_group_and_reports_them_separately():
    adapter = staging_adapter()
    record = cleanup.run_cleanup({"folder": "staging", "scope": "both"}, CONFIG, adapter, dry_run=False, confirm=5)

    assert adapter.trashed == ["d1", "d2", "a1", "a2", "a3"]
    assert [item["group"] for item in record["targets"][0]["deleted"]] == ["files", "files", "archive", "archive", "archive"]


def test_archive_scope_without_an_archive_folder_is_a_no_op():
    adapter = CleanupAdapter(files={"staging-approved": [file_entry("d1", "Current")]}, folders={"staging-approved": []})
    record = cleanup.run_cleanup({"folder": "staging", "scope": "archive"}, CONFIG, adapter, dry_run=True)

    assert record["status"] == "no_op"
    assert adapter.trashed == []


def test_folders_are_never_trashed_including_an_emptied_archive():
    adapter = staging_adapter()
    cleanup.run_cleanup({"folder": "staging", "scope": "both"}, CONFIG, adapter, dry_run=False, confirm=5)

    assert "archive-1" not in adapter.trashed
    assert adapter.folders["staging-approved"] == [folder_entry("archive-1", "Archive")]


def test_a_dry_run_needs_no_confirmation_and_trashes_nothing():
    adapter = staging_adapter()
    record = cleanup.run_cleanup({"folder": "staging"}, CONFIG, adapter, dry_run=True)

    assert record["status"] == "dry_run"
    assert adapter.trashed == []
    assert [item["id"] for item in record["targets"][0]["undeleted"]] == ["d1", "d2"]


def test_applying_without_a_confirmation_count_refuses():
    adapter = staging_adapter()
    record = cleanup.run_cleanup({"folder": "staging"}, CONFIG, adapter, dry_run=False)

    assert record["status"] == "failed"
    assert "Confirmation required" in record["targets"][0]["error"]
    assert adapter.trashed == []


def test_a_stale_confirmation_count_refuses_and_deletes_nothing():
    adapter = staging_adapter()
    record = cleanup.run_cleanup({"folder": "staging"}, CONFIG, adapter, dry_run=False, confirm=5)

    assert record["status"] == "failed"
    assert "does not match" in record["targets"][0]["error"]
    assert adapter.trashed == []


def test_cleanup_is_disabled_by_default_in_shipped_configuration():
    disabled = {"publishing": {**CONFIG["publishing"], "cleanup": {**CONFIG["publishing"]["cleanup"], "enabled": False}}}
    with pytest.raises(cleanup.CleanupError, match="disabled"):
        cleanup.run_cleanup({"folder": "staging"}, disabled, staging_adapter(), dry_run=True)


def test_partial_failure_splits_deleted_and_undeleted():
    adapter = staging_adapter(trash_error_on="d2")
    record = cleanup.run_cleanup({"folder": "staging"}, CONFIG, adapter, dry_run=False, confirm=2)

    target = record["targets"][0]
    assert record["status"] == "failed"
    assert [item["id"] for item in target["deleted"]] == ["d1"]
    assert [item["id"] for item in target["undeleted"]] == ["d2"]


def test_an_unknown_scope_fails_closed():
    with pytest.raises(cleanup.CleanupError, match="scope must be"):
        cleanup.run_cleanup({"folder": "staging", "scope": "everything"}, CONFIG, staging_adapter(), dry_run=True)


def test_cleanup_and_archive_resolve_the_identical_effective_folder():
    """Section 3.2: divergent resolution would make one utility's dry run mislead the other."""
    def build():
        return CleanupAdapter(
            files={"parent-6": [], "week-2": [file_entry("d1", "Grade 6")]},
            folders={"parent-6": [folder_entry("week-2", "Week_2026-08-31"), folder_entry("week-1", "Week_2026-08-24")]},
        )

    request = {"folder": "publish", "grades": "grade_6", "folder_date": "latest"}
    archived = archive.run_archive(request, CONFIG, build(), dry_run=True)
    cleaned = cleanup.run_cleanup(request, CONFIG, build(), dry_run=True)

    assert archived["targets"][0]["effective_folder"] == cleaned["targets"][0]["effective_folder"]


def test_parent_mode_loose_file_refusal_is_inherited():
    adapter = CleanupAdapter(files={"parent-6": [file_entry("d1", "Stray")]}, folders={"parent-6": [folder_entry("w", "W")]})
    record = cleanup.run_cleanup({"folder": "publish", "grades": "grade_6"}, CONFIG, adapter, dry_run=True)

    assert record["status"] == "failed"
    assert "loose files" in record["targets"][0]["error"]


def test_the_cli_script_holds_no_decision_logic():
    source = (REPO / "scripts" / "cleanup_folder.py").read_text(encoding="utf-8")
    assert source.count("run_cleanup(") == 1
    for leaked in ("in parents", "list_child_files", "list_child_folders", "trash_file", "files.delete"):
        assert leaked not in source


def test_the_shipped_configuration_keeps_confirmation_and_the_safe_default_scope():
    from mts.setup_project.configure import resolve_effective_config

    resolved = resolve_effective_config(
        {"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO
    )
    settings = resolved["publishing"]["cleanup"]
    assert settings["default_scope"] == "files"
    assert settings["require_confirmation"] is True
