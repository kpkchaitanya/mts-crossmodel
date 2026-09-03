# MTS Worksheet and Assessment Generation - Implementation Plan and Task Tracker

Status: Active
Last updated: 2026-09-03

## 1. Delivery Strategy

Implement one bounded module at a time. Every module must have a focused validation before another module is changed. Integrate modules only at the checkpoints defined below, then run the existing Math regression gate.

```mermaid
flowchart LR
    D[Data Foundation] --> P[Effective Config Resolver]
    P --> R[Run Loader/Writer]
    R --> G[Gate Controller]
    G --> I1[Shared Runtime Integration]
    I1 --> M[Math Module Adapter]
    M --> A[Google Docs and Drive Adapters]
    A --> I2[Class Worksheet Integration]
    I2 --> WW[Weekly Math Workflow]
    WW --> WI[Weekly Staging Integration]
    WI --> W[Worksheet Type Activation]
    W --> F[Folder Structure Refactor]
    F --> B[Math Bypass Sample Run]
    B --> E[ELA Extension]
    E --> S[SAT and ACT Extensions]
```

## 2. Overall Status

| Phase | Scope | Status | Evidence / Exit Condition |
|---|---|---|---|
| M1 | Product idea and ontology | Complete | Product scope includes Math, ELA, and extensible Worksheet Types. |
| M2 | Functional/NFR requirements and acceptance criteria | Complete | Requirement hierarchy and NFR-to-fitness-function coverage reviewed. |
| M3 | Architecture | Complete | C1/C2, C3 boundary decisions, information architecture, responsibility and fitness-function design reviewed. |
| M4 | Detailed system design | Complete | State machine, C3/C4 mapping, ERD, data classes, contracts, and test design reviewed. |
| M5.0 | Data Foundation | Complete | Worksheet Type data, Math master-data indexes, transaction-evidence schemas, and Math regression gate pass. |
| M5.1 | Effective Config Resolver | Complete | Focused tests validate active Class resolution, override precedence, immutability, and draft/unknown/incompatible rejection. |
| M5.2 | Run Loader/Writer | Complete | Focused tests validate new manifest/effective config persistence, compatible resume/checkpointing, and mismatched request/effective config rejection. |
| M5.3 | Gate Controller | Complete | Focused tests validate revision-scoped approvals, fail-closed rejection, and dependent invalidation. |
| M5.4 | Shared Runtime Integration | Complete | Shared Math Class fixture passes effective config, Run, Scope Review, and scope invalidation; Math migration gate remains green. |
| M5.5 | Math Subject Module Adapter | Complete | Adapter delegates existing P0 curriculum, verification, template/QA behavior while preserving candidate Spec generation as AI-owned. |
| M5.6 | Google Docs/Drive Adapters | Complete | Mocked tests validate master copying, rendering, inspection, paired publication, and fail-closed behavior. |
| M5.7 | Math Class End-to-End Integration | Complete | Staging-only Class Worksheet lifecycle reaches Publish Approval readiness without live publication. |
| M5.7a | Weekly Math Workflow Orchestrator | Complete | Resolves six Math scopes into five Gate 1 Weekly Worksheet plans, including the combined Grades 9/10 split. |
| M5.7b | Weekly Math Staging Integration | Complete | All five Weekly plans pass synthetic candidate-Spec, verification, rendering, QA, and Publish Approval readiness tests in staging. |
| M5.8 | Worksheet Type Activation | In progress | Class and Weekly are configuration-active and staging-ready; remaining Math types require one-at-a-time migration. |
| M5.11 | Folder Structure Refactor | Complete | Target `src/mts`, `tests`, and `data` structure passes validation; legacy mixed roots retired to `archive/legacy-layout` or `data/transactions/legacy_runs`. |
| M5.12 | Math Weekly Bypass Sample Run | Complete through seamless CLI staging render | Math Weekly sample run for week `2026-09-07` generated target transaction evidence with all gates explicitly bypassed, verification/QA retained, and five worksheet/key pairs rendered to Google Docs staging through `scripts/generate_worksheet.py`. |
| M5.9 | ELA Extension | Blocked | Approved ELA extension package, tests, templates, and verification rules required. |
| M5.10 | SAT/ACT Extensions | Blocked | Approved per-type requirements, scoring, fixtures, templates, and tests required. |

## 3. Module-by-Module Tasks

### M5.0 Data Foundation - Complete

