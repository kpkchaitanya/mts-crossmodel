---
description: "Copy approved worksheet/answer-key pairs from staging into per-grade Week_<WEEK_OF> folders."
agent: "agent"
argument-hint: "[week=current|<n>|<iso-date>] [grades=all|<list>] [subject=<subject-id>] [run=<run-id>] [source_folder=<folder-id>] [mode=copy|move] [on_missing=skip|fail] [dry_run=yes|no]"
---

# Command: Deliver Worksheets

## Canonical definition — load this first

- [commands/deliver-worksheets.md](../../commands/deliver-worksheets.md)

This prompt is a thin entry point only. Follow `commands/deliver-worksheets.md` for parameter
resolution, pairing, and the mandatory dry-run-then-confirm sequence. Also read:

- [AGENTS.md](../../AGENTS.md)
- [specs/generate_math_worksheets/03. design/design.md](<../../specs/generate_math_worksheets/03. design/design.md>) section 3.9 (Staging And Final Delivery Contract)
- [data/config/project/base.yaml](../../data/config/project/base.yaml) `publishing.final_delivery` and the subject's `naming`

## Parameters

Parse `week`, `grades`, `subject`, `run`, `source_folder`, `mode`, `on_missing`, and `dry_run` exactly
as documented in `commands/deliver-worksheets.md`. Default `week` to `current`, `grades` to `all`,
`subject` to the subject this invocation is already running under, `mode` to the configured
`final_delivery.mode`, `on_missing` to `skip`, and `dry_run` to `yes`.

## Required sequence

1. Echo the resolved parameter set, including the resolved `week_of` and whether pairing came from a
   run root or from staging names.
2. Invoke `scripts/deliver_folder.py` with `--dry-run` and present the plan plus every reported issue
   (`ambiguous_name`, `incomplete_pair`, `unmatched_files`).
3. Stop. Wait for an explicit instruction before re-invoking with `--apply`.

Never resolve an ambiguous pair on the user's behalf. Delivering the wrong document to parents is
worse than delivering nothing.
