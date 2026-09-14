# Skill: Worksheet Verification

## Use when
Questions are approved or edited and require independent verification before rendering.

## Procedure
1. Read the canonical Worksheet Spec.
2. For supported numeric/geometry/algebra items, recompute using `src/p0_runtime.py` or an equivalent independent calculation path.
3. For every item, independently review wording, sufficient information, grade appropriateness, ambiguity, multiple unintended answers, pattern uniqueness, units, and question-answer consistency as applicable.
4. Never treat the generated answer itself as verification evidence.
5. Mark unsupported deterministic items as reasoning review rather than silently passing them.
6. Reverify all affected items after any edit.
7. Block rendering on unresolved failures/ambiguities.
8. Return compact checked/passed/failed/ambiguous/reasoning-required counts and corrections.
