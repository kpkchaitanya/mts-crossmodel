"""Math verification behavior for the target package layout."""
from __future__ import annotations

from .p0_runtime import verify_question, verify_spec
from .subject_module import MathSubjectError, MathSubjectModule

MathVerifier = MathSubjectModule

__all__ = ["MathVerifier", "MathSubjectError", "MathSubjectModule", "verify_question", "verify_spec"]
