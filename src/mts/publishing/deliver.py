"""Final Delivery policy shared by the generate-worksheet workflow and the delivery utility.

Pairing (which document belongs to which grade, and which is the answer key) comes from a run's
published artifacts when a run root is available, and from staging document names otherwise. Name
matching never guesses: an ambiguous or incomplete match is reported, not resolved.

See `specs/generate_math_worksheets/03. design/utility-design.md` section 4.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
import json

from mts.publishing import archive as archive_policy
from mts.publishing.archive import resolve_week_of  # noqa: F401  (re-exported: single implementation)


class DeliveryError(ValueError):
    """Raised when a delivery request cannot safely proceed."""


def delivery_settings(effective_config: Mapping[str, Any]) -> Mapping[str, Any]:
    settings = effective_config.get("publishing", {}).get("final_delivery")
    if not settings:
        raise DeliveryError("publishing.final_delivery is not configured.")
    if not settings.get("enabled", False):
        raise DeliveryError("publishing.final_delivery.enabled is false; delivery is disabled.")
    return settings


def check_subject_matches(request: Mapping[str, Any], effective_config: Mapping[str, Any]) -> None:
    """Fail closed if a request's `subject` filter disagrees with the loaded configuration.

    Reuses `archive.check_subject_matches`'s logic so the two utilities can never disagree about what
    counts as a mismatch, while still raising `DeliveryError` for callers of this module.
    """
    try:
        archive_policy.check_subject_matches(request, effective_config)
    except archive_policy.ArchiveError as error:
        raise DeliveryError(str(error)) from error


def naming_settings(effective_config: Mapping[str, Any], worksheet_kind: str = "weekly") -> Mapping[str, Any]:
    naming = effective_config.get("naming", {}).get(worksheet_kind)
    if not naming or not naming.get("prefix_by_grade"):
        raise DeliveryError(f"naming.{worksheet_kind}.prefix_by_grade is not configured for this subject.")
    return naming


def normalize_grade_id(value: str) -> str:
    return str(value).strip().replace("-", "_")


def week_folder_name(week_of: str, settings: Mapping[str, Any]) -> str:
    return settings["week_folder_pattern"].replace("{{WEEK_OF}}", week_of)


def resolve_destinations(settings: Mapping[str, Any], grades: Any) -> list[dict[str, Any]]:
    """Resolve requested grades to configured destinations; an unconfigured grade fails closed."""
    destinations = settings.get("destinations_by_grade") or {}
    if not destinations:
        raise DeliveryError("publishing.final_delivery.destinations_by_grade is not configured.")
    if grades in (None, "", "all"):
        selected = sorted(destinations)
    else:
        selected = [normalize_grade_id(g) for g in str(grades).split(",") if g.strip()]
        missing = [grade_id for grade_id in selected if grade_id not in destinations]
        if missing:
            raise DeliveryError(f"No configured Final Delivery destination for: {', '.join(missing)}")
    return [
        {
            "grade_id": grade_id,
            "folder_id": destinations[grade_id]["folder_id"],
            "label": destinations[grade_id].get("label", grade_id),
        }
        for grade_id in selected
    ]


def document_names(naming: Mapping[str, Any], grade_id: str, week_of: str) -> tuple[str, str]:
    prefix = naming["prefix_by_grade"].get(grade_id)
    if not prefix:
        raise DeliveryError(f"No configured document name prefix for {grade_id}.")
    student = naming["document_name_pattern"].replace("{{PREFIX}}", prefix).replace("{{WEEK_OF}}", week_of)
    return student, student + naming["answer_key_suffix"]


def pair_from_run_root(run_root: Path) -> tuple[dict[str, dict[str, Any]], str]:
    """Read exact per-grade document pairs recorded by the run that produced them."""
    for filename in ("published-artifacts.json", "rendered-artifacts.json"):
        path = run_root / filename
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "pairs" in payload:
            pairs = {
                normalize_grade_id(grade_id): {
                    "student_worksheet": pair["student_worksheet"],
                    "answer_key": pair["answer_key"],
                }
                for grade_id, pair in payload["pairs"].items()
            }
        else:
            pairs = {
                normalize_grade_id(entry["worksheet_id"]): {
                    "student_worksheet": entry["worksheet"],
                    "answer_key": entry["answer_key"],
                }
                for entry in payload["artifacts"]
            }
        return pairs, filename
    raise DeliveryError(f"No published-artifacts.json or rendered-artifacts.json under {run_root}")


def pair_from_staging(
    files: Sequence[Mapping[str, Any]],
    *,
    week_of: str,
    naming: Mapping[str, Any],
    grade_ids: Sequence[str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Pair staging documents to grades by name. Ambiguity is reported, never resolved."""
    pairs: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, Any]] = []
    matched_ids: set[str] = set()

    for grade_id in grade_ids:
        student_name, key_name = document_names(naming, grade_id, week_of)
        student = [item for item in files if item.get("name") == student_name]
        answer_key = [item for item in files if item.get("name") == key_name]
        ambiguous = {
            role: [item["id"] for item in found]
            for role, found in (("student_worksheet", student), ("answer_key", answer_key))
            if len(found) > 1
        }
        if ambiguous:
            issues.append({"grade_id": grade_id, "reason": "ambiguous_name", "documents": ambiguous})
            continue
        if not student or not answer_key:
            issues.append({
                "grade_id": grade_id,
                "reason": "incomplete_pair",
                "expected": {"student_worksheet": student_name, "answer_key": key_name},
                "found": {"student_worksheet": bool(student), "answer_key": bool(answer_key)},
            })
            continue
        pairs[grade_id] = {"student_worksheet": student[0], "answer_key": answer_key[0]}
        matched_ids.update({student[0]["id"], answer_key[0]["id"]})

    unmatched = [
        {"id": item["id"], "name": item.get("name")}
        for item in files
        if item["id"] not in matched_ids
    ]
    if unmatched:
        issues.append({"reason": "unmatched_files", "documents": unmatched})
    return pairs, issues


