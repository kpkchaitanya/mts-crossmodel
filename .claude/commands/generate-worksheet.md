---
description: Unified, subject- and worksheet-type-agnostic worksheet generation entry point.
argument-hint: subject=math|ela worksheettype=weekly|class|homework-4-day|compact-unbranded gates=all|bypass all|bypass <gate_id>[,<gate_id>...] [grades=all|<list>] [week=current|<date>] [publish=yes|no] [deliver=yes|no] [difficulty=Low|Low+|Medium|Medium+|High|Very High] [diversity=Low|Low+|Medium|Medium+|High|Very High] [topic_overrides=grade:amount:topic[;...]] [run=<run-id>]
allowed-tools: Bash, Read
---

Follow `commands/generate-worksheet.md` exactly — it is the canonical, harness-neutral definition of
this command; do not re-derive its behavior. This file only registers it as a Claude Code slash
command.

Arguments for this invocation: $ARGUMENTS

Steps:

1. Read, in order: `AGENTS.md`, `constitution.md`, `commands/generate-worksheet.md`,
   `specs/generate_math_worksheets/01. intent/requirements.md` (canonical requirements),
   `specs/generate_math_worksheets/03. design/design.md` (canonical design), and
   `data/config/project/base.yaml`.
2. Resolve `subject`, `worksheettype`, `gates`, `grades`, `week`, `publish`, `deliver`, `difficulty`,
   `diversity`, `form_diversity`, `variation_seed`, `topic_overrides`, and `run` from `$ARGUMENTS` and
   configuration defaults only — never carry a value forward from an earlier turn's design-discussion
   example. Translate any near-alias parameter name (e.g. `grade=1,5,9-10` → `grades=1,5,9-10`), echo
   the full resolved parameter set back to the user, and get explicit confirmation before authoring.
3. Resolve and record the `gates` decision in the Run Manifest before generation starts. Bypassing a
   gate only removes its stop-and-approve checkpoint; Worksheet Spec persistence, verification, and
   visual QA stay mandatory regardless of `gates`.
4. Load the resolved subject's `data/config/subjects/<subject>.yaml`, `docs/subjects/<subject>/`, and
   `src/mts/subjects/<subject>/`, and delegate execution to that subject module. For
   `subject=math worksheettype=weekly`, follow
   `skills/math/weekly-worksheet-execution-runbook.md` directly, or invoke:
   ```powershell
   python scripts/generate_worksheet.py subject=math worksheettype=weekly grades=<list> week=<value> gates="bypass all" publish=<yes|no> deliver=<yes|no>
   ```
5. Do not re-derive the process from design/requirements docs, and do not skip a configured human gate.