- [x] Create `schemas/worksheet-type.schema.json`.
- [x] Create active Math Class Worksheet configuration.
- [x] Create draft Weekly Worksheet configuration with explicit activation blockers.
- [x] Create Math grade/course and master-data indexes that reference P0 knowledge assets.
- [x] Create shared template registry by Worksheet Type.
- [x] Create approval, verification-result, render-artifact, and publication-record schemas.
- [x] Extend repository reconciliation checks for Data Foundation assets.
- [x] Validate new data files parse and referenced paths resolve.
- [x] Run `python tests/math/validate_migration.py`: 3/3 suites and 14 checks pass.

### M5.1 Effective Config Resolver - Complete

Entry condition: M5.0 complete.

- [x] Create `src/runtime/policy.py` as the legacy implementation, superseded by target `src/mts/setup_project/configure.py` and `src/mts/infrastructure/configuration/config_resolver.py`.
- [x] Load base, subject, and Worksheet Type YAML configuration.
- [x] Resolve approved current-run overrides into an immutable effective config snapshot.
- [x] Reject unknown subjects, unknown Worksheet Types, incompatible subject/type combinations, and invalid overrides.
- [x] Reject `draft` and `disabled` Worksheet Types for production execution.
- [x] Add focused unit tests for precedence and failure paths.

Focused validation:

```text
Class Worksheet + Math resolves to an active immutable effective config snapshot.
Weekly Worksheet resolves to an active Math effective config; production readiness is verified separately by M5.7a/b.
```

Integration checkpoint: none. Do not modify Run persistence or gates in this slice.

### M5.2 Run Loader/Writer - Complete

Entry condition: M5.1 passes focused tests.

- [x] Create `src/runtime/run_repository.py` as the legacy implementation, superseded by target `src/mts/workflow_management/run_loader.py` and `src/mts/workflow_management/run_writer.py`.
- [x] Create legacy `runs/<subject>/<run_id>/run-manifest.json` and resolved config snapshot paths; target migration writes `data/transactions/runs/<run_id>/run_manifest.json` and `effective_config.json`.
- [x] Persist new Run checkpoints using IDs/revisions instead of copying Worksheet Spec questions/answers.
- [x] Resume only when request identity and upstream revisions remain compatible.
- [x] Add focused new/resume/incompatible-resume tests.

Focused validation:

```text
A new Math Class Worksheet Run creates its manifest and effective config snapshot.
A compatible request resumes its latest valid checkpoint.
A changed effective config or scope revision rejects the prior checkpoint.
```

Integration checkpoint: Effective Config Resolver + Run Loader/Writer.

### M5.3 Gate Controller - Complete

Entry condition: M5.2 passes focused tests.

- [x] Create `src/runtime/gates.py`.
- [x] Implement revision-scoped approvals for Scope Review, Question Review, Verification Review, Formatting Review, and Publish Approval.
- [x] Reject absent, rejected, or stale approvals.
- [x] Apply the Section 2 invalidation contract from M4 design.
- [x] Add focused transition, rejection, and invalidation tests.

Focused validation:

```text
A valid approval permits only its matching transition and artifact revision.
Changing a Question invalidates verification and downstream approval/evidence.
```

Integration checkpoint: Effective Config Resolver + Run Loader/Writer + Gate Controller.

### M5.4 Shared Runtime Integration - Complete

Entry condition: M5.1 through M5.3 pass focused tests.

- [x] Create shared integration fixtures for an active Math Class Worksheet request.
- [x] Verify effective config, manifest checkpoint, gate decision, and invalidation evidence work together.
- [x] Run the existing Math migration gate.

Focused validation:

```text
python tests/math/validate_migration.py
```

Exit condition: Shared runtime tests pass and Math migration gate remains green.

### M5.5 Math Subject Module Adapter - Complete

Entry condition: M5.4 complete.

- [x] Define Math subject module adapter around existing P0 runtime behavior, now available through `src/mts/subjects/math/p0_runtime.py`.
- [x] Preserve current curriculum cache, deterministic verifier, template revision guard, targeted QA, and telemetry behavior.
- [x] Add adapter-level fixtures without changing established Math answers or existing test expectations.
- [x] Run focused Math module tests and the Math migration gate.

### M5.6 Google Docs/Drive Adapters - Complete

Entry condition: M5.5 complete.

- [x] Port rendering/publishing behavior from `mts-new` behind `src/rendering/google_docs_adapter.py` and publication service boundaries.
- [x] Add mocked Google API tests for copy-master, render, inspect, publish-pair, and retry/failure behavior.
- [x] Prove a master template is never updated.
- [x] Preserve explicit human publishing approval by requiring verified Specs and validated artifacts; Gate 5 integration remains in M5.7.

### M5.7 Math Class End-to-End Integration - Complete

Entry condition: M5.6 complete.

