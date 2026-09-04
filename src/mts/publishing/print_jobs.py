"""Print Worksheets utility policy: decide what to print and how many copies, with no I/O.

Folder resolution comes from `archive` and grade/role pairing from `deliver`, so this utility can
never disagree with the rest of publishing about which document belongs to which grade. The only
decision that lives here is the per-grade copy count.

See `specs/generate_math_worksheets/03. design/utility-design.md` section 6.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mts.publishing import deliver
from mts.publishing.archive import (
    ArchiveError,
    check_subject_matches,
    overall_status,
    resolve_effective_folder,
    resolve_targets,
    resolve_week_of,
    week_folder_pattern_of,
)

ROLES = ("student_worksheet", "answer_key")
INCLUDE_ROLES = {"both": ROLES, "worksheet": ("student_worksheet",), "key": ("answer_key",)}


class PrintError(ArchiveError):
    """Raised when a print request cannot safely proceed."""


def printing_settings(effective_config: Mapping[str, Any]) -> Mapping[str, Any]:
    settings = effective_config.get("publishing", {}).get("printing")
    if not settings:
        raise PrintError("publishing.printing is not configured.")
    if not settings.get("enabled", False):
        raise PrintError("publishing.printing.enabled is false; printing is disabled.")
    return settings


def resolve_source(requested: Any, settings: Mapping[str, Any]) -> str:
    source = requested or settings.get("default_source", "staging")
    if source not in ("staging", "publish"):
        raise PrintError("source must be 'staging' or 'publish'.")
    return source


def resolve_roles(include: Any) -> tuple[str, ...]:
    key = include or "both"
    if key not in INCLUDE_ROLES:
        raise PrintError(f"include must be one of {', '.join(INCLUDE_ROLES)}.")
    return INCLUDE_ROLES[key]


def parse_copy_overrides(value: Any) -> dict[str, dict[str, int]]:
    """Parse `grade_5=6,grade_6=3:2` into per-grade worksheet (and optional key) copy counts."""
    if not value:
        return {}
    overrides: dict[str, dict[str, int]] = {}
    for item in str(value).split(","):
        entry = item.strip()
        if not entry:
            continue
        if "=" not in entry:
            raise PrintError(f"copies override '{entry}' must look like grade_5=6 or grade_5=6:1.")
        grade_id, counts = entry.split("=", 1)
        parts = counts.split(":")
        if len(parts) > 2:
            raise PrintError(f"copies override '{entry}' must have at most one ':' separator.")
        try:
            numbers = [int(part) for part in parts]
        except ValueError:
            raise PrintError(f"copies override '{entry}' must use whole numbers.") from None
        if any(number < 0 for number in numbers):
            raise PrintError(f"copies override '{entry}' must not be negative.")
        override = {"student_worksheet": numbers[0]}
        if len(numbers) == 2:
            override["answer_key"] = numbers[1]
        overrides[deliver.normalize_grade_id(grade_id)] = override
    return overrides


def requested_grade_ids(grades: Any, naming: Mapping[str, Any]) -> tuple[list[str], bool]:
    """Return the grades to consider and whether the user named them explicitly."""
    prefixes = naming["prefix_by_grade"]
    if grades in (None, "", "all"):
        return sorted(prefixes), False
    selected = [deliver.normalize_grade_id(g) for g in str(grades).split(",") if g.strip()]
    missing = [grade_id for grade_id in selected if grade_id not in prefixes]
    if missing:
        raise PrintError(f"No configured naming prefix for: {', '.join(missing)}")
    return selected, True


def resolve_copies(
    settings: Mapping[str, Any],
    grade_id: str,
    overrides: Mapping[str, Mapping[str, int]],
) -> dict[str, int] | None:
    """Merge configured and overridden copy counts; `None` means this grade is not set up to print."""
    configured = (settings.get("copies_by_grade") or {}).get(grade_id)
    override = overrides.get(grade_id)
    if configured is None and override is None:
        return None
    counts = {role: int(value) for role, value in (configured or {}).items() if role in ROLES}
    counts.update({role: int(value) for role, value in (override or {}).items()})
    if any(value < 0 for value in counts.values()):
        raise PrintError(f"Copy counts for {grade_id} must not be negative.")
    return counts


def check_copy_counts_configured(
    settings: Mapping[str, Any],
    grade_ids: Sequence[str],
    overrides: Mapping[str, Mapping[str, int]],
) -> None:
    """Refuse an explicitly named grade with no copy policy; `grades=all` skips it instead."""
    missing = [grade_id for grade_id in grade_ids if resolve_copies(settings, grade_id, overrides) is None]
    if missing:
        raise PrintError(f"No configured print copy counts for: {', '.join(missing)}")


def plan_jobs(
    pairs: Mapping[str, Mapping[str, Any]],
    grade_ids: Sequence[str],
    *,
    settings: Mapping[str, Any],
    overrides: Mapping[str, Mapping[str, int]],
    roles: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expand paired documents into one print job per document, or record why there is none."""
    jobs: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for grade_id in grade_ids:
        counts = resolve_copies(settings, grade_id, overrides)
        if counts is None:
            issues.append({"grade_id": grade_id, "reason": "no_copy_counts_configured"})
            continue
        pair = pairs.get(grade_id)
        if not pair:
            issues.append({"grade_id": grade_id, "reason": "missing_pair"})
            continue
        for role in roles:
            copies = counts.get(role, 0)
            if copies < 1:
                continue
            document = pair[role]
            jobs.append({
                "grade_id": grade_id,
                "role": role,
                "document_id": document["id"],
                "name": document.get("name"),
                "copies": copies,
            })
    return jobs, issues


