# MTS Testing System

MTS Testing System is a cross-model, cross-harness system for producing weekly Math and ELA worksheets
with human supervision, durable review artifacts, independent verification, and controlled publishing.
The product goal is not just to generate worksheet text; it is to preserve the teacher's intent from
request through approved outputs, using one canonical Worksheet Spec as the source for both the
student worksheet and the answer key.

The repository is intentionally model-neutral. GitHub Copilot, ChatGPT, Codex, Claude, Claude Code,
and future harnesses all point to the same governing documents, configuration, workflows, schemas,
and subject modules instead of carrying separate product rules.

## What the System Produces

- Editable student worksheets.
- Separate verified answer keys.
- One immutable, schema-validated Worksheet Spec revision for each approved worksheet.
- A Run Manifest with spec references, fingerprints, approvals, QA status, provenance, confidence
  labels, and available telemetry.
- Approved final artifacts under `outputs/<subject>/`; staged or harness-specific artifacts stay out
  of the canonical output path.

## Operating Principles

- Preserve original human intent as an explicit, reviewable thread.
- Generate worksheet and key artifacts from the same canonical spec.
- Verify answers independently; generated answers are not treated as proof.
- Keep human gates enforceable and fail closed when required run artifacts are missing.
- Prefer reusable shared capabilities while keeping Math and ELA expertise subject-specific.
- Keep harness adapters thin so product behavior remains in canonical repository documents.

## Generation Flow

The current worksheet workflow is:

1. Capture the original request, subject, grades, week, and run-level overrides.
2. Load shared configuration and the selected subject configuration.
3. Resolve curriculum scope, source provenance, pacing evidence, and confidence.
4. Create and persist one canonical Worksheet Spec per planned worksheet under `runs/<subject>/`.
5. Record spec references and fingerprints in the Run Manifest.
6. Apply the subject verifier and independent reasoning review.
7. Render the worksheet and answer key from the same spec.
8. Run content QA and visual layout QA.
9. Enforce configured human approval gates.
10. Publish only approved artifacts to `outputs/<subject>/`.

Gate 2 requires durable spec references for the complete planned worksheet set before verification can
continue.

## Gates

`config/base.yaml` `gates` defines the five configured gates (Curriculum Scope Review, Question
Review, Verification Review, Formatting Review, Publish Approval). `/generate-worksheet` accepts a
`gates` parameter (`all`, `bypass all`, or `bypass <gate_id>[,<gate_id>...]`) as an explicit,
run-scoped override. Bypassing a gate only removes its stop-and-approve checkpoint — Worksheet Spec
persistence, independent verification, reverification after edits, and visual QA stay mandatory, and
the bypass decision is recorded in the Run Manifest so it is explicit and auditable rather than
silent.

Once Gate 5 (Publish Approval) is recorded, `config/base.yaml` `publishing.default_publish` makes
`/generate-worksheet` publish automatically (`publish=yes` is the default). Pass `publish=no` to stage
approved artifacts under `outputs-copilot/` (or a staging Drive folder) without moving them into
canonical `outputs/<subject>/`.

## Slash Command Catalog

