"""Math curriculum behavior for the target package layout."""
from __future__ import annotations

from .subject_module import MathSubjectError, MathSubjectModule

MathCurriculumResolver = MathSubjectModule

__all__ = ["MathCurriculumResolver", "MathSubjectError", "MathSubjectModule"]
