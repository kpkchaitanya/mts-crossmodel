---
description: "Trash files in a Drive folder (Drive Trash, never a permanent delete). Destructive."
agent: "agent"
argument-hint: "folder=staging|publish|<folder-id-or-url> [foldertype=folder|parent] [folderdate=latest|<iso-date>|<folder-name>] [grades=all|<list>] [scope=files|archive|both] [dry_run=yes|no]"
---

# Command: Cleanup Folder

## Canonical definition — load this first

- [commands/cleanup-folder.md](../../commands/cleanup-folder.md)

This prompt is a thin entry point only. Follow `commands/cleanup-folder.md` for parameter resolution,
scope selection, and the mandatory dry-run-then-confirm sequence. Also read:

- [AGENTS.md](../../AGENTS.md)
- [specs/generate_math_worksheets/03. design/utility-design.md](<../../specs/generate_math_worksheets/03. design/utility-design.md>) section 3 (canonical design)
- [data/config/project/base.yaml](../../data/config/project/base.yaml) `publishing.cleanup`

## Parameters

Parse `folder`, `foldertype`, `folderdate`, `grades`, `scope`, and `dry_run` exactly as documented in
`commands/cleanup-folder.md`. Default `foldertype` to the preset's configured type, `folderdate` to
`latest`, `grades` to `all`, `scope` to `files`, and `dry_run` to `yes`.

## Required sequence

1. Echo the resolved parameter set, including the resolved `scope`.
2. Invoke `scripts/cleanup_folder.py` with `--dry-run` and present the plan, grouped by scope.
3. Stop. Wait for an explicit instruction **and** the user's confirmation count before re-invoking
   with `--apply --confirm <count>`. Never supply that count yourself.

This utility trashes files. It never deletes folders and never permanently deletes. It is gated by
`publishing.cleanup.enabled`, and it neither introduces nor bypasses a gate.
