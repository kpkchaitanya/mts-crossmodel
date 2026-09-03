"""Cleanup Folder utility: trash a folder's files, reusing Archive's resolution contract.

Deletion here always means Drive Trash, never `files.delete`, so a mistaken run stays recoverable.
See `specs/generate_math_worksheets/03. design/utility-design.md` section 3.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mts.publishing.archive import (
    ArchiveError,
    existing_archive_folder,
    overall_status,
    resolve_effective_folder,
    resolve_targets,
    week_folder_pattern_of,
)

SCOPES = ("files", "archive", "both")


class CleanupError(ArchiveError):
    """Raised when a cleanup request cannot safely proceed."""


def cleanup_settings(effective_config: Mapping[str, Any]) -> Mapping[str, Any]:
    settings = effective_config.get("publishing", {}).get("cleanup")
    if not settings:
        raise CleanupError("publishing.cleanup is not configured.")
    if not settings.get("enabled", False):
        raise CleanupError("publishing.cleanup.enabled is false; cleanup is disabled.")
    return settings


def archive_folder_name_of(effective_config: Mapping[str, Any]) -> str:
    """Cleanup never defines its own archive folder name; the two utilities must agree."""
    name = effective_config.get("publishing", {}).get("archive", {}).get("archive_folder_name")
    if not name:
        raise CleanupError("publishing.archive.archive_folder_name is required to resolve the archive folder.")
    return name


def resolve_scope(requested: Any, settings: Mapping[str, Any]) -> str:
    scope = requested or settings.get("default_scope", "files")
    if scope not in SCOPES:
        raise CleanupError(f"scope must be one of {', '.join(SCOPES)}.")
    return scope


def plan_cleanup(
    adapter: Any,
    effective_folder_id: str,
    *,
    scope: str,
    archive_folder_name: str,
) -> list[dict[str, Any]]:
    """List the files this scope would trash, tagged with the group each came from."""
    planned: list[dict[str, Any]] = []
    if scope in ("files", "both"):
        planned.extend(_tagged(adapter.list_child_files(effective_folder_id), "files"))
    if scope in ("archive", "both"):
        archive_folder = existing_archive_folder(adapter, effective_folder_id, archive_folder_name)
        # A missing archive folder contributes nothing; scope=both still works on a never-archived folder.
        if archive_folder.get("id"):
            planned.extend(_tagged(adapter.list_child_files(archive_folder["id"]), "archive"))
    return planned


def _tagged(items: Sequence[Mapping[str, Any]], group: str) -> list[dict[str, Any]]:
    return [
        {"id": item["id"], "name": item.get("name"), "webViewLink": item.get("webViewLink"), "group": group}
        for item in items
    ]


def check_confirmation(planned_count: int, confirm: int | None, settings: Mapping[str, Any]) -> None:
    """A dry run is not authorization; the folder can change before the apply."""
    if not settings.get("require_confirmation", True):
        return
    if confirm is None:
        raise CleanupError(f"Confirmation required: re-run with the planned file count ({planned_count}).")
    if confirm != planned_count:
        raise CleanupError(
            f"Confirmation count {confirm} does not match the {planned_count} files planned now. "
            "Nothing was deleted; re-run the dry run."
        )


def run_cleanup(
    request: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    adapter: Any,
    *,
    dry_run: bool = True,
    confirm: int | None = None,
) -> dict[str, Any]:
    """Resolve, plan, and apply cleanup for every target, returning one Cleanup Record."""
    settings = cleanup_settings(effective_config)
    scope = resolve_scope(request.get("scope"), settings)
    archive_folder_name = archive_folder_name_of(effective_config)
    week_folder_pattern = week_folder_pattern_of(effective_config)
    targets = resolve_targets(request, effective_config)

    target_records: list[dict[str, Any]] = []
    for target in targets:
        try:
            target_records.append(
                _cleanup_one(
                    target,
                    adapter,
                    settings=settings,
                    scope=scope,
                    archive_folder_name=archive_folder_name,
                    folder_date=request.get("folder_date"),
                    week_folder_pattern=week_folder_pattern,
                    dry_run=dry_run,
                    confirm=confirm,
                )
            )
        except Exception as error:  # recorded per target so one failure cannot hide the rest
            target_records.append(
                _record(target, {"id": target["folder_id"]}, [], [], status="failed", error=str(error))
            )

    return {
        "utility": "cleanup_folder",
        "dry_run": dry_run,
        "status": overall_status(target_records, applied_status="cleaned"),
        "scope": scope,
        "request": dict(request),
        "archive_folder_name": archive_folder_name,
        "targets": target_records,
    }


def _cleanup_one(
    target: Mapping[str, Any],
    adapter: Any,
    *,
    settings: Mapping[str, Any],
    scope: str,
    archive_folder_name: str,
    folder_date: str | None,
    week_folder_pattern: str | None,
    dry_run: bool,
    confirm: int | None,
) -> dict[str, Any]:
    effective_folder = resolve_effective_folder(
        target,
        adapter,
        archive_folder_name=archive_folder_name,
        folder_date=folder_date,
        week_folder_pattern=week_folder_pattern,
    )
    planned = plan_cleanup(
        adapter, effective_folder["id"], scope=scope, archive_folder_name=archive_folder_name
    )
    if not planned:
        return _record(target, effective_folder, [], [], status="no_op")
    if dry_run:
        return _record(target, effective_folder, [], planned, status="dry_run")

    check_confirmation(len(planned), confirm, settings)

    deleted: list[dict[str, Any]] = []
    for index, item in enumerate(planned):
        try:
            adapter.trash_file(item["id"])
        except Exception as error:
            return _record(
                target, effective_folder, deleted, planned[index:], status="failed", error=str(error)
            )
        deleted.append(item)
    return _record(target, effective_folder, deleted, [], status="cleaned")


def _record(
    target: Mapping[str, Any],
    effective_folder: Mapping[str, Any],
    deleted: Sequence[Mapping[str, Any]],
    undeleted: Sequence[Mapping[str, Any]],
    *,
    status: str,
    error: str | None = None,
) -> dict[str, Any]:
    record = {
        **{key: target[key] for key in ("label", "folder_id", "folder_type") if key in target},
        "status": status,
        "effective_folder": dict(effective_folder),
        "deleted": [dict(item) for item in deleted],
        "undeleted": [dict(item) for item in undeleted],
    }
    if "grade_id" in target:
        record["grade_id"] = target["grade_id"]
    if error:
        record["error"] = error
    return record


__all__ = [
    "CleanupError",
    "archive_folder_name_of",
    "check_confirmation",
    "cleanup_settings",
    "plan_cleanup",
    "resolve_scope",
    "run_cleanup",
]
