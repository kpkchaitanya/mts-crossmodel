"""Write immutable Worksheet Spec revisions to the target data/transactions layout."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mts.infrastructure.file_system.atomic_writer import write_json
from mts.worksheets.spec_loader import SpecLoader


class SpecWriteError(ValueError):
	"""Raised when a Worksheet Spec revision cannot be written safely."""


class SpecWriter:
	"""Write immutable Worksheet Spec revisions to the entity hierarchy."""

	def __init__(self, data_root: str | Path) -> None:
		self.loader = SpecLoader(data_root)

	def write_revision(self, spec: Mapping[str, Any], **identity: Any) -> Path:
		path = self.loader.spec_path(**identity)
		try:
			write_json(path, spec, overwrite=False)
		except FileExistsError as error:
			raise SpecWriteError(str(error)) from error
		return path


__all__ = ["SpecWriter", "SpecWriteError"]
