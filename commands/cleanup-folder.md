# Command: Cleanup Folder

Publishing utility. Trashes files in a Drive folder. This is the destructive companion to
[`/archive-folder`](archive-folder.md) and shares its resolution contract exactly.

Canonical design: [utility-design.md](<../specs/generate_math_worksheets/03. design/utility-design.md>) section 3.

Deletion means **Drive Trash**, never a permanent delete, so a mistaken run stays recoverable.
Folders are never deleted — including the `Archive` folder, even when cleanup empties it.

This command never renders, edits, verifies, or publishes anything. It introduces no gate and
bypasses none.

Gated by configuration: `data/config/project/base.yaml` `publishing.cleanup.enabled`. Setting it
`false` disables the command entirely.

Concrete CLI entry point:

```powershell
.\.venv\Scripts\python.exe scripts/cleanup_folder.py --folder staging --folder-type folder --dry-run
.\.venv\Scripts\python.exe scripts/cleanup_folder.py --folder staging --folder-type folder --scope archive --apply --confirm 12
```

Parameter names are strict at the CLI boundary. Translate a near-alias, replay the full interpreted
parameter set to the user, get explicit confirmation, and only then invoke the CLI.

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `folder` | `staging`, `publish`, a Drive folder ID, or a Drive folder URL | required | Same presets and canonical sources as `/archive-folder`. |
| `foldertype` | `folder`, `parent` | the preset's `folder_type` | Required when `folder` is a raw ID or URL. |
| `folderdate` | `latest`, an ISO date, or a literal folder name | `latest` | Parent mode only. |
| `grades` | `all`, or a comma-separated grade list | `all` | `publish` preset only. |
| `scope` | `files`, `archive`, `both` | `files` | What gets trashed. See below. |
| `dry_run` | `yes`, `no` | `yes` | Applying additionally requires `--confirm <count>`. |

## Scope

| `scope` | Trashes |
|---|---|
| `files` (default) | Loose files directly in the effective folder — the same set `/archive-folder` would move |
| `archive` | Files inside the effective folder's `Archive` child — purge accumulated archives |
| `both` | Both groups, reported separately in the record |

A missing `Archive` child contributes nothing and is not an error. Cleanup never descends past one
level.

## Confirmation

An applying run must pass `--confirm <count>` matching the number of files planned **at apply time**.
If the folder changed since the dry run, the counts differ, the run refuses, and nothing is deleted.
The correct response is a fresh dry run, not a larger number.

The command layer must present the dry-run plan and stop. It may not supply the confirmation count on
the user's behalf — the count is the user's acknowledgement of a specific plan.

## Behavior

1. Resolve every parameter from this invocation and configuration only.
2. Echo the resolved parameter set, including the resolved `scope`.
3. Run with `--dry-run` first. Present the resolved target, effective folder, and the file list
   grouped by scope.
4. Do not proceed to `--apply` without a new, explicit instruction and the user's confirmation count.
5. Report the resulting Cleanup Record. On `status=failed`, report the deleted/undeleted split.

## Rollback

Restore the files from Drive Trash. This is the only rollback this utility has, which is why
permanent deletion is deliberately not implemented.
