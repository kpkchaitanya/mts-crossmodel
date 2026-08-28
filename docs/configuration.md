# Configuration Map

This document is the navigation index for configuration in the MTS cross-model repository. It does not replace the YAML/JSON sources; it identifies which source owns each setting.

## Active Resolution Order

For a normal run, `src/runtime/policy.py` loads and deep-merges these files in order:

1. `config/base.yaml`
2. `config/<subject>.yaml`, currently `config/math.yaml`
3. `config/worksheet-types/<worksheet-type>.yaml`, currently `config/worksheet-types/weekly-worksheet.yaml`
4. Explicit run overrides from the current request

The effective policy is an immutable per-run snapshot. Run-specific changes are not written back to configuration unless explicitly requested.

## Where To Edit

| Need | Edit this file | Main settings |
|---|---|---|
| Shared project behavior | `config/base.yaml` | Project name/timezone, Spec requirement, worksheet/key synchronization, verification blocking, shared formatting, output roots, run roots, telemetry defaults |
| Math-wide behavior | `config/math.yaml` | Subject identity, human-supervised mode, curriculum confidence labels, progressive curriculum backbone, Math verification expectations, Math output target |
| Weekly Worksheet behavior | `config/worksheet-types/weekly-worksheet.yaml` | Active status, Math compatibility, Monday-Friday sections, counts per grade, Grade 9/10 split, template-manifest path, validation requirements |
| Other Worksheet Types | `config/worksheet-types/<type>.yaml` | Type status, supported subjects, sections, counts, template selection, validation, extension blockers |
| Math curriculum cache paths and Math-specific legacy defaults | `subjects/math/config/mts-math-worksheet-config.yaml` | Curriculum source priority, content mix, detailed verification switches, human gates, publishing naming, P0 cache paths |
| Template IDs and cached revisions | `subjects/math/config/template-manifest.json` | Worksheet master ID/revision, answer-key master ID/revision, layout slots, structural cache metadata |
| Worksheet-Type template registry | `templates/by-worksheet-type/template-manifest.json` | Which subject/Worksheet Type points to which template manifest and whether a fallback is active |
| Curriculum source URLs and freshness | `subjects/math/knowledge/sources.json` | CCS, NC DPI, and other authoritative source URLs and verification dates |
| Weekly curriculum scope | `subjects/math/knowledge/curriculum/ccs-2026-2027/pacing.json` | Week-to-grade scope, topics, spiral review, confidence, pacing basis |
| Progressive learning context | `subjects/math/knowledge/curriculum/progressive/progressive-math-backbone.json` | Grade progression, units, key concepts, builds-from, and leads-to relationships |
| Grade/course enablement and catalog | `subjects/math/knowledge/grade-course-catalog.json` | Enabled Math grades/courses and independent Grade 9/10 curriculum scope IDs |
| Per-run truth | `runs/math/<run-id>/` | Resolved policy, Specs, approvals, QA, rendered artifact links, and telemetry; do not edit as defaults |

## Current Weekly Math Defaults

The active Weekly Worksheet file currently controls these values:

- Grade 1: 50 questions, 10 per day
- Grade 4: 50 questions, 10 per day
- Grade 5: 50 questions, 10 per day
- Grade 6: 40 questions, 8 per day
- Grades 9/10 combined: 50 questions, 5 per day, split 25 Math 1 / 25 Math 2
- Five sections: Foundation, Discover, Practice, Apply and Review, Mastery
- Template manifest: `subjects/math/config/template-manifest.json`
- Verification required before rendering
- Visual QA required before final approval

## Templates And Google Drive

`subjects/math/config/template-manifest.json` is the canonical cache for master template IDs and revisions. The master document URLs are also present in the legacy Math config for compatibility, but the active weekly Worksheet Type resolves the manifest path above.

The configured template IDs identify master documents. A run creates copied staging documents and records their generated links under `runs/math/<run-id>/rendered-artifacts.json`. Those generated links are run artifacts, not configuration defaults.

The current live staging renderer is `scripts/render_weekly_specs_to_drive.py`. Its staging folder and OAuth token path are currently constants in that script and should be moved to configuration before generalizing the renderer. Credentials must remain outside the repository and must never be placed in Specs, manifests, or this document.

## Important Duplication To Resolve

`subjects/math/config/mts-math-worksheet-config.yaml` still contains older Class Worksheet counts and defaults, while the active Weekly path uses `config/worksheet-types/weekly-worksheet.yaml`. This is the source of apparent conflicts such as 32-question Class templates versus 40/50-question Weekly plans.

Recommended ownership rule:

- Keep shared policy in `config/base.yaml`.
- Keep Math-wide policy in `config/math.yaml`.
- Keep Worksheet-Type behavior in `config/worksheet-types/`.
- Keep template identity/cache in `subjects/math/config/template-manifest.json`.
- Migrate remaining active P0 switches and source paths out of the legacy subject config, then retire or clearly label `mts-math-worksheet-config.yaml` as compatibility-only.

Do not change `runs/` to alter future defaults. A run directory is evidence of what happened for one instructional cycle.
