# Consolidated Design

## Architecture

The repository uses a shared core with subject modules.

Shared components own run control, schemas, template management, rendering, publishing, telemetry,
resume behavior, and common QA. Subject modules own curriculum interpretation, content generation,
subject verification, grade progression, and subject-specific layout needs.

## Execution path

`intent -> subject/grade resolution -> curriculum scope -> Worksheet Spec -> subject verification -> render -> content and visual QA -> approval -> publish`

## Source of truth

- Governing principles: `constitution.md`
- Agent execution contract: `AGENTS.md`
- Shared behavior: `docs/requirements.md` and `docs/design.md`
- Defaults: `config/*.yaml`
- Subject behavior: `subjects/<subject>/`
- Machine contracts: `schemas/`
- Per-run truth: `runs/<subject>/`

Harness adapters may point to these sources but may not redefine them.