def check_confirmation(planned_copies: int, confirm: int | None, settings: Mapping[str, Any]) -> None:
    """A dry run is not authorization; staging can change, and paper is not undoable."""
    if not settings.get("require_confirmation", True):
        return
    if confirm is None:
        raise PrintError(f"Confirmation required: re-run with the planned copy total ({planned_copies}).")
    if confirm != planned_copies:
        raise PrintError(
            f"Confirmation count {confirm} does not match the {planned_copies} copies planned now. "
            "Nothing was printed; re-run the dry run."
        )


def run_print(
    request: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    adapter: Any,
    printer: Any = None,
    *,
    dry_run: bool = True,
    confirm: int | None = None,
) -> dict[str, Any]:
    """Resolve, plan, and optionally spool every print job, returning one Print Record."""
    check_subject_matches(request, effective_config)
    settings = printing_settings(effective_config)
    source = resolve_source(request.get("source"), settings)
    roles = resolve_roles(request.get("include"))
    overrides = parse_copy_overrides(request.get("copies"))
    week_of = resolve_week_of(request.get("week"), effective_config.get("calendar", {}))
    naming = deliver.naming_settings(effective_config)
    grade_ids, explicit_grades = requested_grade_ids(request.get("grades"), naming)
    if explicit_grades:
        check_copy_counts_configured(settings, grade_ids, overrides)
    archive_folder_name = effective_config.get("publishing", {}).get("archive", {}).get("archive_folder_name")
    week_folder_pattern = week_folder_pattern_of(effective_config)
    targets = resolve_targets({"folder": source, "grades": request.get("grades")}, effective_config)
    # Destinations are shared per-grade folders; a grade this subject does not produce is not a failure.
    targets, skipped_targets = _restrict_targets_to_named_grades(targets, naming, request.get("grades"))

    target_records: list[dict[str, Any]] = []
    planned: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for target in skipped_targets:
        target_records.append(
            _record(
                target,
                {"id": target["folder_id"]},
                [],
                [],
                status="no_op",
                issues=[{"grade_id": target["grade_id"], "reason": "no_naming_for_subject"}],
            )
        )
    for target in targets:
        try:
            effective_folder = resolve_effective_folder(
                target,
                adapter,
                archive_folder_name=archive_folder_name,
                # Parent mode prints the week being requested, never whichever folder is newest.
                folder_date=week_of if target["folder_type"] == "parent" else None,
                week_folder_pattern=week_folder_pattern,
            )
            target_grade_ids = [target["grade_id"]] if "grade_id" in target else grade_ids
            pairs, pairing_issues = deliver.pair_from_staging(
                adapter.list_child_files(effective_folder["id"]),
                week_of=week_of,
                naming=naming,
                grade_ids=target_grade_ids,
            )
            jobs, copy_issues = plan_jobs(
                pairs,
                target_grade_ids,
                settings=settings,
                overrides=overrides,
                roles=roles,
            )
            record = _record(target, effective_folder, [], jobs, status="dry_run", issues=pairing_issues + copy_issues)
            planned.append((record, jobs))
            target_records.append(record)
        except Exception as error:  # recorded per target so one failure cannot hide the rest
            target_records.append(
                _record(target, {"id": target["folder_id"]}, [], [], status="failed", error=str(error))
            )

    total_copies = sum(job["copies"] for _, jobs in planned for job in jobs)
    for record, jobs in planned:
        if not jobs:
            record["status"] = "no_op"

    if not dry_run:
        # One check against the whole plan: a mismatch prints nothing anywhere.
        check_confirmation(total_copies, confirm, settings)
        for record, jobs in planned:
            if jobs:
                _print_jobs(record, jobs, adapter, printer)

    return {
        "utility": "print_worksheets",
        "dry_run": dry_run,
        "status": overall_status(target_records, applied_status="printed"),
        "week_of": week_of,
        "source": source,
        "include": request.get("include") or "both",
        "printer_name": settings.get("printer_name"),
        "duplex": settings.get("duplex", "simplex"),
        "planned_copies": total_copies,
        "request": dict(request),
        "targets": target_records,
    }


