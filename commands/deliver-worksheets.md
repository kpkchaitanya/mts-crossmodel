# Command: Deliver Worksheets

Publishing utility. Copies approved worksheet/answer-key pairs from staging into
`Week_<WEEK_OF>` under each grade's audience-facing destination folder.

Canonical design: [design.md](<../specs/generate_math_worksheets/03. design/design.md>) section 3.9
(Staging And Final Delivery Contract) and
[utility-design.md](<../specs/generate_math_worksheets/03. design/utility-design.md>) section 4.

This is the same Final Delivery step the generate-worksheet workflow performs, exposed as a
standalone command. It is a distribution step, never an authoring step: it never renders, edits,
re-numbers, or re-verifies content. It introduces no gate and bypasses none.

Concrete CLI entry point:

```powershell
.\.venv\Scripts\python.exe scripts/deliver_folder.py --week 2026-08-31 --dry-run
.\.venv\Scripts\python.exe scripts/deliver_folder.py --week 2026-08-31 --grades grade_6 --apply
.\.venv\Scripts\python.exe scripts/deliver_folder.py --run-root data/transactions/runs/<run-id> --week current --apply
```

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `week` | `current`, an instructional week number, or an ISO date | `current` | Resolved to that week's ISO Monday against `calendar.week_1_start`. Names the `Week_<WEEK_OF>` folder and selects which staged documents match. |
| `grades` | `all`, or a comma-separated grade list | `all` | A requested grade with no configured destination is a fail-closed error. |
| `run` (run root) | a run directory | none | When given, pairs come from that run's `published-artifacts.json`. See Pairing below. |
| `source_folder` | a Drive folder ID | `publishing.staging.approved_folder_id` | Staging folder to pair from when no run root is given. |
| `mode` | `copy`, `move` | `publishing.final_delivery.mode` (`copy`) | `copy` keeps staging as the audit trail. |
| `subject` | a configured subject id (e.g. `math`) | the subject the command is running under | Must match; a mismatch is refused before any pairing or delivery. |
| `on_missing` | `skip`, `fail` | `skip` | `skip` delivers every grade that has a staged pair and records the rest; `fail` blocks the run when any requested grade is missing. |
| `dry_run` | `yes`, `no` | `yes` | `yes` resolves and pairs without copying anything. |

## Pairing

Delivery needs to know which document is which grade's worksheet and which is its answer key. There
are two sources, and the more exact one wins:

1. **Run root** (`--run-root`). The run's `published-artifacts.json` states grade and role alongside
   exact document IDs. Nothing is inferred, and duplicates sitting in staging are irrelevant.
2. **Staging document names** (default). Names are matched against
   `naming.weekly.document_name_pattern` and `answer_key_suffix` per grade prefix — the same
   configuration the renderer uses to create them.

Name matching never guesses:

- Two documents matching one expected name is `ambiguous_name`; that grade is skipped and reported.
- A worksheet without its `_KEY` is `incomplete_pair`; that grade is skipped and reported.
- Files matching no expected name (for example `Copy of …`) are reported as `unmatched_files` and
  never delivered.

A grade with no deliverable pair is **skipped and recorded**, so a partially staged week still
delivers every grade that is ready. Pass `on_missing=fail` when a run must not proceed unless every
requested grade is present.

## Behavior

1. Resolve every parameter from this invocation and configuration only.
2. Echo the resolved parameter set, including the resolved `week_of` and pairing source.
3. Run with `--dry-run` first. Present the resolved week folder, the pair chosen per grade, and every
   reported issue.
4. Do not proceed to `--apply` without a new, explicit instruction.
5. Report the resulting Delivery Record.

Delivery is idempotent: `reuse_existing_week_folder` means a re-delivery resolves the existing week
folder rather than creating a second one, so a correction lands in place.

## Rollback

With the default `mode: copy`, staging is untouched; remove the copied documents from the destination
week folder to revert. `mode: move` relocates the staged documents instead, so reverting means moving
them back.
