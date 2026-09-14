---
description: "Export the week's approved worksheet/answer-key pairs to PDF and print them at each grade's class count."
agent: "agent"
argument-hint: "[week=current|<n>|<iso-date>] [grades=all|<list>] [source=staging|publish] [include=both|worksheet|key] [copies=grade_5=6,...] [printer=<name>] [subject=<subject-id>] [dry_run=yes|no]"
---

# Command: Print Worksheets

## Canonical definition — load this first

- [commands/print-worksheets.md](../../commands/print-worksheets.md)

This prompt is a thin entry point only. Follow `commands/print-worksheets.md` for parameter
resolution, class counts, and the mandatory dry-run-then-confirm sequence. Also read:

- [AGENTS.md](../../AGENTS.md)
- [specs/generate_math_worksheets/03. design/utility-design.md](<../../specs/generate_math_worksheets/03. design/utility-design.md>) section 6
- [data/config/project/base.yaml](../../data/config/project/base.yaml) `publishing.printing` and the subject's `publishing.printing.copies_by_grade`

## Parameters

Parse `week`, `grades`, `source`, `include`, `copies`, `printer`, `subject`, and `dry_run` exactly as
documented in `commands/print-worksheets.md`. Default `week` to `current`, `grades` to `all`, `source`
to the configured `default_source`, `include` to `both`, `printer` to the configured `printer_name`,
`subject` to the subject this invocation is already running under, and `dry_run` to `yes`.

## Required sequence

1. Echo the resolved parameter set, including the resolved `week_of`, source folder, printer, and the
   per-grade copy counts that will be used.
2. Invoke `scripts/print_worksheets.py` with `--dry-run` and present every planned job, the total copy
   count, and every reported issue (`ambiguous_name`, `incomplete_pair`, `unmatched_files`,
   `no_copy_counts_configured`, `missing_pair`).
3. Stop. Wait for an explicit instruction before re-invoking with `--apply --confirm <total copies>`,
   and re-run the dry run immediately beforehand so the count still matches.

Printing cannot be undone, and an answer key printed for a class is worse than nothing printed. Never
resolve an ambiguous pair on the user's behalf.
