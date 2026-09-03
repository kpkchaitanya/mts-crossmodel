"""Write Run state to the target data/transactions layout."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mts.infrastructure.file_system.atomic_writer import write_json


class RunWriteError(ValueError):
	"""Raised when target Run evidence is incomplete."""


class RunWriter:
	"""Write target Run records by run ID."""

	def __init__(self, data_root: str | Path) -> None:
		self.data_root = Path(data_root)

	def run_root(self, run_id: str) -> Path:
		if not run_id:
			raise RunWriteError("run_id is required.")
		return self.data_root / "transactions" / "runs" / run_id

	def write_manifest(self, manifest: Mapping[str, Any]) -> None:
		run_id = manifest.get("run_id")
		if not isinstance(run_id, str) or not run_id:
			raise RunWriteError("Run Manifest must provide run_id.")
		write_json(self.run_root(run_id) / "run_manifest.json", manifest)

	def write_effective_config(self, run_id: str, effective_config: Mapping[str, Any]) -> None:
		write_json(self.run_root(run_id) / "effective_config.json", effective_config)

	def write_entity_references(self, run_id: str, entity_references: Mapping[str, Any]) -> None:
		write_json(self.run_root(run_id) / "entity_references.json", entity_references)


__all__ = ["RunWriter", "RunWriteError"]
