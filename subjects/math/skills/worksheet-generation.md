# Skill: Weekly Worksheet Generation

## Use when
Generating one or more weekly MTS Math class worksheets.

## Required inputs
Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md`, `config/mts-math-worksheet-config.yaml`, and `templates/template-links.md`. Apply the current user request as the highest-precedence run override.

## Workflow
1. Initialize/resume a run manifest under `runs/`.
2. Resolve curriculum using the local P0 layers in order: progressive backbone → CCS pacing cache → NC standards validation; refresh externally only on a documented fallback trigger.
3. Present Gate 1 scope and stop when that gate is enabled.
4. Create and persist an immutable, schema-validated canonical Worksheet Spec for each approved grade/course.
5. Record every Spec reference and fingerprint in the Run Manifest.
6. Present questions at Gate 2 when enabled; Gate 2 cannot advance from chat approval alone.
7. Invoke the verification skill; reverify after edits.
8. Present Gate 3 verification summary when enabled.
9. Check template revisions against `config/template-manifest.json`; copy templates and render worksheet/key from the same spec.
10. Run targeted content QA plus required visual/layout QA.
11. Present Gate 4 when enabled.
12. Run final QA and present Gate 5.
13. In Copilot context, stage/dump generated artifacts under `outputs-copilot/`; this is not publication.
14. Publish final artifacts only after final approval to `outputs/`; verify final folder/name and persist telemetry/status.

## Fast-path invariants
- Use `knowledge/curriculum/progressive/progressive-math-backbone.json` for long-term `builds_from`/`leads_to` context; CCS pacing determines what is current.
- Cache first, authoritative fallback when needed.
- One Worksheet Spec is the source for worksheet + key.
- Deterministic verification where supported; reasoning review remains mandatory.
- No full template reinspection on a valid revision-cache HIT.
- No publication before final approval.