- [x] Execute a staging-only Math Class Worksheet lifecycle: effective config -> Run -> scope -> Spec -> verify -> render -> QA -> Publish Approval readiness.
- [x] Retain generated evidence as an isolated temporary-run fixture with mocked Google Docs/Drive services.
- [x] Run all shared, Math, and migration regression tests.

### M5.7a Weekly Math Workflow Orchestrator - Complete

Entry condition: M5.7 complete.

- [x] Create a Math Weekly workflow orchestrator that resolves Grade 1, 4, 5, 6, Math 1, and Math 2 weekly scopes.
- [x] Build reviewable Weekly plans for Grade 1, 4, 5, 6, and combined Grades 9/10.
- [x] Preserve independent Math 1 and Math 2 curriculum resolution with 25 questions each in the combined Worksheet plan.
- [x] Produce Gate 1 Scope Review data and stop before Question generation.
- [x] Add focused tests for counts, five-day sections, Grade 9/10 split, cache provenance, and Gate 1 readiness.

Focused validation:

```text
A Math Weekly request resolves six curriculum scopes and five Worksheet plans.
The combined Grades 9/10 plan retains two independent scopes with 25 questions each.
```

### M5.7b Weekly Math Staging Integration - Complete

Entry condition: M5.7a passes focused tests.

- [x] Accept synthetic candidate Specs for every Weekly plan and enforce Gate 2.
- [x] Verify all candidates, enforce Gate 3, then render and QA staging-only artifacts.
- [x] Enforce Gate 4 and Publish Approval readiness without publishing.
- [x] Add Weekly lifecycle regression fixture and run the Math migration gate.

The fixture proves lifecycle structure and controls, not curriculum quality. Real worksheet content must still be generated/reviewed and independently verified during a supervised run.

### M5.8 Worksheet Type Activation - In Progress

Entry condition: M5.7 complete.

- [x] Activate Math Class Worksheet with its existing regression baseline.
- [x] Activate Math Weekly Worksheet for Grade 1, Grades 4-5, Grade 6, and combined Grades 9/10.
- [x] Set weekly counts to Grade 1/4/5 = 50, Grade 6 = 40, and Grades 9/10 = 25 each (50 combined).
- [x] Register existing approved Class Worksheet templates as the Math Weekly Worksheet fallback.
- [x] Add focused Math Weekly Worksheet effective config coverage and run the Math migration gate.
- [x] Complete M5.7a/b staging workflow and lifecycle validation for Weekly Worksheet.
- [x] Register 4-Day Homework as a draft Math Worksheet Type with its four instructional sections and explicit activation blockers.
- [x] Register Compact/Unbranded Worksheet as a draft Math Worksheet Type with explicit user-defined count/page constraints and activation blockers.
- [ ] Migrate remaining existing Math Worksheet Types into `data/config/worksheet_types/` one type at a time.
- [ ] Add a regression fixture for each remaining active type.
- [ ] Approve 4-Day Homework counts, duration/continuity rules, template rules, and regression fixtures before activation.
- [ ] Approve Compact/Unbranded count/page constraints, readability rules, unbranded templates, and regression fixtures before activation.
- [x] Register dedicated Weekly Worksheet templates and route Weekly Math to their subject/type manifest.

### M5.9 ELA Extension - Blocked

Unblock only after ELA M1/M2 requirements, knowledge, templates, verification rules, and regression fixtures are approved.

### M5.10 SAT/ACT Extensions - Blocked

Unblock each Worksheet Type independently only after its requirements, timing/scoring rules, templates, validation rules, and regression fixtures are approved.

### M5.11 Folder Structure Refactor - In Progress

Entry condition: M4 architecture/design update approved and M5.8 baseline behavior remains regression-protected.

- [x] Create target `src/mts` package structure for Functional Area capabilities, subject specializations, and infrastructure adapters.
- [x] Add compatibility wrappers under `src/mts` that expose existing runtime, rendering, Math subject, and workflow behavior without deleting legacy modules.
- [x] Move or mirror Math subject tests into `tests/subjects/math` and update focused imports to target `src/mts` modules.
- [x] Add structure validation that fails if new executable source is added outside `src/mts` or new tests are added outside `tests` after migration.
- [x] Create target `data/config`, `data/master`, and `data/transactions` directories with compatibility data copied from current config, subject knowledge, templates, and run evidence.
- [x] Update loaders/writers and tests to prefer `data/` paths while retaining legacy path compatibility until regression passes.
- [x] Retire legacy `subjects/`, root `config`, root `templates`, root `src/runtime`, root `src/rendering`, and root `runs` only after replacement source, tests, and data paths pass the Math migration gate.

