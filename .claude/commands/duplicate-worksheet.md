---
description: Copy and rename one worksheet/answer-key pair for a target subject, Worksheet Type, and grade.
argument-hint: from_subject=<id> from_grade=<grade> to_subject=<id> to_grade=<grade> [from_worksheettype=weekly] [to_worksheettype=weekly] [week=current|<n>|<iso-date>] [source_folder=staging|<id>|<url>] [target_folder=<preset>|<id>|<url>] [dry_run=yes|no]
allowed-tools: Bash, Read
---

Follow `commands/duplicate-worksheet.md` exactly. It is the canonical, harness-neutral definition;
this file only registers the Claude Code command.

Arguments for this invocation: $ARGUMENTS

Steps:

1. Read `commands/duplicate-worksheet.md` for the complete parameter and failure contract.
2. Resolve every parameter from `$ARGUMENTS`, project configuration, and both subject naming files
   only. Echo the full resolved request, including both folder IDs and target names.
3. Invoke `scripts/duplicate_worksheet.py`; pass `--dry-run` only when `dry_run=yes`. The default is
   apply mode (`dry_run=no`).
4. Report the resulting Duplicate Worksheet Record. Never overwrite an existing target name or infer
   a missing/ambiguous source pair.