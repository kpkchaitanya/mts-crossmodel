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
4. [Test Design](#4-test-design)
5. [Implementation Sequence](#5-implementation-sequence)

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
| `dry_run` | `yes`, `no` | `yes` | Resolves and plans without moving anything. |

CLI entry point:

```powershell
python scripts/archive_folder.py --folder staging --folder-type folder --dry-run
python scripts/archive_folder.py --folder publish --folder-type parent --folder-date latest
```

Because the operation is destructive-in-effect (artifacts change location), `dry_run` defaults to
`yes`, and the command must present the resolved effective folder and the file list for confirmation
before a real run. The command layer never proceeds from a dry run to a real run without an explicit
new instruction.

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

## 4. Test Design

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

## 5. Implementation Sequence

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
