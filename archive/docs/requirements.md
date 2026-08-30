# Consolidated Requirements

## Purpose

Provide a repeatable, cross-harness system for weekly MTS Math and ELA worksheet generation.

## Shared requirements

- Support Grade 1, Grades 4–6, and combined Grades 9–10, subject to configuration.
- Create separate editable student worksheets and verified answer keys.
- Build both artifacts from one canonical Worksheet Spec.
- Apply configured human gates without silently bypassing them.
- Independently verify every item and reverify affected edits.
- Preserve print readability, controlled whitespace, answer space, pagination, and exact key matching.
- Protect master templates and check template revisions.
- Record source provenance, pacing confidence, run state, approvals, QA, and available telemetry.
- Publish only approved artifacts to `outputs/<subject>/`.

Subject requirements extend these requirements without duplicating them.

