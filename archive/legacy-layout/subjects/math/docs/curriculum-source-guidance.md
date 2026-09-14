# Curriculum Source Guidance v1.1

## Purpose
Resolve weekly/monthly MTS math scope with explicit provenance while minimizing repeated research.

## Fast-path policy
For normal runs, consult local cache first:
- `knowledge/curriculum/ccs-2026-2027/pacing.json`
- `knowledge/curriculum/nc-math/standards-cache.json`
- `knowledge/sources.json`

A cache HIT is a performance optimization, not proof that inferred pacing is official.

## Authority priority
1. CCS current curriculum/pacing sources when accessible.
2. CCS curriculum guidance and current academic calendar.
3. NC DPI standards, unpacking, and progression documents.
4. NC assessment/check-in specifications where useful.
5. Logical pacing inference using date, school calendar, instructional week, prerequisites, and grade/course standards.

## Refresh/fallback triggers
Use external research when:
- the requested week/month is absent from cache;
- source metadata indicates refresh/change detection is due;
- cached evidence is contradictory or insufficient;
- confidence is too low for the proposed scope;
- the user explicitly asks for current/fresh verification.

## Confidence labels
- `confirmed` — directly supported by current CCS curriculum/pacing evidence.
- `strongly_inferred` — multiple current sources, calendar position, and progression strongly support the scope.
- `inferred` — primarily standards/progression-based because direct pacing is unavailable.

Never state inferred pacing as confirmed district pacing.

## Gate 1 output
For each grade/course provide instructional week/date context, topic/unit, standards, spiral topics, question count, difficulty, confidence, and source/basis. For combined Grades 9/10, resolve Grade 9 and Grade 10 independently.

## Calendar considerations
Account for school start, holidays, teacher workdays, breaks, and shortened weeks before inferring instructional progress.

Curriculum resolution remains advisory until approved at the configured curriculum gate.
