"""Format-and-deliver: bring staged worksheets up to pipeline standard, then deliver them.

A staged pair is either **conformant** (rendered through the pipeline, so it carries provenance) or an
**orphan** (authored straight into Drive, no Spec of record). Orphans are reconstructed into a Spec and
re-rendered from the registered template; conformant pairs are delivered as they are.

This module composes existing behavior. Delivery is `deliver.run_deliver`, reconstruction is
`reconstruct.reconstruct_spec`, and rendering is injected by the caller. It defines no delivery,
naming, or formatting rules of its own.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from mts.publishing import deliver as delivery_policy
from mts.publishing import reconstruct


class FormatDeliverError(ValueError):
    """Raised when a staged pair cannot be brought to pipeline standard."""


def classify_pairs(
    pairs: Mapping[str, Mapping[str, Any]], *, week_of: str
) -> dict[str, str]:
    """Label each grade `conformant` or `orphan` from its documents' provenance."""
    flagged = {
        finding["grade_id"]
        for finding in delivery_policy.unstamped_documents(pairs, week_of=week_of)
    }
    return {grade_id: ("orphan" if grade_id in flagged else "conformant") for grade_id in pairs}


def run_format_and_deliver(
    request: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    adapter: Any,
    *,
    read_document_lines: Callable[[str], Sequence[str]],
    persist_spec: Callable[[str, str, Mapping[str, Any]], str],
    render_pair: Callable[[Mapping[str, Any], str, str], Mapping[str, Any]],
    dry_run: bool = True,
) -> dict[str, Any]:
    """Reconstruct and re-render orphan pairs, then deliver every resolved pair."""
    delivery_policy.check_subject_matches(request, effective_config)
    settings = delivery_policy.delivery_settings(effective_config)
    week_of = delivery_policy.resolve_week_of(request.get("week"), effective_config["calendar"])
    destinations = delivery_policy.resolve_destinations(settings, request.get("grades"))
    naming = delivery_policy.naming_settings(effective_config)
    source_folder = (
        request.get("source_folder_id")
        or effective_config["publishing"]["staging"]["approved_folder_id"]
    )

    staged_pairs, issues = delivery_policy.pair_from_staging(
        adapter.list_child_files(source_folder),
        week_of=week_of,
        naming=naming,
        grade_ids=[destination["grade_id"] for destination in destinations],
    )
    classification = classify_pairs(staged_pairs, week_of=week_of)

    actions: list[dict[str, Any]] = []
    delivered_pairs: dict[str, Mapping[str, Any]] = {}
    for grade_id, pair in staged_pairs.items():
        if classification[grade_id] == "conformant":
            delivered_pairs[grade_id] = pair
            actions.append({"grade_id": grade_id, "action": "deliver_existing", "status": "planned" if dry_run else "ready"})
            continue
        if dry_run:
            actions.append({"grade_id": grade_id, "action": "reconstruct_and_rerender", "status": "planned"})
            continue
        try:
            rebuilt = _rebuild(
                grade_id,
                pair,
                week_of=week_of,
                effective_config=effective_config,
                read_document_lines=read_document_lines,
                persist_spec=persist_spec,
                render_pair=render_pair,
            )
        except Exception as error:  # one grade's bad document must not block the others
            actions.append({"grade_id": grade_id, "action": "reconstruct_and_rerender", "status": "failed", "error": str(error)})
            continue
        delivered_pairs[grade_id] = rebuilt["pair"]
        actions.append({
            "grade_id": grade_id,
            "action": "reconstruct_and_rerender",
            "status": "rebuilt",
            "spec_path": rebuilt["spec_path"],
            "replaced": {role: pair[role]["id"] for role in ("student_worksheet", "answer_key")},
        })

    delivery = delivery_policy.run_deliver(
        {**request, "source_label": f"format_and_deliver:{source_folder}"},
        effective_config,
        adapter,
        dry_run=dry_run,
        pairs=delivered_pairs,
    )
    _mark_pending_rebuild(delivery, actions)

    return {
        "utility": "format_and_deliver_worksheets",
        "dry_run": dry_run,
        "week_of": week_of,
        "status": "failed" if any(a["status"] == "failed" for a in actions) else delivery["status"],
        "classification": classification,
        "actions": actions,
        "issues": issues,
        "delivery": delivery,
    }


def _mark_pending_rebuild(delivery: dict[str, Any], actions: Sequence[Mapping[str, Any]]) -> None:
    """A grade awaiting rebuild has no pair *yet*; reporting it as missing would misstate the plan."""
    pending = {
        action["grade_id"] for action in actions
        if action["action"] == "reconstruct_and_rerender" and action["status"] == "planned"
    }
    for target in delivery["targets"]:
        if target.get("grade_id") in pending:
            target["status"] = "pending_rebuild"
            target["error"] = None


def _rebuild(
    grade_id: str,
    pair: Mapping[str, Any],
    *,
    week_of: str,
    effective_config: Mapping[str, Any],
    read_document_lines: Callable[[str], Sequence[str]],
    persist_spec: Callable[[str, str, Mapping[str, Any]], str],
    render_pair: Callable[[Mapping[str, Any], str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    section_titles = {
        section["id"]: section.get("title", section["id"].title())
        for section in effective_config["sections"]
    }
    spec = reconstruct.reconstruct_spec(
        read_document_lines(pair["student_worksheet"]["id"]),
        read_document_lines(pair["answer_key"]["id"]),
        grade_id=grade_id,
        week_of=week_of,
        title=str(effective_config.get("worksheet_title", "MTS - Weekly Math Worksheet")),
        section_titles=section_titles,
        source_documents={
            "student_worksheet": pair["student_worksheet"]["id"],
            "answer_key": pair["answer_key"]["id"],
        },
    )
    spec_path = persist_spec(grade_id, week_of, spec)
    rendered = render_pair(spec, grade_id, week_of)
    return {"pair": rendered, "spec_path": spec_path}


__all__ = ["FormatDeliverError", "classify_pairs", "run_format_and_deliver"]
