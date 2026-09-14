# Math Module Migration Status

## Source

- Math project folder: `1VFOtBDGpw53ZWofxcXILzvUmM-vc5I2j`
- Former implementation container: `github-repo` (`115NtTyQjl60t4yherGboMhYw7FMbwxS_`)
- Migration method: Drive copies; source files were not moved, renamed, edited, or deleted

## Behavior-preserving module layout

The working Math implementation was copied intact under this subject module using its existing
relative structure: `config/`, `docs/`, `knowledge/`, `schemas/`, `src/`, `skills/`, `commands/`,
`templates/`, and `tests/`.

The former root `AGENTS.md`, README, design, and requirements are retained with `.legacy` names for
traceability. They are not active governing files. The consolidated root `AGENTS.md` remains the only
canonical agent contract.

Former `.github` instructions and prompts are stored under `legacy-harness-adapters/` for audit and
comparison. They are not loaded as active GitHub Copilot instructions.

## Preserved assets

- Full P0 runtime
- Original Math configuration and template manifest
- Worksheet and run schemas
- Generation and verification skills
- Generation and verification commands
- Progressive Math backbone
- CCS pacing cache and NC standards cache
- Source provenance metadata
- Math regression tests and P0 smoke result
- Math template registry and master-template copies
- Template-options planning document

## Deliberately not migrated yet

- Historical `runs/`
- Published `outputs/`
- `outputs-copilot/`
- SAT subfolder under Math outputs

These remain in the original project until cutover because they are operational history and published
artifacts, not required for behavior-preserving code migration.

## Validation result

The consolidated structure was materialized as a local Git working tree on 2026-08-25. The Math
migration gate passed 3/3 suites and 14/14 checks. The original reconciliation test was updated only
where its standalone-repository paths conflicted with the consolidated architecture.

Repeat with:

    python tests/math/validate_migration.py

Run the same gate after GitHub publication and before shared-core extraction.
