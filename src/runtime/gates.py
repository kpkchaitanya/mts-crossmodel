"""Enforce revision-scoped MTS human approval gates and invalidation rules."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class GateError(ValueError):
    """Raised when a protected lifecycle transition is not approved."""


GATES = {
    "scope_review": "worksheet_prepared",
    "question_review": "verification_in_progress",
    "verification_review": "render_ready",
    "formatting_review": "publish_approval_pending",
    "publish_approval": "published",
}

_INVALIDATION_RULES = {
    "policy": ("scope_invalidated", set(GATES)),
    "scope": ("scope_invalidated", set(GATES)),
    "question": (
        "question_invalidated",
        {"question_review", "verification_review", "formatting_review", "publish_approval"},
    ),
    "template": ("template_invalidated", {"formatting_review", "publish_approval"}),
    "destination": ("publish_approval_pending", {"publish_approval"}),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_gate(gate: str) -> None:
    if gate not in GATES:
        raise GateError(f"Unknown gate: {gate}")


def record_approval(
    manifest: dict[str, Any],
    *,
    gate: str,
    artifact_revision: str,
    status: str,
    reviewer: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Append an immutable approval decision for a single artifact revision."""
    _validate_gate(gate)
    if status not in {"approved", "rejected"}:
        raise GateError(f"Invalid approval status: {status}")
    if not artifact_revision:
        raise GateError("Approval must identify an artifact revision.")

    updated = deepcopy(manifest)
    updated.setdefault("approvals", []).append(
        {
            "approval_id": f"approval-{uuid4().hex}",
            "gate": gate,
            "artifact_revision": artifact_revision,
            "status": status,
            "reviewer": reviewer,
            "notes": notes,
            "recorded_at": _now(),
        }
    )
    return updated


def require_approval(manifest: dict[str, Any], *, gate: str, artifact_revision: str) -> str:
    """Return the authorized next state or fail closed for absent/stale decisions."""
    _validate_gate(gate)
    matching = [
        approval
        for approval in manifest.get("approvals", [])
        if approval.get("gate") == gate and approval.get("artifact_revision") == artifact_revision
    ]
    if not matching:
        raise GateError(f"Missing {gate} approval for revision {artifact_revision}.")

    latest = matching[-1]
    if latest.get("invalidated_at"):
        raise GateError(f"Stale {gate} approval for revision {artifact_revision}.")
    if latest.get("status") != "approved":
        raise GateError(f"Rejected {gate} approval for revision {artifact_revision}.")
    return GATES[gate]


def require_question_review(manifest: dict[str, Any], *, artifact_revision: str) -> str:
    """Require Gate 2 approval plus durable Specs for every planned Worksheet."""
    if not manifest.get("spec_references"):
        raise GateError("Gate 2 requires persisted Worksheet Spec references.")
    return require_approval(manifest, gate="question_review", artifact_revision=artifact_revision)


def invalidate(manifest: dict[str, Any], *, change: str, reason: str) -> dict[str, Any]:
    """Record an input change and invalidate only dependent gate decisions."""
    if change not in _INVALIDATION_RULES:
        raise GateError(f"Unknown invalidation change: {change}")
    if not reason:
        raise GateError("Invalidation reason is required.")

    next_status, invalidated_gates = _INVALIDATION_RULES[change]
    updated = deepcopy(manifest)
    invalidated_ids = []
    for approval in updated.get("approvals", []):
        if approval.get("gate") in invalidated_gates and not approval.get("invalidated_at"):
            approval["invalidated_at"] = _now()
            approval["invalidation_reason"] = reason
            invalidated_ids.append(approval.get("approval_id"))

    updated["status"] = next_status
    updated.setdefault("invalidations", []).append(
        {
            "change": change,
            "reason": reason,
            "recorded_at": _now(),
            "invalidated_approval_ids": invalidated_ids,
        }
    )
    return updated
