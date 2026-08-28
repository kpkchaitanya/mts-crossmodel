# Consolidated Design

> **Archived.** Superseded by [`specs/generate_math_worksheets/03. design/design.md`](../../specs/generate_math_worksheets/03.%20design/design.md), the canonical design document. Kept here for history only.

## Architecture

The repository uses a shared core with subject modules.

Shared components own run control, schemas, template management, rendering, publishing, telemetry,
resume behavior, and common QA. Subject modules own curriculum interpretation, content generation,
subject verification, grade progression, and subject-specific layout needs.

## Execution path

`intent -> subject/grade resolution -> curriculum scope -> Worksheet Spec -> persist immutable Spec revision -> Gate 2 -> subject verification -> render -> content and visual QA -> approval -> publish`

## Source of truth

- Governing principles: `constitution.md`
- Agent execution contract: `AGENTS.md`
- Shared behavior: `docs/requirements.md` and `docs/design.md`
- Defaults: `config/*.yaml`
- Subject behavior: `subjects/<subject>/`
- Machine contracts: `schemas/`
- Per-run truth: `runs/<subject>/`
 
Generation must materialize each approved Worksheet as an immutable, schema-validated Spec revision
under its Run directory before Gate 2 can transition to verification. The Run Manifest stores the
Spec references and fingerprints; chat output is review evidence, not the source artifact. Gate 2
must fail closed when the complete planned Worksheet set has no durable Spec references.

Harness adapters may point to these sources but may not redefine them.