def provenance_settings(effective_config: Mapping[str, Any]) -> Mapping[str, Any]:
    return effective_config.get("publishing", {}).get("provenance") or {}


def provenance_properties(
    *,
    run_id: str,
    spec_revision: str,
    grade_id: str,
    week_of: str,
    worksheet_type: str,
    artifact_kind: str,
) -> dict[str, str]:
    """Provenance recorded on a rendered document; delivery reads these back.

    Values stay short identifiers because Drive caps each key+value pair at 124 bytes. The run id
    plus grade and revision locates the Spec without storing a full path.
    """
    return {
        "mts_run_id": run_id,
        "mts_spec_rev": spec_revision,
        "mts_grade_id": grade_id,
        "mts_week_of": week_of,
        "mts_wtype": worksheet_type,
        "mts_artifact_kind": artifact_kind,
    }


def unstamped_documents(
    pairs: Mapping[str, Mapping[str, Any]], *, week_of: str
) -> list[dict[str, Any]]:
    """Report documents with no provenance, or provenance naming a different grade or week."""
    findings: list[dict[str, Any]] = []
    for grade_id, pair in pairs.items():
        for role in ("student_worksheet", "answer_key"):
            document = pair[role]
            stamp = document.get("appProperties") or {}
            if not stamp.get("mts_run_id"):
                findings.append({"grade_id": grade_id, "role": role, "id": document["id"], "problem": "no_provenance"})
            elif stamp.get("mts_grade_id") not in (None, grade_id) or stamp.get("mts_week_of") not in (None, week_of):
                findings.append({
                    "grade_id": grade_id,
                    "role": role,
                    "id": document["id"],
                    "problem": "provenance_mismatch",
                    "stamped": {"grade_id": stamp.get("mts_grade_id"), "week_of": stamp.get("mts_week_of")},
                })
    return findings