<table border="1" cellpadding="6" cellspacing="0" rules="all" frame="box" style="border-collapse: collapse; border: 1px solid #6b7280;">
  <thead>
    <tr>
      <th style="border: 1px solid #6b7280;">Functional Area</th>
      <th style="border: 1px solid #6b7280;">Slash Command</th>
      <th style="border: 1px solid #6b7280;">Purpose</th>
      <th style="border: 1px solid #6b7280;">Example Usage</th>
      <th style="border: 1px solid #6b7280;">Math Status</th>
      <th style="border: 1px solid #6b7280;">ELA Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border: 1px solid #6b7280;">Generate Worksheet — Unified Entry Point</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-worksheet</code></td>
      <td style="border: 1px solid #6b7280;">Subject- and worksheet-type-agnostic entry point; resolves <code>subject</code>, <code>worksheettype</code>, <code>gates</code>, <code>grades</code> (default <code>all</code>), <code>week</code> (default <code>current</code>), and <code>publish</code> (default <code>yes</code>; use <code>publish=no</code> to stage only), and delegates to the matching subject command. See <code>commands/generate-worksheet.md</code>.</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-worksheet subject=math worksheettype=weekly gates=bypass all</code></td>
      <td style="border: 1px solid #6b7280;">Active for Math; delegates to <code>/generate-weekly-classworksheets</code></td>
      <td style="border: 1px solid #6b7280;">Refuses and reports; ELA generation not yet registered</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Setup Project (SP)</td>
      <td style="border: 1px solid #6b7280;">Not yet registered</td>
      <td style="border: 1px solid #6b7280;">Load canonical artifacts, resolve subject, supported grades, worksheet types, and override policy.</td>
      <td style="border: 1px solid #6b7280;"><code>/setup-project math weekly</code></td>
      <td style="border: 1px solid #6b7280;">Covered by canonical read order; command planned</td>
      <td style="border: 1px solid #6b7280;">Covered by canonical read order; command planned</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Setup Yearly Curriculum (SYC)</td>
      <td style="border: 1px solid #6b7280;">Not yet registered</td>
      <td style="border: 1px solid #6b7280;">Build or reuse grade/course yearly curriculum progression with standards, prerequisites, provenance, and targeted invalidation.</td>
      <td style="border: 1px solid #6b7280;"><code>/setup-yearly-curriculum math grade 6</code></td>
      <td style="border: 1px solid #6b7280;">Knowledge assets and cache present; command planned</td>
      <td style="border: 1px solid #6b7280;">Requirements/design defined; curriculum command not registered</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Prepare Instructional Cycle (PIC)</td>
      <td style="border: 1px solid #6b7280;">Not yet registered</td>
      <td style="border: 1px solid #6b7280;">Establish week, dates, cycle type, grades, calendar context, and run-level overrides before batch creation.</td>
      <td style="border: 1px solid #6b7280;"><code>/prepare-instructional-cycle math week 5 grades 1,4,5,6,9-10</code></td>
      <td style="border: 1px solid #6b7280;">Modeled inside weekly generation; standalone command planned</td>
      <td style="border: 1px solid #6b7280;">Designed conceptually; standalone command not registered</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Resolve Weekly Curriculum (RWC)</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets</code></td>
      <td style="border: 1px solid #6b7280;">Resolve the current weekly curriculum scope using cache-first, source-aware logic and stop at Gate 1 when enabled.</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets week 5 grades 1,4,5,6,9-10</code></td>
      <td style="border: 1px solid #6b7280;">Active command path</td>
      <td style="border: 1px solid #6b7280;">Subject docs exist; command not registered</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Prepare Batch (PB)</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets</code></td>
      <td style="border: 1px solid #6b7280;">Plan the requested worksheet set, shared overrides, grade/course split, and independent regeneration boundaries.</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets week 5 grades 4,5</code></td>
      <td style="border: 1px solid #6b7280;">Active command path</td>
      <td style="border: 1px solid #6b7280;">Planned through shared workflow adaptation</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Prepare Worksheet (PW)</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets</code></td>
      <td style="border: 1px solid #6b7280;">Apply worksheet type, grade/course, counts, sections, difficulty, template profile, and per-worksheet overrides.</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets week 5 grade 6 weekly</code></td>
      <td style="border: 1px solid #6b7280;">Active command path</td>
      <td style="border: 1px solid #6b7280;">Planned; subject rules documented</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Generate Worksheet (GW)</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets</code></td>
      <td style="border: 1px solid #6b7280;">Generate the canonical Worksheet Spec, ordered sections, questions, expected answers, standards, and Gate 2 review surface.</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets week 5 grade 1</code></td>
      <td style="border: 1px solid #6b7280;">Active command path</td>
      <td style="border: 1px solid #6b7280;">Planned; no ELA generation slash command yet</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Verify Worksheet (VW)</td>
      <td style="border: 1px solid #6b7280;"><code>/verify-worksheet</code></td>
      <td style="border: 1px solid #6b7280;">Independently verify the approved Worksheet Spec/question set, report failed or ambiguous items, and stop at Gate 3 when enabled.</td>
      <td style="border: 1px solid #6b7280;"><code>/verify-worksheet runs/math/&lt;run-id&gt;/specs/&lt;worksheet-spec&gt;.json</code></td>
      <td style="border: 1px solid #6b7280;">Active command path</td>
      <td style="border: 1px solid #6b7280;">Verifier requirements documented; command not registered</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Format Worksheet (FW)</td>
      <td style="border: 1px solid #6b7280;">Not yet registered</td>
      <td style="border: 1px solid #6b7280;">Render verified worksheet and answer key documents from the same spec without modifying master templates.</td>
      <td style="border: 1px solid #6b7280;">Planned after verification gate</td>
      <td style="border: 1px solid #6b7280;">Planned after verification gate</td>
      <td style="border: 1px solid #6b7280;">Planned after subject generation path</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Validate Worksheet (VAL)</td>
      <td style="border: 1px solid #6b7280;">Not yet registered</td>
      <td style="border: 1px solid #6b7280;">Run content QA, visual/layout QA, editability checks, and final readiness checks before approval.</td>
      <td style="border: 1px solid #6b7280;"><code>/validate-worksheet runs/math/&lt;run-id&gt;</code></td>
      <td style="border: 1px solid #6b7280;">Planned QA command; criteria documented</td>
      <td style="border: 1px solid #6b7280;">Planned QA command; criteria documented</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Publish Worksheet (PUB)</td>
      <td style="border: 1px solid #6b7280;">Not yet registered</td>
      <td style="border: 1px solid #6b7280;">Publish only approved worksheet/key pairs to canonical <code>outputs/&lt;subject&gt;/</code> destinations and record links/status.</td>
      <td style="border: 1px solid #6b7280;">Planned after publish approval</td>
      <td style="border: 1px solid #6b7280;">Planned; output policy active</td>
      <td style="border: 1px solid #6b7280;">Planned; output policy active</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Archive Folder (ARC)</td>
      <td style="border: 1px solid #6b7280;"><code>/archive-folder</code></td>
      <td style="border: 1px solid #6b7280;">Publishing utility; moves a folder's previous set of loose files into its <code>Archive</code> child folder, in folder mode or in the latest/dated child of a parent folder. Dry run by default. See <code>commands/archive-folder.md</code>.</td>
      <td style="border: 1px solid #6b7280;"><code>/archive-folder folder=publish foldertype=parent folderdate=latest</code></td>
      <td style="border: 1px solid #6b7280;">Active; subject-agnostic utility</td>
      <td style="border: 1px solid #6b7280;">Active; subject-agnostic utility</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Cleanup Folder (CLN)</td>
      <td style="border: 1px solid #6b7280;"><code>/cleanup-folder</code></td>
      <td style="border: 1px solid #6b7280;">Destructive companion to <code>/archive-folder</code>; trashes loose files, <code>Archive</code> contents, or both. Drive Trash only, never a permanent delete; never deletes folders. Requires a matching <code>--confirm</code> count and is gated by <code>publishing.cleanup.enabled</code>. See <code>commands/cleanup-folder.md</code>.</td>
      <td style="border: 1px solid #6b7280;"><code>/cleanup-folder folder=staging scope=archive</code></td>
      <td style="border: 1px solid #6b7280;">Active; subject-agnostic utility</td>
      <td style="border: 1px solid #6b7280;">Active; subject-agnostic utility</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Manage Templates (MT)</td>
      <td style="border: 1px solid #6b7280;">Not yet registered</td>
      <td style="border: 1px solid #6b7280;">Maintain template registration, revision manifests, cache validity, fallback templates, and controlled template promotion.</td>
      <td style="border: 1px solid #6b7280;"><code>/manage-templates list</code></td>
      <td style="border: 1px solid #6b7280;">Planned; Math templates governed</td>
      <td style="border: 1px solid #6b7280;">Planned; ELA templates governed</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Manage Workflow (MW)</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets</code>, <code>/verify-worksheet</code></td>
      <td style="border: 1px solid #6b7280;">Enforce gates, persist run manifests, support resume/invalidation, capture telemetry, and preserve auditability.</td>
      <td style="border: 1px solid #6b7280;"><code>/generate-weekly-classworksheets resume runs/math/&lt;run-id&gt;</code></td>
      <td style="border: 1px solid #6b7280;">Active through Math commands</td>
      <td style="border: 1px solid #6b7280;">Shared governance active; ELA command surface pending</td>
    </tr>
    <tr>
      <td style="border: 1px solid #6b7280;">Cross-Cutting NFRs</td>
      <td style="border: 1px solid #6b7280;">Applies to all commands and workflows</td>
      <td style="border: 1px solid #6b7280;">Preserve correctness, synchronization, curriculum integrity, reviewability, portability, and observability.</td>
      <td style="border: 1px solid #6b7280;">Use the relevant command for the active lifecycle stage.</td>
      <td style="border: 1px solid #6b7280;">Active governing criteria</td>
      <td style="border: 1px solid #6b7280;">Active governing criteria</td>
    </tr>
  </tbody>
