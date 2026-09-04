---
description: Trash files in a Drive folder (Drive Trash, never a permanent delete). Destructive.
argument-hint: [folder=staging|publish|<id>|<url>] [foldertype=folder|parent] [folderdate=latest|<date>|<name>] [grades=all|<list>] [scope=files|archive|both] [dry_run=yes|no]
allowed-tools: Bash, Read
---

Follow `commands/cleanup-folder.md` exactly — it is the canonical, harness-neutral definition of this
command; do not re-derive its behavior. This file only registers it as a Claude Code slash command.

Arguments for this invocation: $ARGUMENTS

Steps:

1. Read `commands/cleanup-folder.md` for the full parameter contract, scope selection, and behavior.
2. Resolve every parameter from `$ARGUMENTS` and `data/config/project/base.yaml`
   `publishing.cleanup` only — never carry a value forward from an earlier turn. Translate any
   near-alias parameter name, echo the full resolved parameter set (including the resolved `scope`)
   back to the user, and get explicit confirmation before invoking the CLI.
3. Confirm `publishing.cleanup.enabled` is `true`; if it is `false`, stop and report that the command
   is disabled rather than invoking the CLI.
4. Run `scripts/cleanup_folder.py` with `--dry-run` and present the plan, grouped by scope.
5. Do not pass `--apply` without a new, explicit instruction **and** a confirmation count from the
   user after reviewing the dry run. Never supply that count yourself, and never invoke `--apply` with
   a count that does not match a fresh dry run taken immediately beforehand.
6. Report the resulting Cleanup Record per `commands/cleanup-folder.md`.
