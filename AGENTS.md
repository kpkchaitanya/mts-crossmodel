# MTS AI Generation — Agent Contract

This repository is the canonical source for MTS worksheet generation across Math and ELA.
Its governing architecture is model-neutral and harness-neutral.

## Precedence

1. Current user instruction
2. `constitution.md`
3. Applicable configuration
4. Requirements
5. Design defaults

A run-level override is not persisted unless the user explicitly requests it.

## Read order

1. `constitution.md`
2. `specs/generate_math_worksheets/01. intent/requirements.md`
3. `specs/generate_math_worksheets/03. design/design.md` (canonical design document)
4. `config/base.yaml`
5. The selected subject's requirements, design, and configuration
6. The applicable workflow and skills

For Math, read `subjects/math/**` and `config/math.yaml`.
For ELA, read `subjects/ela/**` and `config/ela.yaml`.

## Non-negotiable rules

- Preserve original human intent through requirements, design, implementation, and review.
- Use one canonical Worksheet Spec; derive the worksheet and answer key from it.
- Independently verify every answer and reverify affected items after edits.
- Complete configured content and visual QA before publishing.
- Never edit a master template directly.
- Never present inferred pacing as confirmed.
- Store final approved artifacts only under `outputs/<subject>/`.
- Treat `outputs-copilot/` as staging, never as canonical publication.
- Keep `.github/`, `.claude/`, and other harness adapters thin; they must not redefine governing behavior.
- Keep outputs reviewable and concise enough for a human and an AI system to remain aligned.

## Instruction scoping

This root file is the only canonical `AGENTS.md`. Subject-specific behavior belongs in subject
requirements, design, configuration, skills, and tests. Add a nested `AGENTS.md` only after repeated
evidence shows that directory-scoped instruction overrides are necessary.