def run_deliver(
    request: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    adapter: Any,
    *,
    dry_run: bool = True,
    run_root: Path | None = None,
    pairs: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deliver approved pairs into `Week_<WEEK_OF>` under each grade's destination folder."""
    check_subject_matches(request, effective_config)
    settings = delivery_settings(effective_config)
    week_of = resolve_week_of(request.get("week"), effective_config["calendar"])
    folder_name = week_folder_name(week_of, settings)
    destinations = resolve_destinations(settings, request.get("grades"))
    mode = request.get("mode") or settings["mode"]
    if mode not in {"copy", "move"}:
        raise DeliveryError("mode must be 'copy' or 'move'.")

    issues: list[dict[str, Any]] = []
    if pairs is not None:
        pairs = {normalize_grade_id(grade_id): pair for grade_id, pair in pairs.items()}
        source = request.get("source_label", "provided")
    elif run_root is not None:
        pairs, source = pair_from_run_root(run_root)
    else:
        source_folder = request.get("source_folder_id") or effective_config["publishing"]["staging"]["approved_folder_id"]
        naming = naming_settings(effective_config)
        pairs, staging_issues = pair_from_staging(
            adapter.list_child_files(source_folder),
            week_of=week_of,
            naming=naming,
            grade_ids=[destination["grade_id"] for destination in destinations],
        )
        issues.extend(staging_issues)
        source = f"staging:{source_folder}"

    provenance = provenance_settings(effective_config)
    blocked_grades: set[str] = set()
    if provenance.get("enabled") and run_root is None and pairs:
        findings = unstamped_documents(pairs, week_of=week_of)
        if findings:
            issues.append({"reason": "missing_provenance", "documents": findings})
            if provenance.get("require_stamp_for_delivery"):
                blocked_grades = {finding["grade_id"] for finding in findings}

    on_missing = request.get("on_missing") or "skip"
    if on_missing not in {"skip", "fail"}:
        raise DeliveryError("on_missing must be 'skip' or 'fail'.")
    target_records: list[dict[str, Any]] = []
    for destination in destinations:
        grade_id = destination["grade_id"]
        if grade_id in blocked_grades:
            target_records.append({
                **destination,
                "status": "failed",
                "error": f"{grade_id} has no verifiable provenance; delivery requires a stamped document.",
            })
            continue
        if grade_id not in pairs:
            # Deliver what is available; a missing grade blocks the run only when asked to.
            target_records.append({
                **destination,
                "status": "failed" if on_missing == "fail" else "skipped",
                "error": f"No deliverable pair found for {grade_id}.",
            })
            continue
        if dry_run:
            target_records.append({**destination, "status": "dry_run", "pair": _pair_summary(pairs[grade_id])})
            continue
        try:
            week_folder = adapter.ensure_child_folder(destination["folder_id"], folder_name)
            delivered = adapter.deliver_pair(
                {"artifact_kind": "student_worksheet", "status": "published", "document": pairs[grade_id]["student_worksheet"]},
                {"artifact_kind": "answer_key", "status": "published", "document": pairs[grade_id]["answer_key"]},
                week_folder["id"],
                mode=mode,
                deliver_answer_key=settings["deliver_answer_key"],
            )
            target_records.append({**destination, "status": "delivered", "week_folder": week_folder, **delivered})
        except Exception as error:
            target_records.append({**destination, "status": "failed", "error": str(error)})

    return {
        "utility": "deliver_worksheets",
        "dry_run": dry_run,
        "status": _overall_status(target_records),
        "week_of": week_of,
        "week_folder_name": folder_name,
        "mode": mode,
        "source": source,
        "request": dict(request),
        "issues": issues,
        "targets": target_records,
    }


def _pair_summary(pair: Mapping[str, Any]) -> dict[str, Any]:
    return {
        role: {"id": pair[role]["id"], "name": pair[role].get("name")}
        for role in ("student_worksheet", "answer_key")
    }


def _overall_status(target_records: Sequence[Mapping[str, Any]]) -> str:
    statuses = {record["status"] for record in target_records}
    if "failed" in statuses:
        return "failed"
    if statuses <= {"skipped"}:
        return "no_op"
    if "dry_run" in statuses:
        return "dry_run"
    return "delivered"


__all__ = [
    "DeliveryError",
    "check_subject_matches",
    "delivery_settings",
    "document_names",
    "naming_settings",
    "normalize_grade_id",
    "pair_from_run_root",
    "pair_from_staging",
    "provenance_properties",
    "provenance_settings",
    "resolve_destinations",
    "resolve_week_of",
    "run_deliver",
    "unstamped_documents",
    "week_folder_name",
]