def _restrict_targets_to_named_grades(
    targets: Sequence[Mapping[str, Any]], naming: Mapping[str, Any], grades: Any
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Reuse delivery's rule so print and deliver agree on which grades a subject covers."""
    graded = [target for target in targets if "grade_id" in target]
    if not graded:
        return [dict(target) for target in targets], []
    kept, issues = deliver.restrict_to_named_grades(graded, naming, grades)
    skipped_ids = {issue["grade_id"] for issue in issues}
    return kept, [dict(target) for target in graded if target["grade_id"] in skipped_ids]


def _print_jobs(record: dict[str, Any], jobs: Sequence[Mapping[str, Any]], adapter: Any, printer: Any) -> None:
    if printer is None:
        raise PrintError("A printer is required to apply a print run.")
    for index, job in enumerate(jobs):
        try:
            content = adapter.export_pdf(job["document_id"])
            result = printer.print_pdf(content, name=job["name"] or job["document_id"], copies=job["copies"])
        except Exception as error:
            record["status"] = "failed"
            record["error"] = str(error)
            record["unprinted"] = [dict(item) for item in jobs[index:]]
            return
        record["printed"].append({**dict(job), "result": result})
    record["status"] = "printed"
    record["unprinted"] = []


def _record(
    target: Mapping[str, Any],
    effective_folder: Mapping[str, Any],
    printed: Sequence[Mapping[str, Any]],
    unprinted: Sequence[Mapping[str, Any]],
    *,
    status: str,
    issues: Sequence[Mapping[str, Any]] = (),
    error: str | None = None,
) -> dict[str, Any]:
    record = {
        **{key: target[key] for key in ("label", "folder_id", "folder_type") if key in target},
        "status": status,
        "effective_folder": dict(effective_folder),
        "printed": [dict(item) for item in printed],
        "unprinted": [dict(item) for item in unprinted],
        "issues": [dict(item) for item in issues],
    }
    if "grade_id" in target:
        record["grade_id"] = target["grade_id"]
    if error:
        record["error"] = error
    return record


__all__ = [
    "PrintError",
    "check_copy_counts_configured",
    "parse_copy_overrides",
    "plan_jobs",
    "printing_settings",
    "resolve_copies",
    "resolve_roles",
    "resolve_source",
    "run_print",
]
