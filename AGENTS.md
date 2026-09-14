# MTS AI Generation — Agent Contract

This repository is the canonical source for MTS worksheet generation across Math and ELA.
Its governing architecture is model-neutral and harness-neutral.

## Precedence

1. Current user instruction
2. `constitution.md`
3. Effective config resolved from applicable configuration
4. Requirements
5. Design defaults

A run-level override is not persisted unless the user explicitly requests it.

## Read order

1. `constitution.md`
2. `specs/generate_math_worksheets/01. intent/requirements.md`
3. `specs/generate_math_worksheets/03. design/design.md` (canonical design document)
4. `data/config/project/base.yaml`
5. The selected subject's requirements, design, and configuration
6. The applicable workflow and skills

For Math, use `src/mts/subjects/math/**`, `docs/subjects/math/**`, `data/config/subjects/math.yaml`, and `data/master/subjects/math/**`.
For ELA, use `src/mts/subjects/ela/**`, `docs/subjects/ela/**`, `data/config/subjects/ela.yaml`, and `data/master/subjects/ela/**` when present.

## Non-negotiable rules


## Instruction scoping

This root file is the only canonical `AGENTS.md`. Subject-specific behavior belongs in subject
requirements, design, configuration, skills, and tests. Add a nested `AGENTS.md` only after repeated
evidence shows that directory-scoped instruction overrides are necessary.

