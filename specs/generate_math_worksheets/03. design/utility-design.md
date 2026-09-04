# MTS Worksheet Generation - Publishing Utility Design

Companion to `design.md`. This document specifies **publishing-side utilities**: capabilities that
operate on already-produced artifacts and their distribution locations, rather than on curriculum,
questions, or verification.

`design.md` remains authoritative for the lifecycle, gates, and subject/worksheet-type contracts.
Where this document extends a contract in `design.md`, it says so explicitly and does not restate it.

## Table of Contents

1. [Purpose And Scope](#1-purpose-and-scope)
2. [Utility: Archive Folder](#2-utility-archive-folder)
   - [2.1 Requirement](#21-requirement)
   - [2.2 Placement In The Publishing Module](#22-placement-in-the-publishing-module)
   - [2.3 Resolution Contract](#23-resolution-contract)
   - [2.4 Archive Contract](#24-archive-contract)
   - [2.5 Adapter Extensions](#25-adapter-extensions)
   - [2.6 Configuration Contract](#26-configuration-contract)
   - [2.7 Command And CLI Surface](#27-command-and-cli-surface)
   - [2.8 Pipeline Integration (Future)](#28-pipeline-integration-future)
   - [2.9 Evidence And Idempotence](#29-evidence-and-idempotence)
   - [2.10 Failure Modes](#210-failure-modes)
3. [Utility: Cleanup Folder](#3-utility-cleanup-folder)
   - [3.1 Requirement](#31-requirement)
   - [3.2 Shared Resolution](#32-shared-resolution)
   - [3.3 Scope Contract](#33-scope-contract)
   - [3.4 Deletion Contract](#34-deletion-contract)
   - [3.5 Confirmation Contract](#35-confirmation-contract)
   - [3.6 Adapter Extension](#36-adapter-extension)
   - [3.7 Configuration Contract](#37-configuration-contract)
   - [3.8 Command And CLI Surface](#38-command-and-cli-surface)
   - [3.9 Evidence And Failure Modes](#39-evidence-and-failure-modes)
4. [Utility: Deliver Worksheets](#4-utility-deliver-worksheets)
   - [4.1 Requirement](#41-requirement)
   - [4.2 Relationship To The Workflow](#42-relationship-to-the-workflow)
   - [4.3 Pairing Contract](#43-pairing-contract)
   - [4.4 Naming Contract](#44-naming-contract)
   - [4.5 Delivery Contract](#45-delivery-contract)
   - [4.6 Command And CLI Surface](#46-command-and-cli-surface)
5. [Utility: Format-And-Deliver Worksheets](#5-utility-format-and-deliver-worksheets)
   - [5.1 Requirement](#51-requirement)
   - [5.2 Provenance Contract](#52-provenance-contract)
   - [5.3 Display Numbering Contract](#53-display-numbering-contract)
   - [5.4 Classification Contract](#54-classification-contract)
   - [5.5 Reconstruction Contract](#55-reconstruction-contract)
   - [5.6 Composition Contract](#56-composition-contract)
   - [5.7 Authoring Contract](#57-authoring-contract)
   - [5.8 Command And CLI Surface](#58-command-and-cli-surface)
6. [Utility: Print Worksheets](#6-utility-print-worksheets)
   - [6.1 Requirement](#61-requirement)
   - [6.2 Shared Resolution And Pairing](#62-shared-resolution-and-pairing)
   - [6.3 Copy Count Contract](#63-copy-count-contract)
   - [6.4 Print Contract](#64-print-contract)
   - [6.5 Configuration Contract](#65-configuration-contract)
   - [6.6 Subject Neutrality](#66-subject-neutrality)
   - [6.7 Command And CLI Surface](#67-command-and-cli-surface)
7. [Test Design](#7-test-design)
8. [Implementation Sequence](#8-implementation-sequence)

## 1. Purpose And Scope

Publishing utilities share three properties, and those properties are what qualifies something for
this document:

1. They act on **artifact locations** (Drive folders and the documents in them), not on Spec content.
   They never render, edit, re-number, or re-verify a worksheet.
2. They are **gate-neutral**. They introduce no new gate and bypass none. They are housekeeping
   around the Staging and Final Delivery contract (`design.md` §3.9), not a step inside it.
3. They must be usable in **two modes**: standalone, invoked by a human between runs; and in-pipeline,
   invoked automatically by the publishing module as part of a worksheet run.

The two-mode requirement is the central design constraint. It is why decision logic is separated from
I/O rather than written directly into a script.

## 2. Utility: Archive Folder

### 2.1 Requirement

Before a new instructional week's artifacts are placed into a Drive folder, the previous week's
artifacts in that folder must be set aside so the folder presents only the current set.

- **Folder mode.** Given a folder, move every **file** (not sub-folder) directly inside it into a
  child folder named by configuration (default `Archive`), creating that child folder if it is
  absent.
- **Parent mode.** Given a parent folder that holds no loose files — only dated week sub-folders —
  select the target sub-folder (most recently created by default, or an explicitly requested one),
  then apply Folder mode to it.
- Both modes are exposed through a slash command with named presets for the two locations that
  actually accumulate artifacts:
  - `Folder=Staging FolderType=Folder` → the staging approved folder.
  - `Folder=Publish FolderType=Parent FolderDate=Latest|<date>` → each per-grade Final Delivery
    parent, archiving inside its resolved week folder.

Reference targets used to validate the two modes:

| Preset | Mode | Folder | Canonical config key |
|---|---|---|---|
| `staging` | folder | `1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS` | `publishing.staging.approved_folder_id` |
| `publish` | parent | `10tSM2SwAxzGkzuYT47vNCo16K9TtPZre` (Grade 6) | `publishing.final_delivery.destinations_by_grade.<grade>.folder_id` |

Folder IDs are never duplicated by this utility. Presets **reference** the canonical keys above; a
change to a destination in configuration changes what the preset archives, with no second edit.

### 2.2 Placement In The Publishing Module

Archiving is a publishing capability, so it is owned by the publishing module and layered the same
way the rest of publishing is:

| Layer | Location | Responsibility | External I/O |
|---|---|---|---|
| Policy | `src/mts/publishing/archive.py` | Decide *what* to archive and *where* from listings and configuration | None |
| I/O | `src/mts/infrastructure/google_docs/google_docs_adapter.py` | List children, create the archive folder, re-parent files | Drive |
| Orchestration | `src/mts/publishing/archive.py` `run_archive(...)` | Sequence resolve → plan → apply → record | Via adapter |
| Entry: standalone | `scripts/archive_folder.py` | Argument parsing, credentials, human-readable output | Via orchestration |
| Entry: in-pipeline | publishing pipeline hook (§2.8) | Automatic invocation during a run | Via orchestration |

The policy layer takes **plain data** (a list of child metadata dicts, plus resolved configuration)
and returns a **plan**. It performs no Drive calls, so it is unit-testable without credentials and
callable from the pipeline without duplicating the script. `scripts/archive_folder.py` becomes a thin
adapter over `run_archive(...)`, holding no logic of its own — this is what allows the pipeline hook
in §2.8 to be added later without rewriting or re-testing the behavior.

Placing archiving in `src/mts/publishing/` rather than in the subject modules is deliberate: the
capability is subject-agnostic and worksheet-type-agnostic. Nothing in it may branch on `subject`.

### 2.3 Resolution Contract

Resolution turns a request into exactly one *effective folder* per target, before anything moves.

1. **Folder reference.** A request's folder is a preset name (`staging`, `publish`), a raw Drive
   folder ID, or a Drive folder URL. A URL is reduced to its ID; nothing else is inferred from it.
2. **Preset expansion.** A preset resolves to one or more `(label, folder_id, folder_type)` targets
   read from the canonical configuration keys in §2.1. `publish` expands to one target per configured
   grade; a `grades` restriction narrows that set. A requested grade with no configured destination is
   a fail-closed error, consistent with `design.md` §3.9 rule 3.
3. **Folder mode.** The effective folder is the resolved folder itself.
4. **Parent mode.** The effective folder is a child folder of the resolved folder, selected by the
   folder-date request:
   - `latest` (default): the most recently created non-archive child folder.
   - An ISO date: the child folder named by `final_delivery.week_folder_pattern` with `{{WEEK_OF}}`
     bound to that date's ISO Monday — reusing the delivery naming contract instead of inventing a
     second one.
   - A literal folder name: matched exactly.
   The configured archive folder is always excluded from this selection, so archiving twice can never
   descend into a previous archive.
5. **Parent-mode precondition.** If a parent-mode folder contains loose files, resolution **refuses**
   and reports, rather than guessing whether the user meant Folder mode. The requirement defines
   Parent mode only for the no-loose-files case, and silently picking a behavior there risks archiving
   the wrong set.
6. Resolution is reported before any mutation, in every mode.

### 2.3a Content-Filter Contract

Resolution decides *which folder*; this contract decides *which files inside it* — added so a folder
that mixes multiple grades, subjects, or weeks (`staging` in particular) can be archived selectively
instead of all-or-nothing.

1. With none of `grades`, `subject`, or `week` given, archiving stays **content-blind**: every loose
   file in the resolved folder is planned, exactly as it always has been (§2.4 rule 6 is the default,
   not merely a fallback).
2. `subject` and `week` always filter, in both Folder and Parent mode, because neither had any prior
   meaning for this utility. `subject` must equal the subject the command is running under; a mismatch
   is refused before anything is touched, not silently ignored. `week` resolves to an ISO Monday
   (`archive.resolve_week_of`, the same implementation `deliver.py` re-exports) and matches files whose
   name contains it.
3. `grades` filters file names using `naming.<kind>.prefix_by_grade` — **except** inside a `publish`
   (Parent-mode) target, where `grades` already selected which grade's delivery folder is the target.
   It is not re-applied as a file filter there: doing so would silently exclude a legitimately-named
   file that doesn't match the pattern exactly, changing the already-relied-upon behavior of archiving
   everything in a grade's own delivery folder. In Folder mode (`staging`) and for a raw folder ID,
   `grades` has no such prior meaning and filters normally.
4. A requested grade with no configured naming prefix is a fail-closed error, matching resolution's
   existing unconfigured-grade behavior.
5. Every file excluded by a filter is reported as `filtered_out` in that target's record, distinct from
   `moved`/`unmoved`, so a filtered dry run remains fully auditable — nothing disappears silently.

### 2.4 Archive Contract

1. Only **files** directly in the effective folder are archived. Sub-folders are never moved, never
   descended into, and never archived.
2. The archive destination is the child folder named `publishing.archive.archive_folder_name`
   (default `Archive`), resolved through the existing `ensure_child_folder` semantics: reuse when
   present, create when absent, refuse when ambiguous.
3. Files are **moved** (re-parented), not copied. The purpose is to leave the effective folder
   presenting only the next set; a copy would leave the previous set visible and defeat the utility.
4. Files already inside the archive folder are out of scope by definition — they are not direct
   children of the effective folder.
5. An effective folder with no direct files is a **successful no-op**, not an error. This is what
   makes repeat invocation and the future automatic hook safe.
6. Archiving is content-blind. It does not read, parse, or validate documents, and it does not filter
   by name, type, or run association: everything loose in the folder belongs to the previous set.
7. Archiving requires no gate and grants no approval. Archiving a folder never marks anything
   published, delivered, or approved.

### 2.5 Adapter Extensions

Extends the Google Docs/Drive Adapter Contract (`design.md` §3.6) with primitives only — each is a
single Drive concern with no policy:

8. `list_child_files(folder_id)` returns non-trashed, non-folder direct children with the metadata
   the policy layer needs (`id`, `name`, `mimeType`, `createdTime`, `webViewLink`).
9. `list_child_folders(folder_id)` returns non-trashed direct child folders ordered by `createdTime`
   descending, so parent-mode selection is a pure choice over that list rather than a query detail.
10. `move_file(file_id, destination_id)` re-parents a single file and confirms the destination is
    present in the resulting parents before reporting success, matching the post-condition checks
    already used by `publish_pair` and `deliver_pair`.

`ensure_child_folder` (contract item 5) is reused unchanged for the archive folder. No new folder
creation semantics are introduced.

### 2.6 Configuration Contract

Added to `data/config/project/base.yaml` under `publishing`, alongside `staging` and
`final_delivery`:

```yaml
publishing:
  archive:
    enabled: true
    archive_folder_name: "Archive"
    # Presets reference canonical destination keys; folder IDs are never duplicated here.
    targets:
      staging:
        folder_type: "folder"
        source: "publishing.staging.approved_folder_id"
      publish:
        folder_type: "parent"
        source: "publishing.final_delivery.destinations_by_grade"
        default_folder_date: "latest"
    # Automatic in-pipeline archiving; off by default until §2.8 is implemented and reviewed.
    auto_archive:
      before_render: false
      before_delivery: false
```

Rules:

1. `archive_folder_name` is configuration, not a literal, for the same reason
   `week_folder_pattern` is: audience-visible naming is a policy decision.
2. `targets.<name>.source` is a configuration path, so a preset can never drift from the destination
   that publishing and delivery actually use.
3. `auto_archive` flags default to `false`. The utility ships human-invoked; enabling automatic
   archiving is a separate, explicit decision (§2.8).
4. Subject configuration may not define its own archive targets. Subject-specific destinations are
   already expressed in `destinations_by_grade`, which the `publish` preset reads.

### 2.7 Command And CLI Surface

Slash command `commands/archive-folder.md`, following the structure of `commands/generate-worksheet.md`:
strict parameter names at the CLI boundary, a resolved-parameter echo before invocation, and refusal
of near-aliases rather than silent acceptance.

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `folder` | `staging`, `publish`, a Drive folder ID, or a Drive folder URL | required | Presets resolve through `publishing.archive.targets`. |
| `foldertype` | `folder`, `parent` | preset's `folder_type` | Required when `folder` is a raw ID or URL, since no preset supplies it. |
| `folderdate` | `latest`, an ISO date, or a literal folder name | `latest` | Parent mode only. Refused in Folder mode rather than ignored. |
| `grades` | `all` or a grade list | `all` | `publish` preset only; restricts the expanded target set. |
| `dry_run` | `yes`, `no` | `no` | `yes` resolves and plans without moving anything; `no` performs the moves and is the CLI's own default. |

CLI entry point:

```powershell
python scripts/archive_folder.py --folder staging --folder-type folder --dry-run
python scripts/archive_folder.py --folder publish --folder-type parent --folder-date latest
```

The operation is destructive-in-effect (artifacts change location): while the CLI itself now defaults
`dry_run` to `no`, the command layer must always resolve and present a `--dry-run` plan — the resolved
effective folder and the file list — before invoking `--apply`, and never proceeds from that dry run
to a real run without an explicit new instruction.

### 2.8 Pipeline Integration (Future)

The utility is designed now so that later automation is a configuration change plus two call sites,
not a redesign. Two intended hooks:

| Hook | Fires | Target | Rationale |
|---|---|---|---|
| `before_render` | Immediately before a run renders into the staging approved folder | `staging` preset, Folder mode | Staging presents only the run in progress |
| `before_delivery` | Immediately before Final Delivery re-uses an existing week folder | Resolved delivery week folder, Folder mode | A corrected re-delivery replaces rather than accumulates |

Constraints on any future hook:

1. It calls the same `run_archive(...)` orchestration as the CLI. No parallel implementation.
2. It runs only when its `auto_archive` flag is enabled, and never overrides an explicit run-scoped
   instruction.
3. It runs **after** the gate that authorizes the step it precedes, never before. Archiving must not
   disturb a folder whose approval is still pending.
4. It is non-fatal by policy decision recorded per hook: a failed archive must either block the step
   it precedes or be recorded and skipped, but must never partially archive silently.
5. `before_delivery` interacts with `final_delivery.reuse_existing_week_folder` (`design.md` §3.9
   rule 5): archiving preserves in-place correction of a week, since the previous copies move into
   the week folder's archive rather than being deleted or duplicated.

Until these hooks are implemented and reviewed, both flags remain `false` and archiving is
human-invoked only.

### 2.9 Evidence And Idempotence

1. Every invocation produces an **Archive Record**: the request, the resolved target(s), the
   effective folder, the archive folder (and whether it was created), and one entry per moved file
   with its ID, name, and link.
2. In-pipeline invocations write the record to the Run's evidence as `archived-artifacts.json`,
   consistent with the Delivery Record in `design.md` §3.9 rule 8. Standalone invocations print the
   record and may write it to a path given by the caller.
3. Archiving is idempotent in effect: a second invocation on an already-archived folder finds no
   direct files and records a no-op. Re-running is always safe.
4. Partial failure is recorded, not hidden. Files already moved stay moved, the record lists moved
   and unmoved files separately, and the invocation reports failure so the operator can re-run — which
   is safe because of rule 3.

### 2.10 Failure Modes

| Condition | Behavior |
|---|---|
| Preset unknown, or grade has no configured destination | Fail closed with the resolvable names listed |
| Raw folder ID/URL given without `foldertype` | Refuse; do not infer from folder contents |
| Parent mode, parent contains loose files | Refuse with the loose-file list; do not fall back to Folder mode |
| Parent mode, no eligible child folder | Refuse; do not create one |
| Requested folder date matches no child folder | Refuse with the available folder names |
| Multiple folders match the archive name | Refuse as ambiguous, per `ensure_child_folder` |
| Effective folder has no direct files | Success, recorded as a no-op |
| Drive permission or transient failure mid-run | Record moved/unmoved split, report failure, allow safe re-run |

## 3. Utility: Cleanup Folder

### 3.1 Requirement

Cleanup Folder is Archive Folder with a different terminal action: instead of moving the previous set
into `Archive`, it deletes files. It exists so a folder — or an accumulated `Archive` — can be emptied
without hand-clicking through Drive.

It is the destructive member of this document, so it carries three safeguards Archive does not:
disabled by default, an explicit scope choice, and a count confirmation (§3.5).

### 3.2 Shared Resolution

Cleanup **reuses** Archive's resolution contract (§2.3) unchanged: the same preset/ID/URL handling,
the same per-grade expansion, the same Folder and Parent modes, and the same latest/ISO-date/literal
child-folder selection. It resolves to exactly one effective folder per target, and Parent mode
refuses a parent holding loose files for the same reason.

This is a code requirement, not a documentation convenience. The resolution steps are extracted into a
shared function used by both `run_archive` and `run_cleanup`. Neither utility may carry its own copy,
because a divergence would mean the dry run a user reviewed for one utility no longer predicts the
other's target.

### 3.3 Scope Contract

Cleanup adds one parameter Archive has no need for, because "delete" has more than one sensible
object:

| `scope` | Deletes | Purpose |
|---|---|---|
| `files` (default) | Loose files directly in the effective folder | Exact mirror of Archive's target set |
| `archive` | Files directly inside the effective folder's `Archive` child | Purge accumulated archives |
| `both` | Both sets, reported as two groups | Empty a folder completely |

Rules:

1. `files` is the default so an omitted `scope` behaves like Archive, which is the least surprising
   reading of "clean up this folder".
2. `archive` and `both` resolve the archive folder by the configured `archive_folder_name`, reusing
   Archive's resolution and its ambiguity refusal. A missing `Archive` child contributes nothing and
   is not an error, so `scope=both` still works on a never-archived folder.
3. The record always reports which group each deleted file came from. A user approving a count must be
   able to see what it was made of.
4. Cleanup never descends past one level. It does not walk `Archive`'s sub-folders, and it does not
   walk the effective folder's other sub-folders.

### 3.4 Deletion Contract

1. Deletion means **trash**, not permanent removal: the file is marked `trashed`, stays recoverable
   from Drive Trash for the retention window, and can be restored without re-rendering.
   Permanent deletion (`files.delete`) is deliberately **not implemented**. Adding it would remove the
   only rollback this utility has.
2. Only **files** are trashed. Folders are never deleted — including the effective folder, its
   sub-folders, and the `Archive` folder itself, even when cleanup empties it. An empty folder is a
   valid end state.
3. An empty target set is a recorded success no-op, matching §2.4 rule 5.
4. Cleanup is content-blind for the same reason Archive is: everything in the resolved set belongs to
   the set being cleaned. It does not filter by name, type, or run association.
5. Cleanup requires no gate, grants no approval, and never touches Spec, run, or evidence content.

### 3.5 Confirmation Contract

A dry run alone is not sufficient authorization for deletion, because the folder can change between
the dry run and the apply. This has been observed in practice: staging contents changed twice within
minutes during Archive's validation.

1. An applying run must pass a confirmation count. The run proceeds only when the count equals the
   number of files actually planned at apply time.
2. A mismatch **refuses and deletes nothing**, reporting both counts. The correct response is a fresh
   dry run, not a larger number.
3. The confirmation is required in every applying run, including single-file ones. An exemption
   threshold would be a rule users learn to route around.
4. Dry runs never require a confirmation, so discovering the count is always free.

### 3.6 Adapter Extension

Extends the Google Docs/Drive Adapter Contract (`design.md` §3.6) with one further primitive,
continuing §2.5:

11. `trash_file(file_id)` marks one file trashed and confirms the resulting `trashed` state before
    reporting success. It never calls `files.delete`.

### 3.7 Configuration Contract

Added under `publishing`, deliberately mirroring `publishing.archive` so the two read side by side:

```yaml
publishing:
  cleanup:
    # Kill switch for the whole utility; shipped false, enabled 2026-09-03 after review.
    enabled: true
    default_scope: "files"
    require_confirmation: true
    # Presets reference the same canonical destination keys as publishing.archive.targets.
    targets:
      staging:
        folder_type: "folder"
        source: "publishing.staging.approved_folder_id"
      publish:
        folder_type: "parent"
        source: "publishing.final_delivery.destinations_by_grade"
        default_folder_date: "latest"
```

Rules:

1. `enabled` is the utility's kill switch, and it is the only one: setting it `false` stops cleanup
   without touching code. It shipped `false` and was enabled deliberately after review, so turning the
   utility on is a recorded configuration decision rather than an implementation side effect.
2. `require_confirmation` has no opt-out parameter. Turning confirmation off is a configuration
   decision with an audit trail, never a per-invocation flag.
3. The archive folder name is read from `publishing.archive.archive_folder_name`. Cleanup does not
   define a second one, or the two utilities could disagree about which folder is the archive.

### 3.8 Command And CLI Surface

Slash command `commands/cleanup-folder.md`, structurally identical to `commands/archive-folder.md`.

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `folder` | `staging`, `publish`, a Drive folder ID, or a Drive folder URL | required | Same presets as archive. |
| `foldertype` | `folder`, `parent` | preset's `folder_type` | Required for a raw ID or URL. |
| `folderdate` | `latest`, an ISO date, or a literal folder name | `latest` | Parent mode only. |
| `grades` | `all`, or a grade list | `all` | `publish` preset only. |
| `scope` | `files`, `archive`, `both` | `files` | See §3.3. |
| `dry_run` | `yes`, `no` | `yes` | Applying additionally requires the confirmation count (§3.5). |

CLI entry point:

```powershell
python scripts/cleanup_folder.py --folder staging --folder-type folder --dry-run
python scripts/cleanup_folder.py --folder staging --folder-type folder --scope archive --apply --confirm 12
```

The command layer must present the dry-run plan and stop. It may not choose the confirmation count on
the user's behalf from its own dry run; the count is the user's acknowledgement of a specific plan.

### 3.9 Evidence And Failure Modes

Cleanup emits a Cleanup Record with the same shape as the Archive Record (§2.9), reporting `deleted`
and `undeleted` per target and per scope group. In-pipeline invocations would write
`cleaned-artifacts.json`; there is no pipeline hook today and none is proposed.

| Condition | Behavior |
|---|---|
| `publishing.cleanup.enabled` is false | Refuse; nothing is listed or deleted |
| Confirmation count missing on an applying run | Refuse; report the planned count |
| Confirmation count does not match the plan | Refuse, delete nothing, report both counts |
| `scope=archive` with no `Archive` child | Success, recorded as a no-op |
| Effective folder resolves but holds no files in scope | Success, recorded as a no-op |
| Trash fails mid-run | Record deleted/undeleted split, report failure, allow safe re-run |
| Any resolution failure | Identical to §2.10, since resolution is shared |

Rollback: restore the files from Drive Trash. This is the whole reason §3.4 rule 1 forbids permanent
deletion.

## 4. Utility: Deliver Worksheets

### 4.1 Requirement

Run Final Delivery on demand, outside a generate run: take the approved worksheet/answer-key pairs
sitting in staging and copy them into `Week_<WEEK_OF>` under each grade's audience-facing folder.

This introduces no new distribution semantics. `design.md` §3.9 remains the authoritative Staging And
Final Delivery Contract, and every rule there applies unchanged. This section covers only what a
standalone, folder-anchored entry point adds.

### 4.2 Relationship To The Workflow

The generate-worksheet workflow already delivers, by shelling out to `deliver_weekly_worksheets.py`
with a run root. That path is run-anchored: it reads exact document IDs recorded at publish time.

The utility is folder-anchored: its default source is the staging folder itself. Both paths resolve
the week, the week folder name, and the per-grade destinations through the **same** functions in
`src/mts/publishing/deliver.py`. A second copy of that logic would let the workflow and the utility
disagree about where a week's worksheets belong, which is exactly the failure this consolidation
prevents.

### 4.3 Pairing Contract

Delivery must know, per grade, which document is the student worksheet and which is the answer key.
That mapping has two possible sources, and the more exact one wins:

| Source | Used when | Basis |
|---|---|---|
| Run root | a run root is supplied | `published-artifacts.json` states grade, role, and document ID as recorded facts |
| Staging names | otherwise | document names matched against the configured naming pattern |

Rules:

1. A run root is preferred whenever available, because it requires no inference and is unaffected by
   whatever else happens to be sitting in staging.
2. Name matching **never guesses**. Two documents matching one expected name is `ambiguous_name`; a
   worksheet without its answer key is `incomplete_pair`. In both cases the grade is skipped and the
   issue is reported. Delivering the wrong document to an audience is worse than delivering nothing.
3. Files matching no expected name — manual `Copy of …` duplicates, other subjects' artifacts, stray
   uploads — are reported as `unmatched_files` and never delivered.
4. The resolved week is part of the expected name, so documents from another week cannot be delivered
   into this week's folder by accident.
5. A grade with no deliverable pair is skipped and recorded, so a partially staged week still delivers
   every grade that is ready; waiting for a late grade would withhold worksheets that are already
   approved. `on_missing: fail` is available for runs that must be all-or-nothing.
6. `grades` and `week` are the two filters already inherent to pairing (§4.3 rules 2 and 4). `subject`
   is a further guard: it must equal the subject the effective configuration was loaded for, and a
   mismatch is refused (`check_subject_matches`, shared with `/archive-folder` and
   `/format-and-deliver-worksheets` so all three utilities agree on what counts as a mismatch) before
   any pairing or delivery happens.

### 4.4 Naming Contract

Name-based pairing is only sound if the names were produced by the same definition it reads. The
grade-to-document-name mapping is therefore subject configuration, not a constant inside a script:

```yaml
naming:
  weekly:
    document_name_pattern: "{{PREFIX}}-{{WEEK_OF}}"
    answer_key_suffix: "_KEY"
    prefix_by_grade:
      grade_6: "MTS-Math-6thGrade-WeeklyWorksheet"
```

Rendering writes these names and delivery reads them back, so both must resolve the same
configuration.

`final_delivery.destinations_by_grade` is project-scoped (ADR-0002): a destination is a grade's
audience folder, shared by every subject, so the destination list is broader than any single subject's
output. A destination grade with no `prefix_by_grade` entry for the subject in hand is therefore
**skipped and reported** as `no_naming_for_subject` under `grades=all`, and **refused** when named
explicitly — ELA produces no 9/10, and that must not fail an otherwise complete ELA delivery, while
naming the grade directly stays fail-closed. `restrict_to_named_grades` is the single implementation;
`print_jobs` calls it rather than repeating it.

`file_extension` is optional and empty by default. A subject staged as files rather than Docs sets it
so the answer-key suffix lands before the extension (`…-2026-09-07-KEY.pdf`).

### 4.5 Delivery Contract
Inherited unchanged from `design.md` §3.9: one `Week_<WEEK_OF>` folder per grade destination, reused
rather than duplicated; `mode: copy` by default so staging survives as the audit trail;
`deliver_answer_key` controls whether the key accompanies the worksheet; content is never modified.

Added by the utility:

1. Per-grade failure isolation. One grade's failure — a rate limit, a permission error — is recorded
   against that grade and does not prevent the remaining grades from being delivered.
2. A dry run resolves the week, pairs every grade, and reports all issues **without** creating a week
   folder or copying anything.

### 4.6 Command And CLI Surface

Slash command `commands/deliver-worksheets.md`, structurally identical to the other utilities:
dry-run first, present the plan and the issues, stop, and apply only on an explicit new instruction.

| Parameter | Values | Default |
|---|---|---|
| `week` | `current`, a week number, or an ISO date | `current` |
| `grades` | `all`, or a grade list | `all` |
| `run` | a run root | none (staging names) |
| `source_folder` | a Drive folder ID | `publishing.staging.approved_folder_id` |
| `mode` | `copy`, `move` | `final_delivery.mode` |
| `subject` | a configured subject id | the subject in use |
| `on_missing` | `skip`, `fail` | `skip` |
| `dry_run` | `yes`, `no` | `yes` |

## 5. Utility: Format-And-Deliver Worksheets

### 5.1 Requirement

Take every loose file in staging, bring each up to pipeline standard, and deliver it — in one step,
rather than requiring an operator to notice and separately repair a document that was never rendered
through the pipeline.

This utility exists because "format the way the workflow formats" turned out not to be a text
operation. A rendered document's format is a function of **Spec + template**; a document authored
directly into Drive has no Spec, so half that function's input is missing. The utility's real job is
detecting that gap and closing it — reconstruction, not text repair.

### 5.2 Provenance Contract

Extends the Google Docs/Drive Adapter Contract (`design.md` §3.6) and §2.5/§3.6 of this document with
one further primitive:

12. `stamp_document(file_id, properties)` records provenance as Drive `appProperties` and confirms it
    was written before reporting success. Properties stay short identifiers (`mts_run_id`,
    `mts_spec_rev`, `mts_grade_id`, `mts_week_of`, `mts_wtype`, `mts_artifact_kind`) because Drive caps
    each key+value pair at 124 bytes; a full path is rejected locally rather than failing as an opaque
    403 from Drive.

Every document the pipeline renders is stamped. `publishing.provenance.enabled` gates whether stamping
and reporting happen at all; `require_stamp_for_delivery` gates whether an unstamped document blocks
delivery of its grade or is merely reported. Both default to report-only (`enabled: true`,
`require_stamp_for_delivery: false`) because existing staged documents predate stamping — turning on
enforcement before every in-flight artifact is rendered through the pipeline would block legitimate
delivery.

A stamp naming a different grade or week than the document's own filename is reported as
`provenance_mismatch`, distinct from `no_provenance`. A run root needs no stamp: the run record itself
is the provenance, which is exactly why §4.3 rule 1 prefers it.

### 5.3 Display Numbering Contract

The Weekly Worksheet template's placeholder scheme is `<DAY>_<Q|A><LOCAL_NUMBER>` — per-day slots
restarting at 1, not the Spec's continuous global numbering. `data/config/worksheet_types/weekly_worksheet.yaml`
declares `display_numbering: "local"` so students see 1..10 each day; the Spec keeps global numbers
for storage, ordering, and verification. This is a rendering and QA concern, not unique to this
utility, and applies pipeline-wide:

1. `render_weekly_specs_to_drive.py` renders local numbers into both the worksheet and the answer key
   from the same per-day position, so the two always agree.
2. `p0_runtime.targeted_text_qa_v2(..., numbering="local")` checks each local number appears once per
   section that reaches it, replacing the prior global-numbering assumption that produced false
   failures on Weekly renders (the gap recorded in `design.md` §3.6). `numbering="global"` remains
   available for worksheet types that are actually numbered continuously.
3. A reconstructed Spec (§5.5) round-trips through the same local numbering it was parsed from —
   local-in, global-in-Spec, local-out — so re-rendering never silently renumbers a document a
   student has already seen.

### 5.4 Classification Contract

Every staged pair is either:

| Label | Meaning | Action |
|---|---|---|
| `conformant` | Carries provenance naming its own grade and week | Delivered as-is; never re-rendered |
| `orphan` | No provenance, or provenance naming a different grade/week | Reconstructed and re-rendered (§5.5) before delivery |

Classification reuses `deliver.unstamped_documents` (§5.2) unchanged — the same check delivery itself
uses to report `missing_provenance` — so classification and the delivery gate can never disagree about
which documents are trustworthy.

### 5.5 Reconstruction Contract

`src/mts/publishing/reconstruct.py` builds a Spec from an orphan pair's rendered text. Parsing is
inference, so every ambiguity fails closed rather than being resolved:

1. Numbered lines are grouped under the day heading that precedes them; a numbered line before any
   heading, or a document with no headings at all, refuses.
2. Local numbering within a day must be contiguous `1..n`; a gap refuses.
3. The worksheet's sections must match the key's sections exactly, and each section's question count
   must equal its answer count; any mismatch refuses, naming the section and both counts.
4. Answers are carried over from the key, not recomputed. Numeric text is coerced to `int`/`float` so
   downstream `display_answer` rounding behaves as it does for authored Specs; non-numeric answers
   pass through unchanged.
5. **Verification is not recomputed.** The reconstructed Spec's `verification.status` is `PASS` so
   `render_pair` still functions, but `method: "inherited_from_source_document"`, `recomputed: false`,
   and `source_documents` are recorded on the Spec and on every question, so an inherited answer can
   never be mistaken for one independently verified per `design.md`'s verification contract. This is a
   deliberate, explicit exception to `recompute_every_answer`, scoped to recovering pre-existing
   documents that predate the provenance requirement — it is not a precedent for skipping verification
   on newly authored content.
6. The reconstructed Spec is persisted under the grade's transaction tree like any other Spec revision,
   so it stops being an orphan: a future run can read, audit, or correct it.

### 5.6 Composition Contract

`src/mts/publishing/format_deliver.py` defines no delivery, naming, numbering, or reconstruction rule
of its own — it sequences existing contracts:

1. Pair staging by name (`deliver.pair_from_staging`, §4.3).
2. Classify each pair (§5.4).
3. For each `orphan`: reconstruct (§5.5) → persist the Spec → re-render from the registered template,
   stamping the result (§5.2). The **re-rendered** documents are delivered, never the orphan
   originals; the record names which documents a rebuild replaced.
4. Deliver every resolved pair through `deliver.run_deliver` with the pairs supplied explicitly, so
   week resolution, destination lookup, and the copy/move step are identical to §4's contract.

Failure isolation: one grade's reconstruction or render failure is recorded against that grade with
its error and does not block the others. A dry run classifies and reports without reconstructing,
persisting, or delivering anything; a grade awaiting rebuild is reported `pending_rebuild`, distinct
from `missing pair`, because the pair does not exist yet by design, not because nothing was found.

### 5.7 Authoring Contract

The root cause this utility exists to recover from: content authored directly into a Drive document,
bypassing Spec persistence and rendering entirely. This is now prohibited, not merely worked around:

1. Every document the pipeline produces must come from a persisted Spec revision, be named from
   `naming.<worksheet_kind>` configuration (§4.4), and be stamped with provenance (§5.2).
2. Authoring prompt or answer text straight into a Drive document is refused as a practice, not just
   detected after the fact — stated directly in the Weekly execution runbook and in
   `commands/generate-worksheet.md`.
3. Format-and-deliver remains available as recovery for documents that predate this rule. It is not a
   sanctioned second authoring path.

### 5.8 Command And CLI Surface

Slash command `commands/format-and-deliver-worksheets.md`, structurally identical to the other
utilities: dry run first, present the classification and every action, stop, and apply only on an
explicit new instruction.

| Parameter | Values | Default |
|---|---|---|
| `week` | `current`, a week number, or an ISO date | `current` |
| `grades` | `all`, or a grade list | `all` |
| `subject` | a configured subject id | the subject in use |
| `source_folder` | a Drive folder ID | `publishing.staging.approved_folder_id` |
| `batch_id` | a batch identifier for reconstructed Specs | `reconstructed_<week_of>` |
| `dry_run` | `yes`, `no` | `yes` |

`week`, `grades`, and `subject` are the same request fields `deliver.run_deliver` already resolves
(\u00a74.3, \u00a74.6); format-and-deliver passes them straight through rather than re-filtering staging pairs
itself, and the same `check_subject_matches` guard applies before anything is classified.

CLI entry point:

```powershell
python scripts/format_and_deliver.py --week 2026-09-07 --grades grade_4 --dry-run
python scripts/format_and_deliver.py --week 2026-09-07 --grades grade_4 --apply
```

## 6. Utility: Print Worksheets

### 6.1 Requirement

Produce the physical class set. Given an instructional week, export each grade's approved worksheet
and answer key to PDF and spool them to a local printer at that grade's class count. It is a
distribution step: it never renders, edits, re-numbers, re-verifies, moves, or deletes anything, and
the documents it reads stay exactly where they were.

### 6.2 Shared Resolution And Pairing

Printing defines no folder resolution and no pairing of its own:

- Targets come from `archive.resolve_targets` with the same `staging` and `publish` presets
  (§2.3), and the effective folder from the shared `archive.resolve_effective_folder`.
- In `publish` (parent) mode the folder date is the **requested week**, never `latest`, so printing a
  past week cannot silently pull the newest folder.
- Grade/role pairing is `deliver.pair_from_staging` (§4.3). `ambiguous_name`, `incomplete_pair`, and
  `unmatched_files` are reported and skipped, never resolved. Printing the wrong grade's key wastes
  paper and, worse, hands a class the answers.

### 6.3 Copy Count Contract

The one decision this utility owns is how many copies of each document to print.

- `publishing.printing.copies_by_grade` is subject-scoped, because class sizes are a property of the
  subject's grade cohorts, not of the project.
- A grade absent from `copies_by_grade` is **skipped and reported** under `grades=all`, and **refused**
  when named explicitly. A new grade therefore never prints an unreviewed count.
- `copies` accepts per-grade run overrides (`grade_5=6`, or `grade_5=6:2` to also override the key).
  An override applies to that run only and is never persisted.
- A count of `0` prints nothing for that role; it is a valid way to suppress a key.

### 6.4 Print Contract

1. Each document is exported once through `adapter.export_pdf` and handed to the printer backend with
   its copy count; copies are a printer instruction, not repeated exports.
2. Backends are external PDF viewers driven by a fixed argument list, never a shell string. SumatraPDF
   prints silently with exact copy and duplex control; Acrobat is the no-install fallback and prints
   one copy per invocation at the printer's default duplex.
3. Applying requires `--confirm <total copies>` matching the plan **at apply time**, the same guard as
   cleanup (§3.5). A dry run is not authorization: paper cannot be un-printed.
4. A failure mid-target records what already printed and what did not, so a re-run can be scoped by
   hand rather than reprinting the whole set.

### 6.5 Configuration Contract

`publishing.printing` in `base.yaml`: `enabled`, `printer_name`, `backend`, `backends.<name>.executable`,
`duplex`, `default_source`, `require_confirmation`, `spool_dir`. `enabled: false` is the kill switch.
The subject file contributes `publishing.printing.copies_by_grade` only.

### 6.6 Subject Neutrality

Printing resolves configuration through `resolve_distribution_config` — `base.yaml` merged with the
subject file, with **no** worksheet-type compatibility check and **no** template-registry lookup. Both
of those gate *authoring*: a subject whose templates and verification rules await approval must stay
unable to generate worksheets, but that is no reason it cannot print artifacts it already has. Any
utility that renders must keep using `resolve_effective_config`.

Two staging shapes follow from this, and the adapter handles both in `export_pdf`: a Google Doc is
exported to PDF, a file already stored as `application/pdf` is downloaded unchanged, and any other
type fails closed rather than being silently converted. Where a subject stages files rather than Docs,
`naming.weekly.file_extension` places the answer-key suffix before the extension so name pairing still
works. Math omits the field and its names are unaffected.

### 6.7 Command And CLI Surface

| Parameter | Values | Default |
|---|---|---|
| `week` | `current`, a week number, or an ISO date | `current` |
| `grades` | `all`, or a grade list | `all` |
| `source` | `staging`, `publish` | `publishing.printing.default_source` |
| `include` | `both`, `worksheet`, `key` | `both` |
| `copies` | per-grade overrides | configured counts |
| `printer` | a Windows printer name | `publishing.printing.printer_name` |
| `subject` | a configured subject id | the subject in use |
| `dry_run` | `yes`, `no` | `yes` |

CLI entry point:

```powershell
python scripts/print_worksheets.py --week current --dry-run
python scripts/print_worksheets.py --week current --apply --confirm 20
python scripts/print_worksheets.py --subject ela --week 2026-09-07 --dry-run
```

## 7. Test Design

Extends `design.md` §8. All behavior tests use the existing fake-Drive pattern in
`tests/integration/test_google_docs_adapter.py`; no test performs live Drive I/O.

1. **Policy unit tests** (`src/mts/publishing/archive.py`, no adapter): plan from a listing with mixed
   files and folders; empty-folder no-op; sub-folders excluded; archive folder excluded from
   parent-mode selection; latest-child selection ordering; date-to-week-folder-name resolution;
   preset expansion including grade restriction and unconfigured-grade refusal.
2. **Adapter tests**: `list_child_files` / `list_child_folders` filtering and ordering; `move_file`
   post-condition check; archive-folder reuse vs. creation vs. ambiguity.
3. **Orchestration tests**: dry run mutates nothing and still emits a complete record; real run emits
   a record matching the applied moves; parent-mode loose-file refusal; partial-failure record shape.
4. **Contract test**: `scripts/archive_folder.py` contains no decision logic — every behavior assertion
   above passes against `run_archive(...)` directly, which is the guard that keeps the future pipeline
   hook honest. The same assertion applies to `scripts/cleanup_folder.py` and `run_cleanup(...)`.
5. **Cleanup tests**: each `scope` value's target set; `scope=archive` with no archive folder as a
   no-op; folders never trashed, including an emptied `Archive`; confirmation missing, mismatched, and
   matching; disabled-by-default refusal; partial-failure deleted/undeleted split.
6. **Shared-resolution test**: archive and cleanup resolve the identical effective folder for the same
   request, which is what §3.2 requires and what prevents the two dry runs from diverging.
7. **Deliver Worksheets tests**: week resolution (`current`/number/date); destination resolution and
   unconfigured-grade refusal; document-name derivation from `naming` configuration; staging pairing
   including `ambiguous_name`, `incomplete_pair`, `unmatched_files`, and a different week matching
   nothing; run-root pairing bypassing name matching entirely; one grade's delivery failure not
   blocking the others; `on_missing=skip` (default) delivering every ready grade versus
   `on_missing=fail` blocking the run; the CLI holds no decision logic.
8. **Provenance tests**: `stamp_document` records and returns properties; an oversized property is
   refused locally before reaching Drive; `unstamped_documents` reports both `no_provenance` and
   `provenance_mismatch`; a run root needs no stamp; `require_stamp_for_delivery` blocking versus
   report-only.
9. **Local numbering tests**: per-day numbers restart correctly in the worksheet; the answer key uses
   the identical local numbers as the worksheet; `numbering="global"` remains available and unchanged;
   QA accepts local numbering that global-mode QA would reject, and still fails a genuinely missing
   day.
10. **Reconstruction tests**: a pair reconstructs into globally-numbered sections; prompts and answers
    pair in document order; numeric coercion and text-answer preservation; verification is recorded as
    inherited, never as recomputed; a missing answer, a section present in only one document,
    non-contiguous numbering, and a numbered line before any heading all fail closed; a reconstructed
    Spec round-trips back through rendering to the same local numbering it was parsed from.
11. **Format-and-deliver composition tests**: a stamped pair is classified `conformant` and delivered
    unmodified; an unstamped pair is reconstructed, re-rendered, and the **re-rendered** documents (not
    the originals) are what gets delivered; a dry run reconstructs, renders, and delivers nothing; a
    failed rebuild is recorded and does not block other grades; a grade awaiting rebuild is reported
    `pending_rebuild`, not `missing pair`, since the dry run never claims a pair exists before it does.
12. **Print Worksheets tests**: a dry run plans the configured class counts and spools nothing; an
    apply exports each document once and passes its copy count through; a mismatched confirmation
    prints nothing anywhere; `include=key`; a `copies` override replacing only the named counts; a
    grade without configured counts skipped under `all` and refused when named; a missing pair reported
    while the ready grade still prints; `source=publish` selecting the requested week folder rather than
    the newest; a printer failure splitting printed from unprinted; `enabled: false` as a hard stop;
    copy-override syntax validation; and the CLI holding no decision logic.
13. **Subject-neutral distribution tests**: `resolve_distribution_config` serves a subject that
    `resolve_effective_config` still refuses to author for, and carries no template selection; an
    unknown subject is rejected; `export_pdf` exports a Google Doc, downloads a stored PDF, and refuses
    any other type; a subject staged as PDFs pairs and prints on names carrying a file extension.

## 8. Implementation Sequence

1. Adapter primitives (§2.5) with their tests.
2. `publishing.archive` configuration block (§2.6).
3. `src/mts/publishing/archive.py`: policy functions, then `run_archive(...)` orchestration, with
   tests (§3.1, §3.3).
4. `scripts/archive_folder.py` as a thin CLI over `run_archive(...)`.
5. `commands/archive-folder.md` slash command, registered alongside the existing commands.
6. Validate with `--dry-run` against both reference targets in §2.1, review the resolved plan, then
   execute a real run.
7. Pipeline hooks (§2.8) deferred; `auto_archive` stays `false` until separately designed and
   approved.

Cleanup Folder, after Archive Folder is validated:

8. Extract Archive's resolution steps into a shared function; re-run the full suite to prove archive
   behavior is unchanged before anything new is added.
9. `trash_file` adapter primitive (§3.6) with its tests.
10. `publishing.cleanup` configuration block (§3.7), shipped `enabled: false`.
11. `src/mts/publishing/cleanup.py`: scope resolution, `run_cleanup(...)`, and the confirmation guard,
    with tests (§4.5, §4.6).
12. `scripts/cleanup_folder.py` as a thin CLI, then `commands/cleanup-folder.md` and its prompt entry
    point.
13. Validate against a disposable folder first — never staging or a delivery folder — covering each
    scope, the confirmation mismatch, and Drive Trash restoration.

Deliver Worksheets:

14. `src/mts/publishing/deliver.py`: week resolution, destination resolution, naming-based document
    names, run-root and staging pairing, `run_deliver(...)`, with tests (§6.7).
15. `scripts/deliver_folder.py`, `commands/deliver-worksheets.md`, prompt entry point, README row.
16. Promote the grade→document-name mapping from a private constant in
    `render_weekly_specs_to_drive.py` into subject `naming` configuration, so rendering and delivery
    read the same definition.
17. Validate `--dry-run` against the approved staging folder for a real week, review the resolved
    pairing and any issues, then apply.

Format-And-Deliver Worksheets, after Deliver Worksheets is validated:

18. `stamp_document` adapter primitive (§5.2) with its byte-limit test; `publishing.provenance`
    configuration, shipped report-only; wire stamping into the render path.
19. `display_numbering: "local"` on the Weekly Worksheet type (§5.3); per-day-aware rendering in
    `render_weekly_specs_to_drive.py`; `numbering`-aware `targeted_text_qa_v2`; thread the setting
    through `validate_subject_output` and the generate pipeline's QA projection.
20. `src/mts/publishing/reconstruct.py`: `reconstruct_spec(...)` with its fail-closed tests (§6.10).
21. `src/mts/publishing/format_deliver.py`: `classify_pairs(...)` and `run_format_and_deliver(...)`,
    composing §5.2–§5.5 and `deliver.run_deliver` with explicit pairs, with tests (§6.11).
22. State the authoring contract (§5.7) in the Weekly execution runbook and
    `commands/generate-worksheet.md`: no document without a persisted, named, stamped Spec.
23. `scripts/format_and_deliver.py`, `commands/format-and-deliver-worksheets.md`, prompt entry point,
    README row.
24. Validate against a real orphan pair: dry run shows the correct classification, apply reconstructs
    and delivers exactly that grade, and a stamped pair already in staging is confirmed `conformant`
    and left unmodified.
