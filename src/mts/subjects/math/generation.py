"""Math worksheet-generation behavior for the target package layout."""
from __future__ import annotations

from .subject_module import MathSubjectError, MathSubjectModule

MathGeneration = MathSubjectModule

__all__ = ["MathGeneration", "MathSubjectError", "MathSubjectModule"]