</table>

## Subjects

### Math

The Math module owns curriculum interpretation, CCS/NC alignment, grade progression, question mix,
mathematical verification, notation, diagrams, and ambiguity checks. Curriculum confidence is labeled
as `confirmed`, `strongly_inferred`, or `inferred`, and inferred pacing is never represented as
confirmed district pacing.

### ELA

The ELA module owns weekly theme strategy, anchor passages or paired perspectives, the five-day
learning arc, question construction, evidence notes, grammar corrections, distractor quality, and open
response guidance. It favors readable, high-value work over cramped passages or tiny text.

## Source of Truth

- `constitution.md` — governing principles.
- `AGENTS.md` — repository execution contract and read order.
- `specs/generate_math_worksheets/01. intent/requirements.md` — canonical shared and Math product requirements.
- `specs/generate_math_worksheets/03. design/design.md` — canonical shared and Math architecture/execution design.
- `config/base.yaml` — shared runtime defaults.
- `config/math.yaml` and `config/ela.yaml` — subject defaults.
- `subjects/<subject>/requirements.md` — subject behavior.
- `workflows/generate-weekly-worksheets.md` — end-to-end generation procedure.
- `schemas/` — machine-validatable contracts for specs, manifests, and worksheet types.
- `runs/<subject>/` — per-run truth, including persisted specs and manifests.

