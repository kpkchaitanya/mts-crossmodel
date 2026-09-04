"""Archive Folder utility policy: decides what to archive and where, with no Google Drive I/O.

Every function here takes plain listings plus resolved configuration so the same decisions can be
reused by the CLI today and by the publishing pipeline later. See
`specs/generate_math_worksheets/03. design/utility-design.md` section 2.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any
import re

FOLDER_URL_PATTERN = re.compile(r"/folders/([A-Za-z0-9_-]+)")
FOLDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{12,}$")
FOLDER_TYPES = ("folder", "parent")


class ArchiveError(ValueError):
    """Raised when an archive request cannot safely proceed."""


def archive_settings(effective_config: Mapping[str, Any]) -> Mapping[str, Any]:
    settings = effective_config.get("publishing", {}).get("archive")
    if not settings:
        raise ArchiveError("publishing.archive is not configured.")
    if not settings.get("enabled", False):
        raise ArchiveError("publishing.archive.enabled is false; archiving is disabled.")
    return settings


def parse_folder_reference(value: str) -> str:
    """Reduce a preset name, Drive folder URL, or raw folder ID to its identifying token."""
    if not isinstance(value, str) or not value.strip():
        raise ArchiveError("folder is required.")
    token = value.strip()
    url_match = FOLDER_URL_PATTERN.search(token)
    if url_match:
        return url_match.group(1)
    return token


def resolve_week_of(value: str, calendar: Mapping[str, Any]) -> str:
    """Resolve 'current', an instructional week number, or a date to that week's ISO Monday.

    Canonical implementation shared with `mts.publishing.deliver`, which re-exports this function
    rather than defining its own, so the two utilities can never disagree about week resolution.
    """
    week_1_start = date.fromisoformat(str(calendar["week_1_start"]))
    if value in (None, "", "current"):
        today = date.today()
        return date.fromordinal(today.toordinal() - today.weekday()).isoformat()
    text = str(value)
    if text.isdigit():
        return date.fromordinal(week_1_start.toordinal() + 7 * (int(text) - 1)).isoformat()
    parsed = date.fromisoformat(text)
    return date.fromordinal(parsed.toordinal() - parsed.weekday()).isoformat()


def naming_prefixes(effective_config: Mapping[str, Any], worksheet_kind: str = "weekly") -> Mapping[str, str]:
    """Return the grade->document-name-prefix mapping used both to render and to filter files."""
    naming = effective_config.get("naming", {}).get(worksheet_kind)
    if not naming or not naming.get("prefix_by_grade"):
        raise ArchiveError(f"naming.{worksheet_kind}.prefix_by_grade is not configured for this subject.")
    return naming["prefix_by_grade"]


def check_subject_matches(request: Mapping[str, Any], effective_config: Mapping[str, Any]) -> None:
    """Fail closed if a request's `subject` filter disagrees with the loaded configuration.

    Canonical implementation shared with `mts.publishing.deliver`, which re-exports this function.
    """
    subject = request.get("subject")
    if subject and subject != effective_config.get("subject"):
        raise ArchiveError(
            f"subject filter '{subject}' does not match the loaded configuration's subject "
            f"'{effective_config.get('subject')}'."
        )


def build_content_filter(
    request: Mapping[str, Any], effective_config: Mapping[str, Any], *, apply_grade_filter: bool = True
):
    """Build an optional file-name filter from `grades`, `subject`, and `week` request fields.

    Returns `None` when none apply, which preserves archive's default content-blind behavior: every
    loose file in a resolved folder is archived, exactly as before this filter existed.

    `apply_grade_filter=False` ignores `grades` here because it was already used to select *which*
    target folder to archive (the `publish` preset's per-grade parent-mode targets); re-applying it as
    a name filter inside that already-scoped folder would silently exclude legitimately-named files
    and change archive's established content-blind behavior for that case. `subject` and `week` carry
    no such prior meaning, so they always apply.
    """
    grades = request.get("grades") if apply_grade_filter else None
    subject = request.get("subject")
    week = request.get("week")
    has_grade_filter = grades not in (None, "", "all")
    has_subject_filter = bool(subject)
    has_week_filter = bool(week)
    if not (has_grade_filter or has_subject_filter or has_week_filter):
        return None

    wanted_prefixes: tuple[str, ...] | None = None
    if has_grade_filter or has_subject_filter:
        prefixes = naming_prefixes(effective_config)
        if has_grade_filter:
            grade_ids = [g.strip().replace("-", "_") for g in str(grades).split(",") if g.strip()]
            missing = [grade_id for grade_id in grade_ids if grade_id not in prefixes]
            if missing:
                raise ArchiveError(f"No configured naming prefix for: {', '.join(missing)}")
        else:
            grade_ids = list(prefixes)  # subject filter alone matches any of that subject's grades
        wanted_prefixes = tuple(prefixes[grade_id] for grade_id in grade_ids)

    week_of: str | None = None
    if has_week_filter:
        week_of = resolve_week_of(week, effective_config.get("calendar", {}))

    def matcher(name: str) -> bool:
        if wanted_prefixes is not None and not name.startswith(wanted_prefixes):
            return False
        if week_of is not None and week_of not in name:
            return False
        return True

    return matcher


def resolve_targets(request: Mapping[str, Any], effective_config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Expand a request into one or more `(label, folder_id, folder_type)` targets."""
    settings = archive_settings(effective_config)
    token = parse_folder_reference(request.get("folder"))
    presets = settings.get("targets", {})
    requested_type = request.get("folder_type")

    if token in presets:
        preset = presets[token]
        folder_type = _validate_folder_type(requested_type or preset.get("folder_type"))
        targets = _expand_preset(token, preset, folder_type, effective_config, request.get("grades"))
    else:
        if not FOLDER_ID_PATTERN.match(token):
            known = ", ".join(sorted(presets)) or "none"
            raise ArchiveError(f"'{token}' is not a known preset ({known}) or a Drive folder ID/URL.")
        if not requested_type:
            raise ArchiveError("folder_type is required when folder is a raw Drive folder ID or URL.")
        folder_type = _validate_folder_type(requested_type)
        targets = [{"label": token, "folder_id": token, "folder_type": folder_type}]

    folder_date = request.get("folder_date")
    if folder_date and any(target["folder_type"] == "folder" for target in targets):
        raise ArchiveError("folder_date applies to parent mode only.")
    return targets


def _validate_folder_type(value: Any) -> str:
    if value not in FOLDER_TYPES:
        raise ArchiveError(f"folder_type must be one of {', '.join(FOLDER_TYPES)}.")
    return value


def _expand_preset(
    name: str,
    preset: Mapping[str, Any],
    folder_type: str,
    effective_config: Mapping[str, Any],
    grades: Any,
) -> list[dict[str, Any]]:
    source = _read_config_path(effective_config, preset.get("source", ""))
    if isinstance(source, str):
        return [{"label": name, "folder_id": source, "folder_type": folder_type}]
    if not isinstance(source, Mapping):
        raise ArchiveError(f"Preset '{name}' source must resolve to a folder ID or a mapping of destinations.")

    selected = _select_grades(grades, source)
    return [
        {
            "label": source[grade_id].get("label", grade_id),
            "grade_id": grade_id,
            "folder_id": source[grade_id]["folder_id"],
            "folder_type": folder_type,
        }
        for grade_id in selected
    ]


def _select_grades(grades: Any, destinations: Mapping[str, Any]) -> list[str]:
    if grades in (None, "", "all"):
        return sorted(destinations)
    requested = [g.strip().replace("-", "_") for g in str(grades).split(",") if g.strip()]
    missing = [grade_id for grade_id in requested if grade_id not in destinations]
    if missing:
        raise ArchiveError(f"No configured destination for: {', '.join(missing)}")
    return requested


def _read_config_path(effective_config: Mapping[str, Any], path: str) -> Any:
    if not path:
        raise ArchiveError("Preset source path is required.")
    current: Any = effective_config
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ArchiveError(f"Preset source path is not present in configuration: {path}")
        current = current[part]
    return current


def resolve_folder_name_for_date(value: str, week_folder_pattern: str | None) -> str:
    """Map an ISO date to its week folder name, reusing the delivery naming contract."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return value
    if not week_folder_pattern:
        raise ArchiveError("publishing.final_delivery.week_folder_pattern is required to resolve a folder date.")
    monday = date.fromordinal(parsed.toordinal() - parsed.weekday()).isoformat()
    return week_folder_pattern.replace("{{WEEK_OF}}", monday)


def select_effective_folder(
    child_folders: Sequence[Mapping[str, Any]],
    *,
    folder_date: str | None,
    archive_folder_name: str,
    week_folder_pattern: str | None = None,
) -> dict[str, Any]:
    """Choose the parent-mode child folder to archive inside, never the archive folder itself."""
    candidates = [folder for folder in child_folders if folder.get("name") != archive_folder_name]
    if not candidates:
        raise ArchiveError("Parent folder has no eligible child folder to archive.")
    if folder_date in (None, "", "latest"):
        return dict(candidates[0])

    wanted = resolve_folder_name_for_date(folder_date, week_folder_pattern)
    matches = [folder for folder in candidates if folder.get("name") == wanted]
    if len(matches) > 1:
        raise ArchiveError(f"Ambiguous child folder '{wanted}'.")
    if not matches:
        available = ", ".join(folder.get("name", "?") for folder in candidates)
        raise ArchiveError(f"No child folder named '{wanted}'. Available: {available}")
    return dict(matches[0])


def check_parent_has_no_loose_files(child_files: Sequence[Mapping[str, Any]]) -> None:
    """Parent mode is defined only for a parent with no loose files; never guess otherwise."""
    if child_files:
        names = ", ".join(item.get("name", "?") for item in child_files)
        raise ArchiveError(f"Parent folder contains loose files; use folder mode explicitly. Found: {names}")


def plan_archive(child_files: Sequence[Mapping[str, Any]], *, content_filter=None) -> list[dict[str, Any]]:
    """Build the move plan; an empty listing yields an empty plan, which is a valid no-op.

    `content_filter`, when given, restricts the plan to matching files only. With no filter, archiving
    stays content-blind by default: every loose file is planned, exactly as before filters existed.
    """
    matched = child_files if content_filter is None else [
        item for item in child_files if content_filter(item.get("name", ""))
    ]
    return [
        {"id": item["id"], "name": item.get("name"), "webViewLink": item.get("webViewLink")}
        for item in matched
    ]


def build_target_record(
    target: Mapping[str, Any],
    *,
    effective_folder: Mapping[str, Any],
    archive_folder: Mapping[str, Any] | None,
    moved: Sequence[Mapping[str, Any]],
    unmoved: Sequence[Mapping[str, Any]],
    status: str,
    error: str | None = None,
    filtered_out: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    record = {
        **{key: target[key] for key in ("label", "folder_id", "folder_type") if key in target},
        "status": status,
        "effective_folder": dict(effective_folder),
        "archive_folder": dict(archive_folder) if archive_folder else None,
        "moved": [dict(item) for item in moved],
        "unmoved": [dict(item) for item in unmoved],
        "filtered_out": [
            {"id": item["id"], "name": item.get("name")} for item in filtered_out
        ],
    }
    if "grade_id" in target:
        record["grade_id"] = target["grade_id"]
    if error:
        record["error"] = error
    return record


def resolve_effective_folder(
    target: Mapping[str, Any],
    adapter: Any,
    *,
    archive_folder_name: str,
    folder_date: str | None,
    week_folder_pattern: str | None,
) -> dict[str, Any]:
    """Resolve one target to the single folder to act on. Shared by archive and cleanup."""
    folder_id = target["folder_id"]
    if target["folder_type"] != "parent":
        return {"id": folder_id}
    check_parent_has_no_loose_files(adapter.list_child_files(folder_id))
    return select_effective_folder(
        adapter.list_child_folders(folder_id),
        folder_date=folder_date,
        archive_folder_name=archive_folder_name,
        week_folder_pattern=week_folder_pattern,
    )


def existing_archive_folder(adapter: Any, folder_id: str, archive_folder_name: str) -> dict[str, Any]:
    """Report the archive folder without creating it, so a dry run mutates nothing."""
    matches = [
        folder for folder in adapter.list_child_folders(folder_id)
        if folder.get("name") == archive_folder_name
    ]
    if len(matches) > 1:
        raise ArchiveError(f"Ambiguous archive folder '{archive_folder_name}' under {folder_id}.")
    if matches:
        return {**matches[0], "created": False}
    return {"id": None, "name": archive_folder_name, "created": False, "would_create": True}


def week_folder_pattern_of(effective_config: Mapping[str, Any]) -> str | None:
    return effective_config.get("publishing", {}).get("final_delivery", {}).get("week_folder_pattern")


def overall_status(target_records: Sequence[Mapping[str, Any]], *, applied_status: str) -> str:
    statuses = {record["status"] for record in target_records}
    if "failed" in statuses:
        return "failed"
    if statuses == {"no_op"}:
        return "no_op"
    if "dry_run" in statuses:
        return "dry_run"
    return applied_status


def run_archive(
    request: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    adapter: Any,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Resolve, plan, and apply archiving for every target, returning one Archive Record."""
    check_subject_matches(request, effective_config)
    settings = archive_settings(effective_config)
    archive_folder_name = settings["archive_folder_name"]
    week_folder_pattern = week_folder_pattern_of(effective_config)
    targets = resolve_targets(request, effective_config)

    target_records: list[dict[str, Any]] = []
    for target in targets:
        try:
            content_filter = build_content_filter(
                request, effective_config, apply_grade_filter=target["folder_type"] == "folder"
            )
            target_records.append(
                _archive_one(
                    target,
                    adapter,
                    archive_folder_name=archive_folder_name,
                    folder_date=request.get("folder_date"),
                    week_folder_pattern=week_folder_pattern,
                    dry_run=dry_run,
                    content_filter=content_filter,
                )
            )
        except Exception as error:  # recorded per target so one failure cannot hide the rest
            target_records.append(
                build_target_record(
                    target,
                    effective_folder={"id": target["folder_id"]},
                    archive_folder=None,
                    moved=[],
                    unmoved=[],
                    status="failed",
                    error=str(error),
                )
            )

    return {
        "utility": "archive_folder",
        "dry_run": dry_run,
        "status": overall_status(target_records, applied_status="archived"),
        "request": dict(request),
        "archive_folder_name": archive_folder_name,
        "targets": target_records,
    }


def _archive_one(
    target: Mapping[str, Any],
    adapter: Any,
    *,
    archive_folder_name: str,
    folder_date: str | None,
    week_folder_pattern: str | None,
    dry_run: bool,
    content_filter=None,
) -> dict[str, Any]:
    effective_folder = resolve_effective_folder(
        target,
        adapter,
        archive_folder_name=archive_folder_name,
        folder_date=folder_date,
        week_folder_pattern=week_folder_pattern,
    )

    all_files = adapter.list_child_files(effective_folder["id"])
    if content_filter is None:
        eligible, filtered_out = all_files, []
    else:
        eligible = [item for item in all_files if content_filter(item.get("name", ""))]
        eligible_ids = {item["id"] for item in eligible}
        filtered_out = [item for item in all_files if item["id"] not in eligible_ids]

    planned = plan_archive(eligible)
    if not planned:
        return build_target_record(
            target,
            effective_folder=effective_folder,
            archive_folder=existing_archive_folder(adapter, effective_folder["id"], archive_folder_name),
            moved=[],
            unmoved=[],
            status="no_op",
            filtered_out=filtered_out,
        )

    if dry_run:
        return build_target_record(
            target,
            effective_folder=effective_folder,
            archive_folder=existing_archive_folder(adapter, effective_folder["id"], archive_folder_name),
            moved=[],
            unmoved=planned,
            status="dry_run",
            filtered_out=filtered_out,
        )

    archive_folder = adapter.ensure_child_folder(effective_folder["id"], archive_folder_name)
    moved: list[dict[str, Any]] = []
    for index, item in enumerate(planned):
        try:
            result = adapter.move_file(item["id"], archive_folder["id"])
        except Exception as error:
            return build_target_record(
                target,
                effective_folder=effective_folder,
                archive_folder=archive_folder,
                moved=moved,
                unmoved=planned[index:],
                status="failed",
                error=str(error),
                filtered_out=filtered_out,
            )
        moved.append({**item, "webViewLink": result.get("webViewLink", item.get("webViewLink"))})
    return build_target_record(
        target,
        effective_folder=effective_folder,
        archive_folder=archive_folder,
        moved=moved,
        unmoved=[],
        status="archived",
        filtered_out=filtered_out,
    )


__all__ = [
    "ArchiveError",
    "archive_settings",
    "build_content_filter",
    "build_target_record",
    "check_parent_has_no_loose_files",
    "check_subject_matches",
    "existing_archive_folder",
    "naming_prefixes",
    "overall_status",
    "parse_folder_reference",
    "plan_archive",
    "resolve_effective_folder",
    "resolve_folder_name_for_date",
    "resolve_targets",
    "resolve_week_of",
    "run_archive",
    "select_effective_folder",
    "week_folder_pattern_of",
]
