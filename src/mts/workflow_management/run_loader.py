"""Load Run state from the target data/transactions layout."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mts.infrastructure.file_system.json_loader import load_json


class RunLoadError(ValueError):
	"""Raised when a Run Manifest cannot be loaded."""


class RunLoader:
	"""Load target Run records by run ID."""

	def __init__(self, data_root: str | Path) -> None:
		self.data_root = Path(data_root)

	def run_root(self, run_id: str) -> Path:
		if not run_id:
			raise RunLoadError("run_id is required.")
		return self.data_root / "transactions" / "runs" / run_id

	def load_manifest(self, run_id: str) -> dict[str, Any]:
		return load_json(self.run_root(run_id) / "run_manifest.json")

	def load_effective_config(self, run_id: str) -> dict[str, Any]:
		return load_json(self.run_root(run_id) / "effective_config.json")

	def load_entity_references(self, run_id: str) -> dict[str, Any]:
		return load_json(self.run_root(run_id) / "entity_references.json")


__all__ = ["RunLoader", "RunLoadError"]
