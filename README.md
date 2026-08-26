# MTS AI Generation

Cross-model, cross-harness repository for generating, verifying, rendering, and publishing MTS Math
and ELA worksheets. H

## Supported harnesses

- GitHub Copilot through `.github/copilot-instructions.md`
- ChatGPT and Codex through `AGENTS.md` and repository skills
- Claude and Claude Code through `CLAUDE.md` and `.claude/`
- Other models through the canonical documents and explicit read order

Harness adapters point to the same canonical requirements, design, configuration, workflows, and
schemas. They do not contain independent product logic.

## Start here

1. Read `AGENTS.md`.
2. Select Math or ELA.
3. Read the applicable subject documents and configuration.
4. Invoke the relevant workflow.

## Repository map

- `config/` — shared and subject defaults
- `docs/` — consolidated requirements, design, decisions, and plans
- `subjects/` — subject-specific knowledge and behavior
- `skills/` — reusable capabilities
- `workflows/` — end-to-end procedures
- `schemas/` — machine-validatable contracts
- `src/` — deterministic runtime components
- `templates/` — shared and subject templates
- `tests/` — shared, subject, and golden-example tests
- `runs/` — run state and telemetry
- `outputs/` — approved canonical artifacts
- `outputs-copilot/` — noncanonical staging artifacts

