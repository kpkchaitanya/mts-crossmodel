# Command: Duplicate Worksheet

Publishing utility. Copies one existing worksheet/answer-key pair and renames both copies from the
target subject, Worksheet Type, grade, and instructional week.

Canonical design: [utility-design.md](<../specs/generate_math_worksheets/03. design/utility-design.md>) section 9.

This command never edits document content, reconstructs a Spec, renders, re-verifies, approves,
publishes, delivers, or rewrites provenance metadata. A renamed copy is not a claim that the target
subject or grade independently authored or verified the content.

Concrete CLI entry point:

```powershell
.\.venv\Scripts\python.exe scripts/duplicate_worksheet.py --from-subject math --from-grade grade_6 --to-subject ela --to-grade grade_6
.\.venv\Scripts\python.exe scripts/duplicate_worksheet.py --from-subject math --from-grade grade_6 --to-subject math --to-grade grade_4 --source-folder staging --target-folder <folder-id> --dry-run
```

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `from_subject` | configured subject id | required | Selects source naming configuration. |
| `from_worksheettype` | configured naming kind | `publishing.duplicate_worksheet.default_worksheet_type` (`weekly`) | Maps to CLI `--from-worksheet-type`. |
| `from_grade` | configured grade id | required | Selects the exact source pair. |
| `to_subject` | configured subject id | required | Selects target naming configuration. |
| `to_worksheettype` | configured naming kind | `publishing.duplicate_worksheet.default_worksheet_type` (`weekly`) | Maps to CLI `--to-worksheet-type`. |
| `to_grade` | configured grade id | required | Selects the target naming prefix. |
| `week` | `current`, instructional week number, or ISO date | `current` | Resolves to the ISO Monday used in both source and target names. |
| `source_folder` | configured preset, Drive folder ID, or Drive folder URL | `publishing.duplicate_worksheet.default_source_folder` (`staging`) | Presets resolve through configured canonical paths. |
| `target_folder` | configured preset, Drive folder ID, or Drive folder URL | resolved source folder | Omit it to leave the copies beside the source files. |
| `dry_run` | `yes`, `no` | `no` | `yes` resolves and reports without copying; `no` copies immediately. |

Parameter names are strict at the CLI boundary. The command layer translates user-facing
`worksheettype` and `source_folder` forms to their hyphenated CLI flags, echoes the complete resolved
request, and does not carry values forward from an earlier invocation.

## Behavior

1. Resolve source and target distribution configuration independently from this invocation.
2. Resolve `week` to its ISO Monday, `source_folder` to its configured/default folder, and omitted
   `target_folder` to the resolved source folder.
3. Require exactly one source worksheet and one source answer key under the configured source names.
4. Derive both target names from the target subject and Worksheet Type naming configuration.
5. Refuse before copying when either target name already exists. Never overwrite or guess.
6. With `dry_run=yes`, report the exact pair, folder IDs, and target names without mutation.
7. With the default `dry_run=no`, copy and rename both files and report the Duplicate Worksheet Record.

## Rollback

The source pair is never changed. Remove the two copied file IDs named in the Duplicate Worksheet
Record to revert an applied operation.