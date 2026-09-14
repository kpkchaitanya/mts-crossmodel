---
description: Bring every staged pair to pipeline standard (reconstructing orphans) then deliver.
argument-hint: [week=current|<n>|<iso-date>] [grades=all|<list>] [subject=<subject-id>] [source_folder=<folder-id>] [batch_id=<id>] [dry_run=yes|no]
allowed-tools: Bash, Read
---

Follow `commands/format-and-deliver-worksheets.md` exactly — it is the canonical, harness-neutral
definition of this command; do not re-derive its behavior. This file only registers it as a Claude
Code slash command.

Arguments for this invocation: $ARGUMENTS

Steps:

1. Read `commands/format-and-deliver-worksheets.md` for the full parameter contract, classification
   rules, and behavior.
2. Resolve every parameter from `$ARGUMENTS` and `data/config/project/base.yaml`
   `publishing.provenance` only — never carry a value forward from an earlier turn. Translate any
   near-alias parameter name, echo the full resolved parameter set back to the user, and get explicit
   confirmation before invoking the CLI.
3. Run `scripts/format_and_deliver.py` with `--dry-run` first, regardless of the CLI's own default,
   and present each grade's classification (`conformant` or `orphan`), planned action, and every
   pairing issue.
4. Do not pass `--apply` without a new, explicit instruction from the user after reviewing the dry run.
   Never reconstruct or re-render a `conformant` pair, and never present an inherited (reconstructed)
   answer as independently verified.
5. Report the resulting record per `commands/format-and-deliver-worksheets.md`.
