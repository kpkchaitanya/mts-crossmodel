"""Resolve immutable policy snapshots from MTS configuration files."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
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


def _resolve_template_registration(root: Path, subject: str, worksheet_type: str) -> dict[str, Any]:
    registry_path = root / "templates" / "by-worksheet-type" / "template-manifest.json"
    if not registry_path.is_file():
        raise PolicyError(f"Template registry not found: {registry_path}")
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PolicyError(f"Template registry is invalid: {registry_path}") from error
    matches = [
        entry for entry in registry.get("entries", [])
        if entry.get("subject") == subject and entry.get("worksheet_type_id") == worksheet_type
    ]
    if len(matches) != 1:
        raise PolicyError(f"No unique template registration for {subject}/{worksheet_type}")
    entry = matches[0]
    if entry.get("status") != "active":
        raise PolicyError(f"Template registration is not active: {subject}/{worksheet_type}")
    manifest_path = entry.get("manifest_path")
    if not isinstance(manifest_path, str) or not manifest_path:
        raise PolicyError(f"Active template registration has no manifest: {subject}/{worksheet_type}")
    resolved_path = (registry_path.parent / manifest_path).resolve()
    if not resolved_path.is_file():
        raise PolicyError(f"Template manifest not found: {resolved_path}")
    return {"registry_path": registry_path.relative_to(root).as_posix(), "entry": entry, "manifest_path": resolved_path.relative_to(root).as_posix()}


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
    template_registration = _resolve_template_registration(root, subject, worksheet_type)
    effective.setdefault("template_selection", {})["template_registry"] = template_registration["registry_path"]
    effective["template_selection"]["template_manifest"] = template_registration["manifest_path"]
    effective["template_selection"]["template_registry_entry"] = deepcopy(template_registration["entry"])
    effective["request"] = {"subject": subject, "worksheet_type": worksheet_type}
    effective["run_overrides"] = deepcopy(dict(overrides))
    return _freeze(effective)
