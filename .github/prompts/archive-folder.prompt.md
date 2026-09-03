---
description: "Archive a Drive folder's previous set of loose files into its Archive folder."
agent: "agent"
argument-hint: "folder=staging|publish|<folder-id-or-url> [foldertype=folder|parent] [folderdate=latest|<iso-date>|<folder-name>] [grades=all|<list>] [dry_run=yes|no]"
---

# Command: Archive Folder

## Canonical definition — load this first

- [commands/archive-folder.md](../../commands/archive-folder.md)

This prompt is a thin entry point only. Follow `commands/archive-folder.md` for parameter resolution,
mode selection, and the mandatory dry-run-then-confirm sequence. Also read:

- [AGENTS.md](../../AGENTS.md)
- [specs/generate_math_worksheets/03. design/utility-design.md](<../../specs/generate_math_worksheets/03. design/utility-design.md>) (canonical design)
- [data/config/project/base.yaml](../../data/config/project/base.yaml) `publishing.archive`

## Parameters

Parse `folder`, `foldertype`, `folderdate`, `grades`, and `dry_run` exactly as documented in
`commands/archive-folder.md`. Default `foldertype` to the preset's configured type, `folderdate` to
`latest`, `grades` to `all`, and `dry_run` to `yes`.

## Required sequence

1. Echo the resolved parameter set.
2. Invoke `scripts/archive_folder.py` with `--dry-run` and present the plan.
3. Stop. Wait for an explicit instruction before re-invoking with `--apply`.

This utility moves files. It never renders, edits, verifies, publishes, or deletes, and it neither
introduces nor bypasses a gate.
