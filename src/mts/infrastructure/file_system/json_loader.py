"""Load JSON records from disk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonLoadError(ValueError):
    """Raised when a JSON record cannot be loaded."""


def load_json(path: str | Path) -> dict[str, Any]:
    record_path = Path(path)
    if not record_path.is_file():
        raise JsonLoadError(f"JSON file not found: {record_path}")
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise JsonLoadError(f"JSON record must be an object: {record_path}")
    return payload
