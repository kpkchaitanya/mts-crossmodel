"""Policy for duplicating one staged worksheet pair across subject configurations."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mts.publishing.archive import FOLDER_ID_PATTERN, parse_folder_reference, resolve_week_of


class DuplicateWorksheetError(ValueError):
    """Raised when a worksheet duplication request cannot be resolved safely."""


def duplicate_settings(config: Mapping[str, Any]) -> Mapping[str, Any]:
    settings = config.get("publishing", {}).get("duplicate_worksheet")
    if not settings:
        raise DuplicateWorksheetError("publishing.duplicate_worksheet is not configured.")
    if not settings.get("enabled", False):
        raise DuplicateWorksheetError("publishing.duplicate_worksheet.enabled is false.")
    return settings


def resolve_folder(value: str | None, config: Mapping[str, Any]) -> str:
    settings = duplicate_settings(config)
    reference = value or settings.get("default_source_folder", "staging")
    token = parse_folder_reference(reference)
    presets = settings.get("folders", {})
    if token not in presets:
        if FOLDER_ID_PATTERN.match(token):
            return token
        known = ", ".join(sorted(presets)) or "none"
        raise DuplicateWorksheetError(
            f"'{token}' is not a known duplicate folder preset ({known}) or a Drive folder ID/URL."
        )

    path = presets[token]
    current: Any = config
    for part in str(path).split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise DuplicateWorksheetError(f"Duplicate folder preset path is not configured: {path}")
        current = current[part]
    if not isinstance(current, str) or not current:
        raise DuplicateWorksheetError(f"Duplicate folder preset must resolve to a folder ID: {token}")
    return current


def _naming(config: Mapping[str, Any], worksheet_type: str) -> Mapping[str, Any]:
    kind = worksheet_type.removesuffix("-worksheet").replace("-", "_")
    naming = (config.get("naming") or {}).get(kind)
    if not naming or not naming.get("prefix_by_grade"):
        raise DuplicateWorksheetError(f"naming.{kind}.prefix_by_grade is not configured.")
    return naming


def _names(config: Mapping[str, Any], worksheet_type: str, grade: str, week: str) -> tuple[str, str]:
    naming = _naming(config, worksheet_type)
    grade = grade.strip().replace("-", "_")
    prefix = naming["prefix_by_grade"].get(grade)
    if not prefix:
        raise DuplicateWorksheetError(f"No configured naming prefix for {grade}.")
    pattern = naming.get("document_name_pattern", "{{PREFIX}}-{{WEEK_OF}}")
    stem = pattern.replace("{{PREFIX}}", prefix).replace("{{WEEK_OF}}", week)
    extension = naming.get("file_extension", "")
    return stem + extension, stem + naming.get("answer_key_suffix", "_KEY") + extension


def pair_source(files: Sequence[Mapping[str, Any]], config: Mapping[str, Any], worksheet_type: str, grade: str, week: str) -> dict[str, Any]:
    student_name, key_name = _names(config, worksheet_type, grade, week)
    student = [item for item in files if item.get("name") == student_name]
    key = [item for item in files if item.get("name") == key_name]
    if len(student) != 1 or len(key) != 1:
        raise DuplicateWorksheetError(
            f"Expected one source pair for {grade} ({student_name}); found "
            f"{len(student)} worksheet(s) and {len(key)} answer key(s)."
        )
    return {"student_worksheet": student[0], "answer_key": key[0], "week": week}


def target_names(config: Mapping[str, Any], worksheet_type: str, grade: str, week: str) -> dict[str, str]:
    student_name, key_name = _names(config, worksheet_type, grade, week)
    return {"student_worksheet": student_name, "answer_key": key_name}


def run_duplicate(
    request: Mapping[str, Any],
    source_config: Mapping[str, Any],
    target_config: Mapping[str, Any],
    adapter: Any,
    *,
    source_folder_id: str,
    target_folder_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    source_subject = request["from_subject"]
    target_subject = request["to_subject"]
    grade = str(request["from_grade"]).strip().replace("-", "_")
    target_grade = str(request["to_grade"]).strip().replace("-", "_")
    source_type = request.get("from_worksheet_type") or duplicate_settings(source_config).get(
        "default_worksheet_type", "weekly"
    )
    target_type = request.get("to_worksheet_type") or duplicate_settings(target_config).get(
        "default_worksheet_type", "weekly"
    )
    week = resolve_week_of(str(request.get("week", "current")), source_config["calendar"])
    files = adapter.list_child_files(source_folder_id)
    pair = pair_source(files, source_config, source_type, grade, week)
    names = target_names(target_config, target_type, target_grade, week)
    existing = {item.get("name") for item in adapter.list_child_files(target_folder_id)}
    collisions = [name for name in names.values() if name in existing]
    if collisions:
        raise DuplicateWorksheetError(f"Target file(s) already exist: {', '.join(collisions)}")
    record = {
        "utility": "duplicate_worksheet", "dry_run": dry_run, "status": "dry_run" if dry_run else "duplicated",
        "from_subject": source_subject, "from_grade": grade, "from_worksheet_type": source_type,
        "to_subject": target_subject, "to_grade": target_grade, "to_worksheet_type": target_type,
        "week": week, "source_folder": source_folder_id, "target_folder": target_folder_id,
        "source_pair": pair, "target_names": names,
    }
    if not dry_run:
        record["duplicated_pair"] = {
            role: adapter.copy_file(pair[role]["id"], target_folder_id, names[role])
            for role in ("student_worksheet", "answer_key")
        }
    return record
