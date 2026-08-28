---
description: "Unified, subject- and worksheet-type-agnostic worksheet generation entry point."
agent: "agent"
argument-hint: "subject=math|ela worksheettype=weekly|class|homework-4-day|compact-unbranded gates=all|bypass all|bypass <gate_id>[,<gate_id>...] [grades=all|<list>] [week=current|<date>] [publish=yes|no] [difficulty=Low|Low+|Medium|Medium+|High|Very High] [diversity=Low|Low+|Medium|Medium+|High|Very High] [topic_overrides=grade:amount:topic[;...]] [run=<run-id>]"
---

# Command: Generate Worksheet

## Canonical definition — load this first

- [commands/generate-worksheet.md](../../commands/generate-worksheet.md)

This prompt is a thin entry point only. Follow `commands/generate-worksheet.md` for parameter
resolution, gate handling, and delegation to the resolved subject command. Also read, in order:

- [AGENTS.md](../../AGENTS.md)
- [constitution.md](../../constitution.md)
- [docs/requirements.md](../../docs/requirements.md) and [specs/generate_math_worksheets/03. design/design.md](<../../specs/generate_math_worksheets/03. design/design.md>) (canonical design)
- [config/base.yaml](../../config/base.yaml)
- The selected subject's `config/<subject>.yaml` and `requirements.md`

## Parameters

Parse `subject`, `worksheettype`, `gates`, `grades`, `week`, `publish`, `difficulty`, `diversity`,
`topic_overrides`, and `run` from the user's invocation exactly as documented in
`commands/generate-worksheet.md`. Default to `subject=math`, `worksheettype=weekly`, `gates=all`,
`grades=all`, `week=current` (today's date), `publish=yes`, `difficulty=diversity=medium_plus`, and no
`topic_overrides` when a parameter is omitted — the run publishes automatically once Gate 5 is recorded
unless the user passes `publish=no`.

Resolve and record the `gates` decision in the Run Manifest before generation starts. Bypassing a
gate only removes its stop-and-approve checkpoint; Worksheet Spec persistence, verification, and
visual QA stay mandatory regardless of `gates`.

Delegate execution to the resolved subject's command (for `subject=math`, this is
[subjects/math/commands/generate-weekly-classworksheets.md](../../subjects/math/commands/generate-weekly-classworksheets.md)).
For `subject=math worksheettype=weekly`, run the exact steps in
[subjects/math/skills/weekly-worksheet-execution-runbook.md](../../subjects/math/skills/weekly-worksheet-execution-runbook.md)
directly instead of re-deriving the process from design/requirements docs.
