---
description: "Unified, subject- and worksheet-type-agnostic worksheet generation entry point."
agent: "agent"
argument-hint: "subject=math|ela worksheettype=weekly|class|homework-4-day|compact-unbranded gates=all|bypass all|bypass <gate_id>[,<gate_id>...] [grades=all|<list>] [week=current|<date>] [publish=yes|no] [deliver=yes|no] [difficulty=Low|Low+|Medium|Medium+|High|Very High] [diversity=Low|Low+|Medium|Medium+|High|Very High] [topic_overrides=grade:amount:topic[;...]] [run=<run-id>]"
---

# Command: Generate Worksheet

## Canonical definition — load this first

- [commands/generate-worksheet.md](../../commands/generate-worksheet.md)

This prompt is a thin entry point only. Follow `commands/generate-worksheet.md` for parameter
resolution, gate handling, and delegation to the resolved subject command. Also read, in order:

- [AGENTS.md](../../AGENTS.md)
- [constitution.md](../../constitution.md)
- [specs/generate_math_worksheets/01. intent/requirements.md](<../../specs/generate_math_worksheets/01. intent/requirements.md>) (canonical requirements) and [specs/generate_math_worksheets/03. design/design.md](<../../specs/generate_math_worksheets/03. design/design.md>) (canonical design)
- [data/config/project/base.yaml](../../data/config/project/base.yaml)
- The selected subject's `data/config/subjects/<subject>.yaml`, `docs/subjects/<subject>/`, and `src/mts/subjects/<subject>/`

## Parameters

Parse `subject`, `worksheettype`, `gates`, `grades`, `week`, `publish`, `deliver`, `difficulty`, `diversity`,
`topic_overrides`, and `run` from the user's invocation exactly as documented in
`commands/generate-worksheet.md`. Default to `subject=math`, `worksheettype=weekly`, `gates=all`,
`grades=all`, `week=current` (today's date), `publish=yes`, `deliver=yes`, `difficulty=diversity=medium_plus`, and no
`topic_overrides` when a parameter is omitted — the run publishes automatically once Gate 5 is recorded
unless the user passes `publish=no`.

If the user's invocation includes a likely typo, shorthand, or non-canonical parameter name, do not
pass it directly to code. Translate it in the model layer, replay the interpretation, and ask the user
to confirm before proceeding. Example: interpret `grade=1,5,9-10` as `grades=1,5,9-10`, then confirm
that interpretation with the user before invoking `scripts/generate_worksheet.py`.

Resolve and record the `gates` decision in the Run Manifest before generation starts. Bypassing a
gate only removes its stop-and-approve checkpoint; Worksheet Spec persistence, verification, and
visual QA stay mandatory regardless of `gates`.

Delegate execution to the resolved subject behavior under `src/mts/subjects/<subject>/`. For
`subject=math worksheettype=weekly`, run the exact steps in
[skills/math/weekly-worksheet-execution-runbook.md](../../skills/math/weekly-worksheet-execution-runbook.md)
directly or invoke the migrated CLI:

```powershell
python scripts/generate_worksheet.py subject=math worksheettype=weekly grades=<list> week=<value> gates="bypass all" publish=<yes|no> deliver=<yes|no>
```

Do not re-derive the process from design/requirements docs.
