"""Load Worksheet Spec revisions from the target data/transactions layout."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mts.infrastructure.file_system.json_loader import load_json


class SpecLoadError(ValueError):
	"""Raised when a Worksheet Spec revision cannot be loaded."""


class SpecLoader:
	"""Load immutable Worksheet Spec revisions from the entity hierarchy."""

	def __init__(self, data_root: str | Path) -> None:
		self.data_root = Path(data_root)

	def spec_path(self, *, subject: str, grade: str, cycle_id: str, batch_id: str, worksheet_type: str, revision: int) -> Path:
		if not all([subject, grade, cycle_id, batch_id, worksheet_type, revision]):
			raise SpecLoadError("subject, grade, cycle_id, batch_id, worksheet_type, and revision are required.")
		return (
			self.data_root
			/ "transactions"
			/ "subjects"
			/ subject
			/ "grades"
			/ grade
			/ "cycles"
			/ cycle_id
			/ "batches"
			/ batch_id
			/ "worksheets"
			/ worksheet_type
			/ "specs"
			/ f"r{revision}.json"
		)

	def load_revision(self, **identity: Any) -> dict[str, Any]:
		return load_json(self.spec_path(**identity))


__all__ = ["SpecLoader", "SpecLoadError"]