Current user instructions override configuration for the active run only unless persistence is
explicitly requested.

## Supported Harnesses

- GitHub Copilot through `.github/copilot-instructions.md`.
- ChatGPT and Codex through `AGENTS.md` and repository skills.
- Claude and Claude Code through `CLAUDE.md` and `.claude/`.
- Other models through the canonical documents and explicit read order.

Harness adapters may point to canonical sources, but they must not redefine governing behavior.

## Start Here

1. Read `AGENTS.md`.
2. Read `constitution.md`.
3. Read `specs/generate_math_worksheets/01. intent/requirements.md`, `specs/generate_math_worksheets/03. design/design.md`, and `config/base.yaml`.
4. Select Math or ELA.
5. Read the selected subject's requirements and configuration.
6. Use the applicable workflow, skills, schemas, and tests.

## Repository Map

- `config/` — shared defaults, subject defaults, and worksheet-type defaults.
- `docs/` — consolidated requirements, plans, migration notes, and supporting knowledge.
- `specs/generate_math_worksheets/` — canonical design document (`03. design/design.md`) plus the intent/architecture/implementation trail that produced it.
- `subjects/` — subject-specific requirements, curriculum knowledge, commands, skills, and
  templates.
- `workflows/` — end-to-end procedures such as weekly worksheet generation.
- `schemas/` — JSON schemas for Worksheet Specs, Run Manifests, and worksheet type contracts.
- `src/` — deterministic runtime components for curriculum, rendering, run control, and verification.
- `templates/` — shared templates; master templates are copied rather than edited directly.
- `tests/` — shared, subject, and golden-example validation tests.
- `runs/` — active and historical run state, manifests, specs, approvals, QA evidence, and telemetry.
- `outputs/` — approved canonical published artifacts.
- `outputs-copilot/` — noncanonical staging artifacts for Copilot-assisted runs.
- `specs/` — product and implementation specs that drive planned changes.
- `.github/`, `.claude/`, and other adapter folders — harness glue only.

## Development Notes

- Install Python dependencies with `pip install -r requirements.txt` when using local runtime scripts.
- Keep shared behavior in root-level docs, schemas, workflows, and runtime modules.
- Keep subject-specific behavior under `subjects/<subject>/` and the matching subject configuration.
- Validate structural or behavioral changes with the relevant tests and schemas before publishing
  artifacts.

