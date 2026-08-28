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
- `docs/requirements.md` — shared product requirements.
- `docs/design.md` — shared architecture and execution design.
- `config/base.yaml` — shared runtime defaults.
- `config/math.yaml` and `config/ela.yaml` — subject defaults.
- `subjects/<subject>/requirements.md` and `subjects/<subject>/design.md` — subject behavior.
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
3. Read `docs/requirements.md`, `docs/design.md`, and `config/base.yaml`.
4. Select Math or ELA.
5. Read the selected subject's requirements, design, and configuration.
6. Use the applicable workflow, skills, schemas, and tests.

## Repository Map

- `config/` — shared defaults, subject defaults, and worksheet-type defaults.
- `docs/` — consolidated requirements, design, plans, migration notes, and supporting knowledge.
- `subjects/` — subject-specific requirements, design, curriculum knowledge, commands, skills, and
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

