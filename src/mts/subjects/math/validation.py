"""Math output-validation behavior for the target package layout."""
from __future__ import annotations

from .p0_runtime import targeted_text_qa
from .subject_module import MathSubjectError, MathSubjectModule

MathValidator = MathSubjectModule

__all__ = ["MathValidator", "MathSubjectError", "MathSubjectModule", "targeted_text_qa"]
