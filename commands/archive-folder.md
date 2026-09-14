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
.\.venv\Scripts\python.exe scripts/archive_folder.py --folder staging --folder-type folder --grades grade_6 --week 2026-08-31 --dry-run
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
| `folderdate` | `latest`, an ISO date, or a literal folder name | `latest` | Parent mode only; refused in Folder mode rather than ignored. An ISO date resolves to that week's Monday under `publishing.final_delivery.week_folder_pattern` (`Week_<WEEK_OF>`). Selects *which child folder* to descend into — distinct from `week` below, which filters file names once inside whichever folder was resolved. |
| `grades` | `all`, or a comma-separated grade list | `all` | In `publish` (parent mode), selects which grade's destination folder is a target — unchanged from before. In `staging` (folder mode) and for a raw folder ID, it additionally filters that folder's file list to only the requested grades' named documents, using `naming.weekly.prefix_by_grade`. A requested grade with no configured naming prefix is a fail-closed error. |
| `subject` | a configured subject id (e.g. `math`) | none | Filters the file list to only that subject's named documents. Must match the subject the command is running under; a mismatch is refused before anything is touched. Given alone (no `grades`), matches any grade of that subject. |
| `week` | `current`, an instructional week number, or an ISO date | none | Filters the file list to only documents naming that week (the resolved ISO Monday must appear in the file name). Applies in both modes, unlike `folderdate`. |
| `dry_run` | `yes`, `no` | `no` | `yes` resolves and plans without moving anything (`--dry-run`). `no` performs the moves (`--apply`), and is now the CLI's own default when neither flag is given. |

## Filtering

By default — no `grades`, `subject`, or `week` given — archiving stays **content-blind**: every loose
file in the resolved folder moves, exactly as it always has. Giving any of them restricts the file
list to matches only; everything else stays in place and is reported as `filtered_out` so the plan
remains auditable.

`grades` has one exception: in the `publish` preset (parent mode), it already selects which grade's
delivery folder is the target, so it is **not** re-applied as a file filter inside that folder — doing
so would silently exclude a legitimately-named file that doesn't match the naming pattern exactly,
changing the already-relied-upon behavior of archiving everything in a grade's own delivery folder.
`subject` and `week` carry no such prior meaning and always apply, in both modes.

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
3. Run with `--dry-run` first regardless of the CLI's own default. Present the resolved target,
   effective folder, archive folder, and the file list.
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
