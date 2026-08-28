# Consolidation Report: mts-new vs mts-crossmodel

Date: 2026-08-25

## 1) Executive Summary

Recommendation: use mts-crossmodel as the consolidation base repository, then port the production-ready math implementation pieces from mts-new.

Why this base:
- mts-crossmodel already models the target end-state architecture for multi-subject operation (Math + ELA) with clear governance precedence and subject isolation.
- mts-new is currently stronger in practical math workflow assets (templates, publishing/render scripts, and a full spec package) but is math-only.
- The union target is best achieved by preserving cross-subject structure from mts-crossmodel and importing mature math execution capabilities from mts-new.

## 2) Comparison Scope

Compared areas:
- Governance and operating contract
- Spec-driven development readiness
- Subject coverage and modularity
- Runtime implementation and tests
- Publishing and template execution path
- Repository hygiene and portability

## 3) Observed State

### A. Repository scale and focus

- mts-new tracked files: 70
- mts-crossmodel tracked files: 65

Interpretation:
- mts-new keeps a narrower tracked set but includes practical scripts and deeper math spec artifacts.
- mts-crossmodel has a broader architectural shape for multi-subject operation, with shallow subject runtime implementation outside math P0.

### B. Governance and workflow control

Strengths in mts-new:
- Strong gate discipline and mandatory human checkpoints in agent instructions.
- Explicit run-time configuration precedence and publishing guardrails.

Strengths in mts-crossmodel:
- Explicit cross-repo precedence model and canonical execution contract.
- Clear distinction between final outputs and staging outputs-copilot.
- Shared + subject module split is documented and coherent.

Conclusion:
- Both repos encode good governance, but mts-crossmodel is better aligned with long-term multi-subject consolidation.

### C. Spec-driven development readiness

mts-new:
- Has a full feature spec package for math at specs/01.generate-weekly-math-worksheets (requirements, design, plan, todo, implementation docs).
- This is currently more complete than mts-crossmodel for math feature planning traceability.

mts-crossmodel:
- Has concise consolidated docs and subject-level requirement/design stubs.
- Math and ELA subject requirements are high-level and not yet expanded to detailed FR/NFR traceability like mts-new.

Conclusion:
- mts-new is currently stronger for spec depth (math).
- mts-crossmodel needs spec depth uplift per subject to be truly spec-driven end-to-end.

### D. Runtime implementation and verification

mts-new:
- Practical scripts for template rendering and Drive publishing:
  - scripts/render_docs_from_template.py
  - scripts/publish_to_drive.py
- Additional markdown-to-PDF utility in reports/final/2026-08-22/generate_pdfs.py
- No tracked tests currently under tests/.

mts-crossmodel:
- Has math runtime utility module with deterministic verification and QA helpers:
  - subjects/math/src/p0_runtime.py
- Has math runtime tests:
  - subjects/math/tests/test_p0_runtime.py
  - subjects/math/tests/test_curriculum_backbone.py
  - subjects/math/tests/test_repo_reconciliation.py
- ELA currently has requirements/design/readme but no equivalent runtime/test implementation.

Conclusion:
- mts-new has production-oriented I/O scripts (Drive/docs publishing path).
- mts-crossmodel has better unit-test posture for math runtime core logic.
- Union requires combining both strengths and extending to ELA.

### E. Subject coverage

mts-new:
- Explicitly math-focused; no ELA references found in core docs/spec/config scan.

mts-crossmodel:
- Explicitly supports both subjects in architecture, configs, and folder layout.
- ELA logic is not yet implementation-complete.

Conclusion:
- For union goals (Math + ELA), mts-crossmodel is the only viable base without architectural rollback.

### F. Hygiene and portability considerations

mts-new:
- Untracked local-only folders include .venv and .secrets; not currently git-tracked.
- .gitignore contains basic exclusions for runs/outputs and .secrets.

mts-crossmodel:
- Clean staged/final output boundary and dedicated run/output roots.
- Better suited to multi-harness, multi-subject collaboration as-is.

## 4) Decision

Choose mts-crossmodel as the consolidation target repository.

Reason:
- It already contains the desired canonical architecture for union operation (shared core + subject modules + governance).
- Migrating mts-new into this shape is lower risk than adding ELA and cross-subject governance onto mts-new.

