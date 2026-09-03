# Archive Folder Utility - M0-M8 Feature Record

Status: Complete through M7; M8 open
Owner: MTS Publishing
Requested: 2026-09-03
Change type: Enhancement (publishing utility)

## Intent and scope

Before a new instructional week's artifacts are placed into a Drive folder, the previous week's
artifacts in that folder must be set aside so the folder presents only the current set. The Archive
Folder utility moves every loose file in a target folder into an `Archive` child folder, in either
Folder mode (the folder itself) or Parent mode (the resolved week sub-folder of a parent).

It is built as a publishing-module capability, not a standalone script, so it can later be invoked
automatically by the publishing pipeline. Canonical design:
[utility-design.md](../03.%20design/utility-design.md).

Excluded from this change set:

- Automatic in-pipeline archiving. The `auto_archive` hooks are specified (utility-design §2.8) but
  ship disabled; enabling them is a separate design and approval.
- Any change to rendering, verification, publishing, or delivery behavior.
- Deletion. Archiving only re-parents files; nothing is trashed.
- Subject-specific archive targets. The capability is subject-agnostic.

## Decisions

- Policy lives in `src/mts/publishing/archive.py` and takes plain listings plus resolved
  configuration; all Drive I/O stays in the adapter. This is what makes the future pipeline hook a
  call site rather than a rewrite.
- `scripts/archive_folder.py` is a thin CLI over `run_archive(...)` and holds no decision logic.
- Presets reference canonical configuration paths (`publishing.staging.approved_folder_id`,
  `publishing.final_delivery.destinations_by_grade`); folder IDs are never duplicated.
- Files are moved, not copied. A copy would leave the previous set visible and defeat the purpose.
- Parent mode refuses when the parent contains loose files, rather than falling back to Folder mode.
- An empty target folder is a recorded success no-op, which is what makes re-runs and the future
  automatic hook safe.
- `dry_run` defaults to `yes`; the command never proceeds from a dry run to a real run without a new
  explicit instruction.
- The utility is gate-neutral: it introduces no gate, bypasses none, and grants no approval.

## Acceptance criteria

1. Folder mode moves every direct file of the target folder into its `Archive` child, creating that
   child only when absent, and never moves or descends into sub-folders.
2. Parent mode resolves the latest non-archive child folder (or an explicitly requested ISO date or
   folder name) and then applies Folder mode to it.
3. Parent mode refuses, with the loose-file list, when the parent contains loose files.
4. The `staging` preset resolves to `publishing.staging.approved_folder_id` in Folder mode, and the
   `publish` preset expands to one Parent-mode target per configured grade, honoring a `grades`
   restriction and failing closed on an unconfigured grade.
5. A dry run reports the resolved target, effective folder, archive folder, and file list, and mutates
   nothing.
6. Every invocation emits an Archive Record; a second invocation on an already-archived folder records
   a no-op and succeeds.
7. Partial failure records moved and unmoved files separately and reports failure, leaving a safe
   re-run.
8. `scripts/archive_folder.py` contains no decision logic: every behavior above is asserted directly
   against `run_archive(...)`.
9. No existing render, publish, or delivery behavior changes, and `auto_archive` flags remain `false`.

## M0-M8 status

| Milestone | Status | Evidence / next action |
|---|---|---|
| M0 | Complete | Policy and adapter tests written against the fake-Drive pattern before the live run. |
| M1 | Complete | Intent, scope, and exclusions in this record. |
| M2 | Complete | Acceptance criteria above. |
| M3 | Complete | Layering, ownership, and two-mode constraint decided in utility-design §2.2. |
| M4 | Complete | Resolution, archive, adapter, configuration, and failure contracts in utility-design §2.3-§2.10. |
| M5 | Complete | Adapter primitives, `publishing.archive` config, `src/mts/publishing/archive.py`, `scripts/archive_folder.py`, `commands/archive-folder.md`, prompt entry point, README row. |
| M6 | Complete | 22 focused archive tests plus the full suite pass (128 total). |
| M7 | Complete | Both reference targets archived on 2026-09-03; both re-runs recorded a no-op with no duplicate Archive folder. |
| M8 | Ready for review | Decide whether to design the `auto_archive` pipeline hooks. |

## Phased implementation steps

### Phase 1 - Adapter primitives (M5)

`src/mts/infrastructure/google_docs/google_docs_adapter.py`, extending the contract in design.md §3.6
as items 8-10. Primitives only; no policy.

| Task | Detail |
|---|---|
| 1.1 | `list_child_files(folder_id)` - non-trashed, non-folder direct children returning `id,name,mimeType,createdTime,webViewLink`. |
| 1.2 | `list_child_folders(folder_id)` - non-trashed direct child folders ordered by `createdTime desc`. |
| 1.3 | `move_file(file_id, destination_id)` - re-parent one file and confirm the destination is in the resulting parents, matching the post-condition style of `publish_pair`/`deliver_pair`. |
| 1.4 | Reuse `ensure_child_folder` unchanged for the archive folder; introduce no new folder-creation semantics. |

Exit: primitives exist with fake-Drive tests for filtering, ordering, and the move post-condition.

### Phase 2 - Configuration (M5)

| Task | Detail |
|---|---|
| 2.1 | Add `publishing.archive` to `data/config/project/base.yaml` per utility-design §2.6: `enabled`, `archive_folder_name`, `targets.staging`, `targets.publish`, `auto_archive` (both `false`). |
| 2.2 | Confirm the block survives `resolve_effective_config` (`src/mts/infrastructure/configuration/config_resolver.py`, re-exported by `mts.setup_project.configure`) for a `{subject, worksheet_type}` request. |
| 2.3 | Confirm no subject config defines archive targets. |

