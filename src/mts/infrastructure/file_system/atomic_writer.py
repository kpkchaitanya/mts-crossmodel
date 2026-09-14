"""Write JSON records to disk through a temporary file and replace."""
from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import tempfile
from typing import Any


def plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [plain(item) for item in value]
    if isinstance(value, list):
        return [plain(item) for item in value]
    return value


def write_json(path: str | Path, payload: Mapping[str, Any], *, overwrite: bool = True) -> None:
    target = Path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite immutable record: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(plain(payload), indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=target.parent, suffix=".tmp") as handle:
        temporary = Path(handle.name)
        handle.write(encoded)
    temporary.replace(target)
