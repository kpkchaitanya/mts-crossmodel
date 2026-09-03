# Configuration Map

This document is the navigation index for configuration in the MTS cross-model repository. It does not replace the YAML/JSON sources; it identifies which source owns each setting.

## Active Resolution Order

For a normal run, `src/mts/setup_project/configure.py` loads and deep-merges these files in order:

1. `data/config/project/base.yaml`
2. `data/config/subjects/<subject>.yaml`, currently `data/config/subjects/math.yaml`
3. `data/config/worksheet_types/<worksheet_type>.yaml`, currently `data/config/worksheet_types/weekly_worksheet.yaml`
4. Explicit run overrides from the current request

The effective config is an immutable per-run snapshot. Run-specific changes are not written back to configuration unless explicitly requested.

## Where To Edit

| Need | Edit this file | Main settings |
|---|---|---|
| Shared project behavior | `data/config/project/base.yaml` | Project name/timezone, Spec requirement, worksheet/key synchronization, verification blocking, shared formatting, output roots, run roots, telemetry defaults |
| Math-wide behavior | `data/config/subjects/math.yaml` | Subject identity, human-supervised mode, curriculum confidence labels, progressive curriculum backbone, Math verification expectations, Math output target |
| Weekly Worksheet behavior | `data/config/worksheet_types/weekly_worksheet.yaml` | Active status, Math compatibility, Monday-Friday sections, `questions_per_day`, `questions_per_week`, Grade 9/10 split, Weekly template-manifest path, validation requirements |
| Other Worksheet Types | `data/config/worksheet_types/<type>.yaml` | Type status, supported subjects, sections, `questions_per_worksheet`, template selection, validation, extension blockers |
| Archived legacy Math configuration | `archive/subjects/math/config/archive/mts-math-worksheet-config.yaml` | Historical Class Worksheet defaults and settings retained for reference; not loaded by the active resolver and must not be edited for new runs |
| Class template IDs and cached revisions | `data/master/subjects/math/template_manifests/class-worksheet.json` | Class Worksheet master ID/revision, answer-key master ID/revision, layout slots, structural cache metadata |
| Weekly template IDs and cached revisions | `data/master/subjects/math/template_manifests/weekly-worksheet.json` | Weekly Worksheet master ID/revision, answer-key master ID/revision, layout metadata, inspection/cache status |
| Worksheet-Type template registry | `data/master/templates/registry.json` | Which subject/Worksheet Type points to which template manifest and whether a fallback is active |
| Curriculum source URLs and freshness | `data/master/subjects/math/curriculum_sources.json` | CCS, NC DPI, and other authoritative source URLs and verification dates |
| Weekly curriculum scope | `data/master/subjects/math/curriculum/ccs-2026-2027/pacing.json` | Week-to-grade scope, topics, spiral review, confidence, pacing basis |
| Progressive learning context | `data/master/subjects/math/curriculum/progressive/progressive-math-backbone.json` | Grade progression, units, key concepts, builds-from, and leads-to relationships |
| Grade/course enablement and catalog | `data/master/subjects/math/grade_course_catalog.json` | Enabled Math grades/courses and independent Grade 9/10 curriculum scope IDs |
| Per-run truth | `data/transactions/subjects/<subject>/grades/<grade>/cycles/<cycle>/...` plus `data/transactions/runs/<run-id>/` | Effective config, Specs, approvals, QA, rendered artifact links, and telemetry; do not edit as defaults |

## Current Weekly Math Defaults

The active Weekly Worksheet file currently controls these values:

- Grade 1: 50 questions, 10 per day
- Grade 4: 50 questions, 10 per day
- Grade 5: 50 questions, 10 per day
- Grade 6: 40 questions, 8 per day
- Grades 9/10 combined: 25 questions, 5 per day, split 13 Math 1 / 12 Math 2
- Five sections: Foundation, Discover, Practice, Apply and Review, Mastery
- Template manifest: `data/master/subjects/math/template_manifests/weekly-worksheet.json`
- Verification required before rendering
- Visual QA required before final approval

Count naming is scope-specific by design:

- `questions_per_day` is the daily allocation inside a Weekly Worksheet.
- `questions_per_week` is the total Weekly Worksheet allocation across its instructional days.
- `questions_per_worksheet` is the default count for one Class, Compact, or other single-sheet artifact.
- `worksheet.question_count` is retained only in a concrete Worksheet Spec to record the realized count of that artifact; it is not a configurable default name.

For combined products, `questions_per_day` applies to the combined worksheet, not separately to each
source group. The deterministic derivation is `questions_per_day x configured sections =
questions_per_week`; `grade_split` must sum to `questions_per_week`, and `source_selector` identifies
the source group for each split entry.

## Templates And Google Drive

`data/master/subjects/math/template_manifests/class-worksheet.json` is the Class Worksheet template manifest. Weekly Worksheet has its own manifest at `data/master/subjects/math/template_manifests/weekly-worksheet.json`, containing the supplied Weekly master IDs. The Weekly manifest remains inspected only when both masters' live revisions match the recorded revisions.

The configured template IDs identify master documents. A run creates copied staging documents and records generated links under the run's transaction evidence. Those generated links are run artifacts, not configuration defaults.

The current live staging renderer is `scripts/render_weekly_specs_to_drive.py`. Its staging folder and OAuth token path are currently constants in that script and should be moved to configuration before generalizing the renderer. Credentials must remain outside the repository and must never be placed in Specs, manifests, or this document.

## Important Duplication To Resolve

The older Math configuration is archived under `archive/subjects/math/config/archive/mts-math-worksheet-config.yaml`. It contained Class Worksheet counts and defaults, while the active path uses `data/config/subjects/math.yaml` plus `data/config/worksheet_types/<worksheet_type>.yaml`. Archiving removes the source of apparent conflicts such as 32-question Class templates versus 40/50-question Weekly plans.

Recommended ownership rule:

- Keep shared configuration in `data/config/project/base.yaml`.
- Keep Math-wide configuration in `data/config/subjects/math.yaml`.
- Keep Worksheet-Type behavior in `data/config/worksheet_types/`.
- Keep Class template identity/cache in `data/master/subjects/math/template_manifests/class-worksheet.json`.
- Keep Weekly template identity/cache in `data/master/subjects/math/template_manifests/weekly-worksheet.json`.
- Keep the archived legacy file for historical comparison only; add future active settings to the canonical shared, subject, or Worksheet Type configuration files.

Do not change `data/transactions/` to alter future defaults. A run directory is evidence of what happened for one instructional cycle.
