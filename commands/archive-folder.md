# Command: Archive Folder

Publishing utility. Moves the previous set of loose files in a Drive folder into that folder's
`Archive` child folder, so the folder presents only the current set.

Canonical design: [utility-design.md](<../specs/generate_math_worksheets/03. design/utility-design.md>) section 2.

This command never renders, edits, re-numbers, verifies, publishes, or deletes anything. It moves
files between folders. It introduces no gate and bypasses none.

Concrete CLI entry point:

```powershell
.\.venv\Scripts\python.exe scripts/archive_folder.py --folder staging --folder-type folder --dry-run
.\.venv\Scripts\python.exe scripts/archive_folder.py --folder publish --folder-type parent --folder-date latest --apply
```

Parameter names are strict at the CLI boundary. If an invocation contains a near-alias, such as
`grade=6` or `type=parent`, the model/prompt layer must translate it to the canonical parameter,
replay the full interpreted parameter set to the user, get explicit confirmation, and only then
invoke the CLI. The CLI must reject the non-canonical parameter instead of silently accepting it.

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `folder` | `staging`, `publish`, a Drive folder ID, or a Drive folder URL | required | Presets resolve through `data/config/project/base.yaml` `publishing.archive.targets`, which reference the canonical staging and delivery destinations. Folder IDs are never duplicated in the archive configuration. |
| `foldertype` | `folder`, `parent` | the preset's `folder_type` | Required when `folder` is a raw ID or URL, because no preset supplies it. Never inferred from folder contents. |
| `folderdate` | `latest`, an ISO date, or a literal folder name | `latest` | Parent mode only; refused in Folder mode rather than ignored. An ISO date resolves to that week's Monday under `publishing.final_delivery.week_folder_pattern` (`Week_<WEEK_OF>`). |
| `grades` | `all`, or a comma-separated grade list | `all` | `publish` preset only. A requested grade with no configured destination is a fail-closed error. |
| `dry_run` | `yes`, `no` | `yes` | `yes` resolves and plans without moving anything (`--dry-run`). `no` performs the moves (`--apply`). |

## Modes

**Folder mode** (`foldertype=folder`) archives the resolved folder itself: every direct file moves
into its `Archive` child, which is created only when absent. Sub-folders are never moved and never
descended into.

**Parent mode** (`foldertype=parent`) first selects a child folder of the resolved parent — the most
recently created non-archive child by default, or the one named by `folderdate` — then applies Folder
mode to it. If the parent itself contains loose files, the command refuses and reports them rather
than falling back to Folder mode.

## Presets

| Preset | Mode | Resolves from |
|---|---|---|
| `staging` | `folder` | `publishing.staging.approved_folder_id` |
| `publish` | `parent` | `publishing.final_delivery.destinations_by_grade.<grade>.folder_id`, one target per grade |

## Behavior

1. Resolve every parameter from this invocation and configuration only. Never carry a value forward
   from an earlier turn.
2. Echo the resolved parameter set before invoking the CLI.
3. Run with `--dry-run` first. Present the resolved target, effective folder, archive folder, and the
   file list.
4. Do not proceed to `--apply` without a new, explicit instruction from the user. A dry run is never
   self-approving.
5. Report the resulting Archive Record. On `status=failed`, report the moved/unmoved split; re-running
   is safe because an already-archived folder records a no-op.

## Rollback

Archiving only re-parents files; nothing is trashed, renamed, or edited. To revert, move the files
named in the Archive Record back out of the `Archive` folder. To disable the utility entirely, set
`publishing.archive.enabled: false`.

## Not in scope

Automatic in-pipeline archiving. `publishing.archive.auto_archive.before_render` and
`.before_delivery` are specified in utility-design section 2.8 but ship `false`; enabling them is a
separate design and approval.
