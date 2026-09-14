---
description: Copy approved worksheet/answer-key pairs from staging into per-grade Week_<WEEK_OF> folders.
argument-hint: [week=current|<n>|<iso-date>] [grades=all|<list>] [subject=<subject-id>] [run=<run-id>] [source_folder=<folder-id>] [mode=copy|move] [on_missing=skip|fail] [dry_run=yes|no]
allowed-tools: Bash, Read
---

Follow `commands/deliver-worksheets.md` exactly — it is the canonical, harness-neutral definition of
this command; do not re-derive its behavior. This file only registers it as a Claude Code slash
command.

Arguments for this invocation: $ARGUMENTS

Steps:

1. Read `commands/deliver-worksheets.md` for the full parameter contract, pairing rules, and behavior.
2. Resolve every parameter from `$ARGUMENTS` and `data/config/project/base.yaml`
   `publishing.final_delivery` (and the subject's `naming`) only — never carry a value forward from an
   earlier turn. Translate any near-alias parameter name, echo the full resolved parameter set
   (including the resolved `week_of` and whether pairing came from a run root or from staging names)
   back to the user, and get explicit confirmation before invoking the CLI.
3. Run `scripts/deliver_folder.py` with `--dry-run` first, regardless of the CLI's own default, and
   present the plan plus every reported issue (`ambiguous_name`, `incomplete_pair`, `unmatched_files`).
4. Do not pass `--apply` without a new, explicit instruction from the user after reviewing the dry run.
   Never resolve an ambiguous pair on the user's behalf — delivering the wrong document to parents is
   worse than delivering nothing.
5. Report the resulting Delivery Record per `commands/deliver-worksheets.md`.
