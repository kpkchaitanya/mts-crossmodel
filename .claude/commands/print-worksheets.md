---
description: Export the week's approved worksheet/answer-key pairs to PDF and print them at each grade's class count (always dry-run first, then confirm)
argument-hint: [week=current|<n>|<iso-date>] [grades=all|<list>] [source=staging|publish] [include=both|worksheet|key] [copies=grade_5=6,...] [printer=<name>] [subject=<subject-id>] [dry_run=yes|no]
allowed-tools: Bash, Read
---

Follow `commands/print-worksheets.md` exactly — it is the canonical, harness-neutral definition of
this command; do not re-derive its behavior. This file only registers it as a Claude Code slash
command.

Arguments for this invocation: $ARGUMENTS

Steps:

1. Read `commands/print-worksheets.md` for the full parameter contract, class counts, and behavior.
2. Resolve every parameter from `$ARGUMENTS`, `data/config/project/base.yaml` `publishing.printing`,
   and the subject's `publishing.printing.copies_by_grade` only — never carry a value forward from an
   earlier turn. Echo the full resolved parameter set, including the per-grade copy counts, and get
   explicit confirmation before invoking the CLI.
3. Run `scripts/print_worksheets.py` with `--dry-run` first and present the effective folder, every
   planned job, the total copy count, and every reported issue.
4. Do not pass `--apply` without a new, explicit instruction after the user reviews the dry run, and
   always re-run the dry run immediately beforehand so `--confirm <total copies>` matches the plan now.
5. Report the resulting Print Record per `commands/print-worksheets.md`.

Printing cannot be undone. Never resolve an ambiguous pair on the user's behalf.