Focused validation:

```text
python -m pytest tests/subjects/math tests/shared tests/integration
python tests/math/validate_migration.py
```

Exit condition: new `src/mts` imports and `tests/subjects/math` paths pass while migrated legacy behavior remains available from the target package.

Result: complete. Legacy transaction evidence moved to `data/transactions/legacy_runs`; old mixed roots moved to `archive/legacy-layout`.

### M5.12 Math Weekly Bypass Sample Run - Complete for Offline Sample

Entry condition: M5.11 focused validation passes.

- [x] Resolve effective config for Math Weekly Worksheet, week of `2026-09-07`.
- [x] Create a staging/sample Run with every configured human gate explicitly recorded as bypassed for this run only.
- [x] Generate or synthesize complete Math Weekly Worksheet Specs from one canonical question set per worksheet.
- [x] Independently verify every question and answer; bypassing gates must not bypass verification or QA.
- [x] Render/validate staging artifacts or, if live Google access is not used, produce a sample transaction run that reaches publish-readiness with mocked artifacts.
- [x] Persist run evidence under the configured transaction path and record the result in `end-to-end-progress.md`.

Focused validation:

```text
python tests/integration/test_weekly_math_lifecycle.py
python tests/math/validate_migration.py
```

Exit condition: sample week `2026-09-07` reaches verified, QA-complete, publish-readiness state with all gate bypasses explicitly recorded.

Result: complete through live Google Docs staging render. Canonical publication and Final Delivery were not attempted.

## 4. Validation Rules

1. Run focused unit or integration tests immediately after each module change.
2. Do not edit a second module before the first module's focused validation passes.
3. Run `python tests/math/validate_migration.py` after each integration checkpoint and before enabling a new subject or Worksheet Type.
4. Preserve existing Math P0 data and runtime paths until replacement behavior has passed regression checks.
5. Do not create real production Run data during module development; use fixtures or staging-only artifacts.
6. Update this tracker after each module validation with status, command, result, and any blocker.

## 5. Change Log

