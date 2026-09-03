"""Persist immutable Worksheet Spec revisions and their Run Manifest references."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any


class SpecRepositoryError(ValueError):
    """Raised when a Worksheet Spec cannot be persisted safely."""


def _fingerprint(spec: Mapping[str, Any]) -> str:
    encoded = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class SpecRepository:
    """Write immutable JSON Specs and link them to an existing run manifest."""

    def __init__(self, runs_root: str | Path) -> None:
        self.runs_root = Path(runs_root)

    def write_revision(
        self,
        manifest: Mapping[str, Any],
        spec: Mapping[str, Any],
        *,
        worksheet_id: str,
        revision: str,
    ) -> dict[str, Any]:
        self._validate(spec, worksheet_id)
        run_id = manifest.get("run_id")
        subject = manifest.get("subject")
        if not isinstance(run_id, str) or not run_id or not isinstance(subject, str) or not subject:
            raise SpecRepositoryError("Spec persistence requires a valid Run Manifest identity.")
        if not revision:
            raise SpecRepositoryError("Spec revision is required.")

        fingerprint = _fingerprint(spec)
        relative_path = Path(subject) / run_id / "specs" / worksheet_id / f"{revision}.json"
        path = self.runs_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(deepcopy(dict(spec)), indent=2, sort_keys=True) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != payload:
            raise SpecRepositoryError("Worksheet Spec revisions are immutable.")
        path.write_text(payload, encoding="utf-8")
        return {
            "worksheet_id": worksheet_id,
            "revision": revision,
            "spec_path": relative_path.as_posix(),
            "fingerprint": fingerprint,
        }

    @staticmethod
    def _validate(spec: Mapping[str, Any], worksheet_id: str) -> None:
        worksheet = spec.get("worksheet")
        sections = spec.get("sections")
        verification = spec.get("verification")
        if not worksheet_id or not isinstance(worksheet, Mapping) or not isinstance(sections, list):
            raise SpecRepositoryError("Worksheet Spec must contain worksheet metadata and sections.")
        required = {"grade", "week_start", "question_count", "duration_minutes"}
        if not required.issubset(worksheet):
            raise SpecRepositoryError("Worksheet Spec is missing required worksheet metadata.")
        if not isinstance(verification, Mapping) or verification.get("status") not in {"PENDING", "PASS", "FAIL"}:
            raise SpecRepositoryError("Worksheet Spec must contain a valid verification status.")
        questions = []
        for section in sections:
            if not isinstance(section, Mapping) or not isinstance(section.get("questions"), list):
                raise SpecRepositoryError("Every Worksheet Spec section must contain questions.")
            questions.extend(section["questions"])
        if len(questions) != worksheet["question_count"]:
            raise SpecRepositoryError("Worksheet Spec question_count does not match its questions.")
        numbers = [question.get("number") for question in questions if isinstance(question, Mapping)]
        if len(numbers) != len(questions) or sorted(numbers) != list(range(1, len(questions) + 1)):
            raise SpecRepositoryError("Worksheet Spec question numbering must be contiguous.")