# Math and ELA Consolidation Migration Manifest

## Original human intent

Make the consolidated MTS AI Generation folder the Git repository root, remove the intermediate
`github-repo` layer, support Copilot, ChatGPT, Codex, Claude, and Claude Code, and avoid duplicated
governing instructions.

## Safety boundary

The existing Math and ELA folders remain unchanged until the consolidated repository passes regression
and end-to-end validation.

## Math source mapping

| Existing asset | Consolidated destination | Action |
|---|---|---|
| Root `README.md` | Root and Math README | Merge; retain Math details in module |
| Root `AGENTS.md` | Root `AGENTS.md` | Merge shared rules; move Math rules to Math requirements/design/config |
| `docs/requirements.md` | Shared and Math requirements | Split shared versus Math-specific behavior |
| `docs/design.md` | Shared and Math design | Split shared architecture versus Math implementation |
| `docs/plan.md` | `docs/plans/math-optimization-plan.md` | Migrate after review |
| Math YAML | `config/math.yaml` | Merge without changing working defaults |
| Template manifest | `config/template-manifest.json` | Migrate to shared template control |
| `skills/` | Root skills plus Math extensions | Refactor after baseline migration |
| `commands/` | `workflows/` and harness adapters | Convert to canonical workflows |
| `knowledge/` | `subjects/math/knowledge/` | Move intact initially |
| `schemas/` | Root `schemas/` | Reconcile into extensible shared contracts |
| `src/p0_runtime.py` | Shared runtime plus Math verifier | Migrate intact, then refactor |
| `tests/` | Shared and Math tests | Preserve all regression tests |
| `templates/` | Shared and Math templates | Classify; preserve master IDs |
| `runs/`, `outputs/`, `outputs-copilot/` | Subject-specific consolidated folders | Migrate only after cutover decision |

## ELA source mapping

| Existing asset | Consolidated destination | Action |
|---|---|---|
| Root README and AGENTS Google Docs | Root/ELA Markdown files | Convert; do not preserve as executable Google Docs |
| ELA requirements/design Google Docs | `subjects/ela/` Markdown files | Convert and extend shared requirements |
| ELA YAML Google Doc | `config/ela.yaml` | Convert to actual YAML |
| Progressive ELA backbone | `subjects/ela/knowledge/` | Convert to structured durable knowledge |
| Empty skills/commands/schemas/src/tests | Shared framework and ELA implementations | Do not copy empty folders |
| `runs/`, `outputs/`, `outputs-copilot/` | Subject-specific consolidated folders | Migrate only after cutover decision |

## Phases

- Phase 0: inventory and preserve source folders
- Phase 1: establish consolidated root and canonical cross-harness files
- Phase 2: migrate Math without behavior changes and run regressions
- Phase 3: extract proven common capabilities
- Phase 4: implement ELA using the common core and ELA-specific verification
- Phase 5: run end-to-end and cross-harness validation
- Phase 6: declare cutover and archive legacy sources after explicit approval

## Current status

- Phase 0: completed at planning level
- Phase 1: repository structure and canonical seed files created
- Phase 2: Math implementation copied intact into `subjects/math/`; source preserved unchanged
- Phase 2 runtime validation: PASS — 3/3 suites, 14/14 checks on 2026-08-25
- Phase 3 onward: pending
