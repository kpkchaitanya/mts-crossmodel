"""Persist resumable MTS Run Manifests without duplicating Worksheet Spec content."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class RunRepositoryError(ValueError):
    """Raised when a Run cannot be created or safely resumed."""


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _fingerprint(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(_plain(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_plain(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


class RunRepository:
    """Create or resume a Run after verifying its request and policy identity."""

    def __init__(self, runs_root: str | Path) -> None:
        self.runs_root = Path(runs_root)

    def create_or_resume(
        self,
        request: Mapping[str, Any],
        resolved_policy: Mapping[str, Any],
        *,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        subject = request.get("subject")
        worksheet_type = request.get("worksheet_type")
        if not isinstance(subject, str) or not subject:
            raise RunRepositoryError("Run request must provide a non-empty subject.")
        if not isinstance(worksheet_type, str) or not worksheet_type:
            raise RunRepositoryError("Run request must provide a non-empty worksheet_type.")

        request_snapshot = _plain(request)
        policy_snapshot = _plain(resolved_policy)
        request_fingerprint = _fingerprint(request_snapshot)
        policy_fingerprint = _fingerprint(policy_snapshot)
        run_id = run_id or f"run-{uuid4().hex}"
        run_dir = self.runs_root / subject / run_id
        manifest_path = run_dir / "run-manifest.json"

        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("request_fingerprint") != request_fingerprint:
                raise RunRepositoryError("Run request does not match the existing Run Manifest.")
            if manifest.get("policy_fingerprint") != policy_fingerprint:
                raise RunRepositoryError("Resolved policy does not match the existing Run Manifest.")
            return manifest

        now = datetime.now(timezone.utc).isoformat()
        manifest = {
            "manifest_version": "1.0",
            "run_id": run_id,
            "subject": subject,
            "worksheet_type": worksheet_type,
            "status": "initialized",
            "started_at": now,
            "request": request_snapshot,
            "request_fingerprint": request_fingerprint,
            "policy_fingerprint": policy_fingerprint,
            "policy_snapshot_path": "resolved-policy.json",
            "checkpoints": [],
            "spec_references": [],
            "approvals": [],
            "artifacts": [],
            "telemetry": {"token_usage": None},
        }
        _write_json(run_dir / "resolved-policy.json", policy_snapshot)
        _write_json(manifest_path, manifest)
        return manifest

    def add_checkpoint(self, run_id: str, subject: str, checkpoint: str) -> dict[str, Any]:
        """Append a named checkpoint to an existing Run Manifest."""
        manifest_path = self.runs_root / subject / run_id / "run-manifest.json"
        if not manifest_path.exists():
            raise RunRepositoryError(f"Run Manifest not found: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.setdefault("checkpoints", []).append(
            {"name": checkpoint, "recorded_at": datetime.now(timezone.utc).isoformat()}
        )
        _write_json(manifest_path, manifest)
        return manifest

    def save_manifest(self, manifest: Mapping[str, Any]) -> None:
        """Persist an updated manifest after a lifecycle controller changes it."""
        run_id = manifest.get("run_id")
        subject = manifest.get("subject")
        if not isinstance(run_id, str) or not run_id or not isinstance(subject, str) or not subject:
            raise RunRepositoryError("Run Manifest must provide non-empty run_id and subject.")
        manifest_path = self.runs_root / subject / run_id / "run-manifest.json"
        if not manifest_path.exists():
            raise RunRepositoryError(f"Run Manifest not found: {manifest_path}")
        _write_json(manifest_path, manifest)
