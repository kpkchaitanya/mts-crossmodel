---
description: Move a Drive folder's previous loose files into its Archive child folder (always dry-run first, then confirm)
argument-hint: [folder=staging|publish|<id>|<url>] [foldertype=folder|parent] [folderdate=latest|<date>|<name>] [grades=all|<list>] [subject=<subject-id>] [week=current|<n>|<iso-date>] [dry_run=yes|no]
allowed-tools: Bash, Read
---

Follow `commands/archive-folder.md` exactly — it is the canonical, harness-neutral definition of this
command; do not re-derive its behavior. This file only registers it as a Claude Code slash command.

Arguments for this invocation: $ARGUMENTS

Steps:

1. Read `commands/archive-folder.md` for the full parameter contract, presets, modes, and behavior.
2. Resolve every parameter from `$ARGUMENTS` and `data/config/project/base.yaml` `publishing.archive`
   only — never carry a value forward from an earlier turn. Translate any near-alias parameter name,
   echo the full resolved parameter set back to the user, and get explicit confirmation before invoking
   the CLI.
3. Run `scripts/archive_folder.py` with `--dry-run` first, regardless of the CLI's own default (now
   apply-by-default), and present the resolved target, effective folder, archive folder, and file list.
4. Do not pass `--apply` without a new, explicit instruction from the user after reviewing the dry run.
5. Report the resulting Archive Record per `commands/archive-folder.md`.
