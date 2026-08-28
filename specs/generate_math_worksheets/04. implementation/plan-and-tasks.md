# MTS Worksheet and Assessment Generation - Implementation Plan and Task Tracker

Status: Active
Last updated: 2026-08-27

## 1. Delivery Strategy

Implement one bounded module at a time. Every module must have a focused validation before another module is changed. Integrate modules only at the checkpoints defined below, then run the existing Math regression gate.

```mermaid
flowchart LR
    D[Data Foundation] --> P[Policy Resolver]
    P --> R[Run Repository]
    R --> G[Gate Controller]
    G --> I1[Shared Runtime Integration]
    I1 --> M[Math Module Adapter]
    M --> A[Google Docs and Drive Adapters]
    A --> I2[Class Worksheet Integration]
    I2 --> WW[Weekly Math Workflow]
    WW --> WI[Weekly Staging Integration]
    WI --> W[Worksheet Type Activation]
    W --> E[ELA Extension]
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
| M5.1 | Policy Resolver | Complete | Focused tests validate active Class resolution, override precedence, immutability, and draft/unknown/incompatible rejection. |
| M5.2 | Run Repository | Complete | Focused tests validate new manifest/policy persistence, compatible resume/checkpointing, and mismatched request/policy rejection. |
| M5.3 | Gate Controller | Complete | Focused tests validate revision-scoped approvals, fail-closed rejection, and dependent invalidation. |
| M5.4 | Shared Runtime Integration | Complete | Shared Math Class fixture passes policy, Run, Scope Review, and scope invalidation; Math migration gate remains green. |
| M5.5 | Math Subject Module Adapter | Complete | Adapter delegates existing P0 curriculum, verification, template/QA behavior while preserving candidate Spec generation as AI-owned. |
| M5.6 | Google Docs/Drive Adapters | Complete | Mocked tests validate master copying, rendering, inspection, paired publication, and fail-closed behavior. |
| M5.7 | Math Class End-to-End Integration | Complete | Staging-only Class Worksheet lifecycle reaches Publish Approval readiness without live publication. |
| M5.7a | Weekly Math Workflow Orchestrator | Complete | Resolves six Math scopes into five Gate 1 Weekly Worksheet plans, including the combined Grades 9/10 split. |
| M5.7b | Weekly Math Staging Integration | Complete | All five Weekly plans pass synthetic candidate-Spec, verification, rendering, QA, and Publish Approval readiness tests in staging. |
| M5.8 | Worksheet Type Activation | In progress | Class and Weekly are configuration-active and staging-ready; remaining Math types require one-at-a-time migration. |
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

### M5.1 Policy Resolver - Complete

Entry condition: M5.0 complete.

- [x] Create `src/runtime/policy.py`.
- [x] Load base, subject, and Worksheet Type YAML configuration.
- [x] Resolve approved current-run overrides into an immutable policy snapshot.
- [x] Reject unknown subjects, unknown Worksheet Types, incompatible subject/type combinations, and invalid overrides.
- [x] Reject `draft` and `disabled` Worksheet Types for production execution.
- [x] Add focused unit tests for precedence and failure paths.

Focused validation:

```text
Class Worksheet + Math resolves to an active immutable policy snapshot.
Weekly Worksheet resolves to an active Math policy; production readiness is verified separately by M5.7a/b.
```

Integration checkpoint: none. Do not modify Run persistence or gates in this slice.

### M5.2 Run Repository - Complete

Entry condition: M5.1 passes focused tests.

- [x] Create `src/runtime/run_repository.py`.
- [x] Create `runs/<subject>/<run_id>/run-manifest.json` and resolved-policy snapshot paths.
- [x] Persist new Run checkpoints using IDs/revisions instead of copying Worksheet Spec questions/answers.
- [x] Resume only when request identity and upstream revisions remain compatible.
- [x] Add focused new/resume/incompatible-resume tests.

Focused validation:

```text
A new Math Class Worksheet Run creates its manifest and policy snapshot.
A compatible request resumes its latest valid checkpoint.
A changed policy or scope revision rejects the prior checkpoint.
```

Integration checkpoint: Policy Resolver + Run Repository.

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

Integration checkpoint: Policy Resolver + Run Repository + Gate Controller.

### M5.4 Shared Runtime Integration - Complete

Entry condition: M5.1 through M5.3 pass focused tests.

- [x] Create shared integration fixtures for an active Math Class Worksheet request.
- [x] Verify resolved policy, manifest checkpoint, gate decision, and invalidation evidence work together.
- [x] Run the existing Math migration gate.

Focused validation:

```text
python tests/math/validate_migration.py
```

Exit condition: Shared runtime tests pass and Math migration gate remains green.

### M5.5 Math Subject Module Adapter - Complete

Entry condition: M5.4 complete.

- [x] Define Math subject module adapter around existing `subjects/math/src/p0_runtime.py` behavior.
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

- [x] Execute a staging-only Math Class Worksheet lifecycle: policy -> Run -> scope -> Spec -> verify -> render -> QA -> Publish Approval readiness.
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
- [x] Add focused Math Weekly Worksheet policy coverage and run the Math migration gate.
- [x] Complete M5.7a/b staging workflow and lifecycle validation for Weekly Worksheet.
- [x] Register 4-Day Homework as a draft Math Worksheet Type with its four instructional sections and explicit activation blockers.
- [x] Register Compact/Unbranded Worksheet as a draft Math Worksheet Type with explicit user-defined count/page constraints and activation blockers.
- [ ] Migrate remaining existing Math Worksheet Types into `config/worksheet-types/` one type at a time.
- [ ] Add a regression fixture for each remaining active type.
- [ ] Approve 4-Day Homework counts, duration/continuity rules, template policy, and regression fixtures before activation.
- [ ] Approve Compact/Unbranded count/page constraints, readability rules, unbranded templates, and regression fixtures before activation.
- [ ] Register dedicated Weekly Worksheet templates when they are approved; the current active fallback remains valid until then.

### M5.9 ELA Extension - Blocked

Unblock only after ELA M1/M2 requirements, knowledge, templates, verification rules, and regression fixtures are approved.

### M5.10 SAT/ACT Extensions - Blocked

Unblock each Worksheet Type independently only after its requirements, timing/scoring rules, templates, validation rules, and regression fixtures are approved.

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
| 2026-08-27 | M5.1 Policy Resolver | Complete | `python tests/shared/test_policy.py` passed 4/4 focused tests. |
| 2026-08-27 | M5.2 Run Repository | Complete | `python tests/shared/test_run_repository.py` passed 3/3 focused tests. |
| 2026-08-27 | M5.3 Gate Controller | Complete | `python tests/shared/test_gates.py` passed 4/4 focused tests. |
| 2026-08-27 | M5.4 Shared Runtime Integration | Complete | `python tests/integration/test_shared_runtime.py` passed 1/1; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.5 Math Subject Module Adapter | Complete | `python subjects/math/tests/test_subject_module.py` passed 4/4; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.6 Google Docs/Drive Adapters | Complete | `python tests/integration/test_google_docs_adapter.py` passed 3/3 mocked tests; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.7 Math Class End-to-End Integration | Complete | `python tests/integration/test_math_class_lifecycle.py` passed 1/1; combined shared/integration suite passed 20 focused checks; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.8 Worksheet Type Activation | In progress | Math Weekly Worksheet activated for Grade 1, Grades 4-6, and combined Grades 9/10; `python tests/shared/test_policy.py` passed 4/4 and Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.8 Worksheet Type Activation | In progress | 4-Day Homework registered as a draft with four sections and activation blockers; `python tests/shared/test_policy.py` passed 5/5 and Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | Planning correction | Complete | Split Class Worksheet integration from the missing Weekly workflow and staging integration; Weekly remains configuration-active but not production-ready. |
| 2026-08-27 | M5.7a Weekly Math Workflow Orchestrator | Complete | `python subjects/math/tests/test_weekly_workflow.py` passed 3/3; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.7b Weekly Math Staging Integration | Complete | `python tests/integration/test_weekly_math_lifecycle.py` passed 1/1 with five Plans, five-day candidate Specs, and 240 fixture Questions; Math migration gate passed 3/3 suites and 14 checks. |
| 2026-08-27 | M5.8 Worksheet Type Activation | In progress | Compact/Unbranded Worksheet registered as a draft; `python tests/shared/test_policy.py` passed 6/6 and Math migration gate passed 3/3 suites and 14 checks. |