| Date | Slice | Status update | Validation |
|---|---|---|---|
| 2026-08-27 | M5.0 Data Foundation | Complete | New JSON files parsed; references resolve; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.1 Effective Config Resolver | Complete | `python tests/shared/test_policy.py` passed 4/4 focused tests. |
| 2026-08-27 | M5.2 Run Loader/Writer | Complete | `python tests/shared/test_run_repository.py` passed 3/3 focused tests. |
| 2026-08-27 | M5.3 Gate Controller | Complete | `python tests/shared/test_gates.py` passed 4/4 focused tests. |
| 2026-08-27 | M5.4 Shared Runtime Integration | Complete | `python tests/integration/test_shared_runtime.py` passed 1/1; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.5 Math Subject Module Adapter | Complete | Legacy `python subjects/math/tests/test_subject_module.py` passed 4/4 at the time; target migration now validates through `tests/subjects/math/test_subject_module.py`. |
| 2026-08-27 | M5.6 Google Docs/Drive Adapters | Complete | `python tests/integration/test_google_docs_adapter.py` passed 3/3 mocked tests; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.7 Math Class End-to-End Integration | Complete | `python tests/integration/test_math_class_lifecycle.py` passed 1/1; combined shared/integration suite passed 20 focused checks; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.8 Worksheet Type Activation | In progress | Math Weekly Worksheet activated for Grade 1, Grades 4-6, and combined Grades 9/10; `python tests/shared/test_policy.py` passed 4/4 and Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.8 Worksheet Type Activation | In progress | 4-Day Homework registered as a draft with four sections and activation blockers; `python tests/shared/test_policy.py` passed 5/5 and Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | Planning correction | Complete | Split Class Worksheet integration from the missing Weekly workflow and staging integration; Weekly remains configuration-active but not production-ready. |
| 2026-08-27 | M5.7a Weekly Math Workflow Orchestrator | Complete | Legacy `python subjects/math/tests/test_weekly_workflow.py` passed 3/3 at the time; target migration now validates through `tests/subjects/math/test_weekly_workflow.py`. |
| 2026-08-27 | M5.7b Weekly Math Staging Integration | Complete | `python tests/integration/test_weekly_math_lifecycle.py` passed 1/1 with five Plans, five-day candidate Specs, and 240 fixture Questions; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.8 Worksheet Type Activation | In progress | Compact/Unbranded Worksheet registered as a draft; `python tests/shared/test_policy.py` passed 6/6 and Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-28 | M5.8 Worksheet Type Activation | In progress | Dedicated Weekly Worksheet student/key masters registered in `subjects/math/config/template-manifests/weekly-worksheet.json`; renderer now consumes the manifest; effective config and reconciliation tests pass. |
| 2026-09-03 | M5.11 Folder Structure Refactor | In progress | Began target `src/mts`, `tests`, and `data` migration plan with legacy compatibility requirement before path retirement. |
| 2026-09-03 | M5.11/M5.12 Structure and sample evidence | Complete for focused slice | `python -m pytest tests/integration/test_weekly_math_lifecycle.py tests/test_target_structure.py tests/test_target_data_layout.py tests/subjects/math/test_target_package_imports.py tests/integration/test_math_weekly_bypass_sample.py` passed 10/10; `python -m pytest tests` passed 51/51; `python tests/math/validate_migration.py` passed 3/3 suites and 14 checks; sample run `run-2026-09-07-weekly-bypass-sample` wrote 5 worksheet records and 25 explicit gate bypass records. |
| 2026-09-03 | M5.11 Target loaders/writers | Complete for focused slice | Target effective config resolver reads `data/config` and `data/master`; target RunLoader/RunWriter and SpecLoader/SpecWriter use `data/transactions`; `python -m pytest tests/test_target_loaders_writers.py tests/integration/test_math_weekly_bypass_sample.py` passed 3/3. |
| 2026-09-03 | M5.11 Legacy root retirement | Complete | Moved historical `runs` to `data/transactions/legacy_runs` and archived old `subjects`, root `config`, root `templates`, `src/runtime`, `src/rendering`, `src/curriculum`, and `src/verification` under `archive/legacy-layout`; `python -m pytest tests` passed 94/94 and `python tests/math/validate_migration.py` passed 4/4 target suites. |
| 2026-09-03 | M5.12 Next-week Math sample regeneration | Complete for offline sample | `python scripts/run_math_weekly_bypass_sample.py` passed from the new active structure for week `2026-09-07`, writing 5 worksheet records and 25 explicit gate bypass records. |
| 2026-09-03 | M5.12 Next-week Math staging render | Complete through staging render | `.\.venv\Scripts\python.exe scripts/render_weekly_specs_to_drive.py --run-root data/transactions/runs/run-2026-09-07-weekly-bypass-sample --date 2026-09-07` rendered 5 worksheet/key pairs to Google Docs staging; `python -m pytest tests` passed 99/99 and `python tests/math/validate_migration.py` passed 4/4 target suites. |
| 2026-09-03 | M5.12 Next-week delivery dry-run | Complete | `python scripts/deliver_weekly_worksheets.py --run-root data/transactions/runs/run-2026-09-07-weekly-bypass-sample --week-of 2026-09-07 --dry-run` resolved all five grade audience folders without copying audience-facing files. |
| 2026-09-03 | M5.12 Seamless generate command runner | Complete | `python scripts/generate_worksheet.py subject=math worksheettype=weekly week=next gates="bypass all" publish=no deliver=no run=run-2026-09-07-weekly-cli` resolved defaults, recorded 25 gate bypasses, rendered 5 worksheet/key pairs to staging, and dry-ran delivery. |
| 2026-09-03 | M5.12 Parameter typo confirmation boundary | Complete | CLI rejects non-canonical `grade=` with a suggestion; prompt/command docs require model-side translation, replay, and user confirmation before invoking canonical `grades=`; `python -m pytest tests/integration/test_generate_worksheet_runner.py` passed 6/6. |
| 2026-09-03 | Confirmed prompt invocation publish/deliver | Delivery blocked | User confirmed `grade=1,5,9-10` -> `grades=1,5,9-10` and week `2026-09-07`; `python scripts/generate_worksheet.py subject=math worksheettype=weekly grades=1,5,9-10 week=2026-09-07 gates="bypass all" publish=yes deliver=yes run=run-2026-09-07-grades-1-5-9-10-publish-deliver` rendered and published 3 pairs, then stopped during Final Delivery on Google Drive `userRateLimitExceeded`; failure recorded in `delivery-failure.json`; tests passed 103/103 and migration gate passed 4/4. |
| 2026-09-03 | M5.12 Curriculum-driven Question Plan fix | Complete | Updated design section 3.5/3.7 and `scripts/generate_worksheet.py` so generation persists `worksheet_plan.json` and `question_plan.json`, derives planned skills from resolved Weekly Curriculum or Yearly Curriculum/progressive fallback, validates Specs against planned slot metadata, and preserves Math 1/Math 2 scope files for combined Grades 9/10; focused tests passed 7/7, full tests passed 103/103, and migration gate passed 4/4. |