Exit: `resolve_effective_config(...)["publishing"]["archive"]` returns the block intact.

### Phase 3 - Policy layer (M0, M5, M6)

New `src/mts/publishing/archive.py`. Pure functions over plain data; no Drive calls, no `subject`
branching.

| Task | Detail |
|---|---|
| 3.1 | `resolve_targets(request, effective_config)` - preset/ID/URL handling, `publish` grade expansion, `grades` restriction, unconfigured-grade fail-closed. |
| 3.2 | `select_effective_folder(child_folders, folder_date, archive_folder_name, week_folder_pattern)` - latest / ISO-date-to-`Week_<WEEK_OF>` / literal-name selection, excluding the archive folder. |
| 3.3 | `plan_archive(child_files)` - the move plan; empty listing yields a no-op plan. |
| 3.4 | Parent-mode loose-file precondition check returning a refusal with the offending files. |
| 3.5 | Archive Record construction: request, resolved targets, effective folder, archive folder (and whether created), moved and unmoved files. |

Exit: policy unit tests in `tests/` pass with no credentials and no adapter import.

### Phase 4 - Orchestration (M5, M6)

| Task | Detail |
|---|---|
| 4.1 | `run_archive(request, effective_config, adapter, *, dry_run)` sequencing resolve → precondition → select → plan → apply → record. |
| 4.2 | Dry run returns a complete record having called no mutating adapter method. |
| 4.3 | Partial-failure handling: keep already-moved files moved, split moved/unmoved in the record, report failure. |
| 4.4 | Record emission - returned to the caller; written as `archived-artifacts.json` when a run root is supplied, mirroring the Delivery Record in design.md §3.9 rule 8. |

Exit: orchestration tests cover dry run, real run, loose-file refusal, and partial failure.

### Phase 5 - Entry points (M5)

| Task | Detail |
|---|---|
| 5.1 | `scripts/archive_folder.py` - argparse (`--folder`, `--folder-type`, `--folder-date`, `--grades`, `--dry-run`, optional `--report`), OAuth client construction and `resolve_effective_config` following `scripts/deliver_weekly_worksheets.py`, then a single `run_archive(...)` call and human-readable output. |
| 5.2 | `commands/archive-folder.md` - parameter table from utility-design §2.7, strict parameter names, resolved-parameter echo before invocation, mandatory dry-run-then-confirm. |
| 5.3 | Register the command alongside the existing entries in `commands/`. |

Exit: `--dry-run` runs end to end against a reference target and prints a resolved plan.

### Phase 6 - Validation (M7)

| Task | Detail |
|---|---|
| 6.1 | Dry run `--folder staging --folder-type folder` against `1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS`; review the plan. |
| 6.2 | Dry run `--folder publish --folder-type parent --folder-date latest --grades grade_6` against `10tSM2SwAxzGkzuYT47vNCo16K9TtPZre`; confirm the selected week folder. |
| 6.3 | On explicit approval, execute both for real and review the Archive Records. |
| 6.4 | Re-run both and confirm each records a no-op. |
| 6.5 | Update this record's M0-M8 status with the evidence. |

Exit: both reference targets archived, both re-runs no-op, criteria 1-9 demonstrated.

## Validation and rollback approach

Validation:

- Unit and integration tests run with plain `python -m pytest`; Drive scripts use
  `.\.venv\Scripts\python.exe`. All behavior tests use the existing fake-Drive pattern in
  `tests/integration/test_google_docs_adapter.py`; no test performs live Drive I/O.
- Live validation is dry-run-first against the two reference targets (Phase 6).

Rollback:

- Archiving only re-parents files. To revert a run, move the files named in the Archive Record back out
  of the `Archive` folder; nothing is trashed, renamed, or edited.
- To disable the capability, set `publishing.archive.enabled: false`; no existing Spec, published, or
  delivered artifact is affected.
- The change set adds files and one configuration block. No existing behavior is modified, so removing
  the additions restores the prior state exactly.

## Decisions and unresolved risks

Open, defaulted for now and cheap to change before Phase 5:

- Archive folder name defaults to `Archive` (`archive_folder_name`).
- The `publish` preset defaults to `grades=all`.
- `dry_run` defaults to `yes`.

Risks:

- **Wrong folder archived in Parent mode.** Mitigated by dry-run default, the explicit resolved-target
  echo, and refusal when the parent holds loose files.
- **Latest-child selection is ambiguous** if week folders are created out of order. Mitigated by
  `createdTime desc` ordering plus the explicit ISO-date and literal-name options; a mismatch is a
  refusal, not a guess.
- **Non-worksheet files swept up.** Archiving is content-blind by design (utility-design §2.4 rule 6);
  the dry run is the control.
- **Drift back into script-held logic** when the pipeline hook is added later. Mitigated by acceptance
  criterion 8 and its contract test.

## Progress status

Phases 1-6 complete; 128 tests pass. Validated live on 2026-09-03:

- `staging` (folder mode) archived 5 files from `1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS`, including
  duplicate-named re-renders, which archiving moves because it is content-blind by design.
- `publish` (parent mode, `grade_6`) resolved `10tSM2SwAxzGkzuYT47vNCo16K9TtPZre` to its latest child
  `Week_2026-08-31` and archived 10 files.
- Re-running both recorded `no_op` and moved nothing. Neither re-run raised the ambiguous-archive
  error, confirming the existing `Archive` folder was reused rather than duplicated.

Acceptance criteria 1-9 are demonstrated. Remaining decision (M8): whether to design the
`auto_archive` pipeline hooks in utility-design section 2.8; both flags stay `false` until then.