## 5) Union Plan (Phased)

## Phase 0: Baseline and Guardrails (1-2 days)
- Freeze current branches and tag baseline commits for both repos.
- Add migration tracking doc and checklists under docs/plans/.
- Define merge policy: no direct edits to master templates; subject-isolated changes only.

Exit criteria:
- Baseline tags created.
- Migration checklist approved.

## Phase 1: Spec Consolidation (2-4 days)
- Port detailed math spec assets from mts-new specs/01.generate-weekly-math-worksheets into subjects/math/specs/ in mts-crossmodel.
- Establish a parallel ELA spec scaffold with matching FR/NFR structure under subjects/ela/specs/.
- Add traceability mapping from consolidated docs to subject specs.

Exit criteria:
- Math spec in mts-crossmodel reaches current mts-new depth.
- ELA spec skeleton has full requirement categories and acceptance criteria placeholders.

## Phase 2: Runtime Consolidation (3-6 days)
- Migrate and adapt these scripts from mts-new into mts-crossmodel subject/shared runtime paths:
  - scripts/render_docs_from_template.py
  - scripts/publish_to_drive.py
- Integrate with existing math p0 runtime helpers and config schema paths.
- Create shared service wrappers for template rendering and publishing so ELA can reuse them.

Exit criteria:
- End-to-end dry run works for math from Worksheet Spec to rendered artifact in staging.
- Existing math P0 tests still pass.

## Phase 3: Test and Validation Hardening (2-5 days)
- Introduce tests for migrated rendering/publishing adapters (mocked external APIs).
- Add integration test path for math run manifest generation and gate enforcement.
- Add initial ELA runtime smoke tests and schema checks.

Exit criteria:
- Deterministic CI tests pass for math core + adapters.
- ELA has at least smoke-level automated verification.

## Phase 4: ELA Implementation Completion (4-8 days)
- Implement ELA worksheet spec generation and verification flow following shared core lifecycle.
- Add ELA template manifest and QA checks parallel to math controls.
- Validate publish flow to outputs/ela and staging discipline for outputs-copilot/ela.

Exit criteria:
- ELA can complete supervised run through all enabled gates.
- ELA outputs and answer keys are produced from one canonical Worksheet Spec.

## Phase 5: Cutover and Decommission (1-2 days)
- Declare mts-crossmodel as canonical union repo.
- Archive mts-new or convert it to compatibility adapter/docs-only role.
- Publish migration notes and final operational runbook.

Exit criteria:
- Team uses a single canonical repository for both subjects.
- Documentation and workflow commands point only to consolidated paths.

## 6) High-Priority Gap Backlog

1. Spec depth parity
- Gap: mts-crossmodel subject requirements are concise; math needs full FR/NFR depth parity; ELA needs equivalent detailed spec.

2. Production adapter migration
- Gap: Drive/docs rendering-publishing adapters exist in mts-new only.

3. Unified test strategy
- Gap: mts-new has practical scripts but little tracked testing; mts-crossmodel has math core tests but limited integration tests and no ELA runtime tests.

4. Config/schema normalization
- Gap: Align naming/structure between consolidated root configs and subject configs to avoid drift.

5. Security and secret management
- Gap: Ensure OAuth/service-account credential handling is externalized and never committed; add explicit secret handling playbook.

## 7) Risks and Mitigations

- Risk: Migration drifts from existing gate/governance behavior.
  - Mitigation: gate behavior tests + explicit approval checkpoints in run manifest.

- Risk: ELA architecture remains documentation-only.
  - Mitigation: phase-gate ELA implementation with minimum runnable smoke criteria.

- Risk: Integration scripts couple too tightly to Math assumptions.
  - Mitigation: move scripts to shared adapter layer with subject-specific config injection.

- Risk: Template drift breaks rendering.
  - Mitigation: enforce template manifest revision checks before full render.

## 8) Recommended Next Action

Start Phase 1 immediately in mts-crossmodel:
- Create subjects/math/specs/ and subjects/ela/specs/.
- Port math requirements/design/plan/todo from mts-new with path and terminology adaptation.
- Add a traceability index document linking consolidated docs to subject-level specs.

This gives a spec-driven base first, then allows safe runtime migration in Phase 2.
