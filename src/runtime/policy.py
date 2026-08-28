"""Resolve immutable policy snapshots from MTS configuration files."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml


class PolicyError(ValueError):
    """Raised when a request cannot be resolved to an executable policy."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PolicyError(f"Configuration file not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise PolicyError(f"Configuration must be a mapping: {path}")
    return payload


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def resolve(
    request: Mapping[str, Any],
    *,
    repository_root: str | Path,
) -> Mapping[str, Any]:
    """Resolve an executable, immutable policy snapshot for one request.

    The effective policy merges base, subject, and Worksheet Type configuration;
    explicit request overrides are applied last and are retained in the snapshot.
    """
    root = Path(repository_root)
    subject = request.get("subject")
    worksheet_type = request.get("worksheet_type")
    overrides = request.get("overrides", {})

    if not isinstance(subject, str) or not subject:
        raise PolicyError("Request must provide a non-empty subject.")
    if not isinstance(worksheet_type, str) or not worksheet_type:
        raise PolicyError("Request must provide a non-empty worksheet_type.")
    if not isinstance(overrides, Mapping):
        raise PolicyError("Request overrides must be a mapping.")

    base = _load_yaml(root / "config" / "base.yaml")
    subject_policy = _load_yaml(root / "config" / f"{subject}.yaml")
    if subject_policy.get("subject") != subject:
        raise PolicyError(f"Subject configuration does not match request subject: {subject}")

    type_policy = _load_yaml(root / "config" / "worksheet-types" / f"{worksheet_type}.yaml")
    if type_policy.get("worksheet_type_id") != worksheet_type:
        raise PolicyError(f"Worksheet Type configuration does not match request: {worksheet_type}")
    if type_policy.get("status") != "active":
        raise PolicyError(f"Worksheet Type is not active: {worksheet_type}")
    if subject not in type_policy.get("compatible_subjects", []):
        raise PolicyError(f"Worksheet Type {worksheet_type} is not compatible with subject {subject}")

    effective = _merge(base, subject_policy)
    effective = _merge(effective, type_policy)
    effective = _merge(effective, dict(overrides))
    effective["request"] = {"subject": subject, "worksheet_type": worksheet_type}
    effective["run_overrides"] = deepcopy(dict(overrides))
    return _freeze(effective)
