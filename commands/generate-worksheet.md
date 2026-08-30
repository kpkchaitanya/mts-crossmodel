# Command: Generate Worksheet

Unified, subject- and worksheet-type-agnostic entry point for worksheet generation. Resolves its
parameters against canonical configuration and delegates to the selected subject module and
worksheet-type definition instead of duplicating subject-specific logic.

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `subject` | `math`, `ela` | `math` | Must resolve to `config/<subject>.yaml` and a registered `subjects/<subject>/commands/` entry point. `ela` generation is not yet registered; the command reports this and stops rather than guessing behavior. |
| `worksheettype` | `weekly`, `class`, `homework-4-day`, `compact-unbranded` | `weekly` | Resolves to the matching `worksheet_type_id` under `config/worksheet-types/`. Only `status: active` types run (`weekly-worksheet`, `class-worksheet` today). `draft`/`disabled` types are refused, and the type's `extension_readiness.blockers` are reported, unless the user explicitly accepts them for this run. |
| `gates` | `all`, `bypass all`, `bypass <gate_id>[,<gate_id>...]` | `all` | Explicit, run-scoped override of `config/base.yaml` `gates`. See Gate resolution below. Never applied silently. |
| `grades` | `all`, or a list/range (e.g. `1,4,5,6,9-10`) | `all` | Passed through as `grade_ids` to the subject's scope resolution (e.g. `weekly_workflow.prepare_scope_review`). `all` resolves to every grade/course enabled in the subject's grade/course catalog for the selected worksheet type; an explicit list restricts the run to only those grades/courses. |
| `week` | `current`, a week number (e.g. `5`), or an ISO date | `current` | Resolves the `on_date` used for curriculum scope resolution against `config/base.yaml` `calendar.week_1_start` (`2026-08-17`, a Monday). See Week resolution below. |
| `publish` | `yes`, `no` | `yes` (`config/base.yaml` `publishing.default_publish`) | Whether to execute the final publish step (moving staged artifacts from `outputs-copilot/`/staging Drive into canonical `outputs/<subject>/`) automatically once Gate 5 (`publish_approval`) is recorded. `publish=no` stops after staging; artifacts remain staged pending a separate, explicit publish action. Publishing still only proceeds once `publish_approval` is recorded (approved directly or via an explicit `gates` bypass) — `publish=yes` never skips that recorded approval, it only removes the extra manual publish step afterward. |
| `deliver` | `yes`, `no` | `yes` (`config/base.yaml` `publishing.final_delivery.default_deliver`) | Whether to execute Final Delivery after publication: copying each published pair into `Week_<WEEK_OF>` under that grade's audience folder in `config/<subject>.yaml` `publishing.final_delivery.destinations_by_grade`. Requires `publish=yes`; `deliver=yes publish=no` is refused rather than silently downgraded, because there is nothing published to deliver. `deliver=no` ends the run at Staging. Delivery never runs before `publish_approval` is recorded, and never modifies content. |
| `difficulty` | `Low`, `Low+`, `Medium`, `Medium+`, `High`, `Very High` | `Medium+` (`config/base.yaml` `question_design.difficulty.default`) | How ambitious the difficulty ramp is across the week/day. See Question design below. |
| `diversity` | `Low`, `Low+`, `Medium`, `Medium+`, `High`, `Very High` | `Medium+` (`config/base.yaml` `question_design.diversity.default`) | How many distinct skills mix per day and how often spiral-review is injected. See Question design below. |
| `topic_overrides` | `grade:amount:topic[;grade:amount:topic...]` (`amount` is `N%` or a fixed count) | none | Forces a subset of a specific grade's *daily* questions onto a named topic — e.g. `grade_1:60%:Count on and Count down using add and subtract`. Applies every day that week, not once across the week. See Question design below. |
| `run` (resume) | an existing run id | none | Passed through unchanged to `RunRepository.create_or_resume` to resume an in-progress run instead of starting a new one. |

## Question design

`difficulty` and `diversity` are independent, parametrizable settings on the same 6-point ordinal
scale (`config/base.yaml` `question_design.levels`), resolved via
`subjects/<subject>/src/question_plan.py` `normalize_level` (accepts natural spellings like `Low+`,
`Very High`).

- `difficulty` selects a `(start_rank, end_rank)` band on that scale (e.g. `medium_plus` → ranks 1–4,
  `low_plus` → ranks 0–2). Each question's actual difficulty is computed from its position — half from
  its day's position in the week (Monday easier, Friday harder), half from its position within the day
  (Q1 easier than Q10) — linearly mapped into the configured band. Call `build_week_plan(...)` before
  authoring content to get this per-slot plan; call `check_diversity_and_progression(spec)` after
  authoring as a deterministic QA gate (difficulty must be non-decreasing per day).
- `diversity` selects a minimum distinct-skill count per day and how often (every Nth slot) a
  spiral-review skill is substituted into the rotating current-week skill sequence, so no day drills a
  single skill. `check_diversity_and_progression(spec)` also fails if a day doesn't meet the configured
  minimum distinct-skill count.
- `topic_overrides` is parsed once per command invocation via `question_plan.parse_topic_overrides(raw)`
  into `{grade_id: [{topic, kind, value}, ...]}`. When calling `build_week_plan(...)` for a given grade,
  pass `topic_overrides=<parsed>.get(grade_id)` for that grade only. Override slots are spread evenly
  across the day (`question_plan._assign_evenly_spaced`) and keep the same position-based difficulty as
  any other slot — only the skill/topic label changes. Combined overrides that exceed a day's slot
  count raise rather than silently truncating.

## Week resolution

`config/base.yaml` `calendar.week_1_start` (`2026-08-17`) anchors school-year instructional week
numbering: week `N` starts on `week_1_start + 7 * (N - 1)` days. Resolve `week` before curriculum scope
resolution:

1. `week=current` (default): compute today's date under `project.timezone`, then take the Monday of
   that date's calendar week as `on_date` (e.g. via `p0_runtime.week_start_iso`). Also derive the
   corresponding instructional week number (`floor((on_date - week_1_start).days / 7) + 1`) for
   reporting — it is informational only and never overrides the resolved date.
2. `week=<n>` (an integer): `on_date = week_1_start + timedelta(days=7 * (n - 1))`.
3. `week=<ISO date>`: use the date as given; the subject's week-start logic still snaps it to that
   week's Monday before curriculum lookup.

Report the resolved instructional week number and `on_date` alongside the Gate 1 scope so the user can
confirm the run targets the intended week.

## Gate resolution

`config/base.yaml` defines the five configured gates (`scope_review` through `publish_approval`,
matching `src/runtime/gates.py` `GATES` exactly). This command resolves the `gates` parameter against
that list before generation starts:

1. `gates=all` (default): every gate stops for approval as configured.
2. `gates=bypass all`: every gate's stop-and-approve checkpoint is skipped for this run only.
3. `gates=bypass <gate_id>[,<gate_id>...]`: only the listed gates are skipped; unlisted gates still stop for approval.

Bypassing a gate only removes its stop-and-wait checkpoint. It never waives
`config/base.yaml` `gates.bypass.non_bypassable_requirements` — Worksheet Spec persistence,
independent verification, reverification after edits, and visual QA remain mandatory regardless of
the `gates` value. Record the resolved decision (which gates were bypassed, and that it was by
explicit current-user instruction) in the Run Manifest `gates` field before generation proceeds. A
bypass this command applies is explicit and logged, not silent, so it does not violate the
requirement to apply configured human gates without silently bypassing them.

## Behavior

1. Resolve `subject` and load `config/base.yaml` plus `config/<subject>.yaml`. Refuse and report if the subject has no registered generation command under `subjects/<subject>/commands/`.
2. Resolve `worksheettype` against `config/worksheet-types/*.yaml` by `worksheet_type_id` and confirm `compatible_subjects` includes the resolved subject.
3. Resolve `grades` (default `all`) and `week` (default `current`) per Week resolution above into the `grade_ids`/`on_date` inputs the subject's scope resolution expects.
4. Resolve `gates` per Gate resolution above and record the decision in the Run Manifest.
5. Resolve `publish` (default `yes` from `config/base.yaml` `publishing.default_publish`) and record it in the Run Manifest alongside `gates`.
6. Resolve `difficulty` and `diversity` (default `medium_plus` from `config/base.yaml` `question_design`) and pass them to the subject's `build_week_plan(...)` before authoring, and to `check_diversity_and_progression(spec)` as a QA gate after authoring. See Question design above.
7. Resolve `topic_overrides` (default none) via `question_plan.parse_topic_overrides(raw)` once, and pass the per-grade slice to `build_week_plan(...)` for each grade. See Question design above.
8. **Echo the fully-resolved parameter set back to the user before any authoring/rendering starts** —
   every parameter above (`subject`, `worksheettype`, `grades`, `week`, `gates`, `publish`, `deliver`,
   `difficulty`, `diversity`, and `topic_overrides`), explicitly stating `topic_overrides: none` when
   the user did not supply one for *this* invocation. Never carry a `topic_overrides` (or any other
   parameter) value forward from an earlier conversation turn, an example from prior design
   discussion, or a previous run — every invocation resolves its parameters from that invocation's
   input and configured defaults only. This step exists specifically to make an incorrectly
   carried-over value visible and correctable before it reaches authored content or a published
   document, not just auditable afterward in the Run Manifest.
9. Execute the resolved subject's execution runbook directly (for `subject=math` and
   `worksheettype=weekly`, this is
   [`subjects/math/skills/weekly-worksheet-execution-runbook.md`](../subjects/math/skills/weekly-worksheet-execution-runbook.md)),
   which lists the exact module calls, scripts, and gate ids to run — do not re-derive the process
   from `specs/generate_math_worksheets/03. design/design.md`/`specs/generate_math_worksheets/01. intent/requirements.md` first; those are background rationale only. The runbook's run-mode failure and change-control protocol is mandatory during execution.
10. In a Copilot repository context, stage generated artifacts under `outputs-copilot/`; canonical `outputs/<subject>/` is reserved for the approved publish step.
11. Once `publish_approval` is recorded for the run: if `publish=yes` (default), immediately execute the publish step (e.g. `GoogleDocsAdapter.publish_pair`) into `outputs/<subject>/` and report the published links. If `publish=no`, stop after staging and report that artifacts are staged only, pending a separate publish action.
12. Publishing ends **Staging**. If `deliver=yes` (default), continue into **Final Delivery**: copy each published pair into `Week_<WEEK_OF>` under that grade's parent folder from `config/<subject>.yaml` `publishing.final_delivery.destinations_by_grade`, reusing an existing week folder rather than duplicating it, then report the audience-facing links. Delivery never renders or edits content, and staging is retained as the audit trail. If `deliver=no`, stop after publication and report that the batch has not been delivered to its audience.

## Examples

- `/generate-worksheet subject=math worksheettype=weekly gates=bypass all` (grades default to `all`, week defaults to `current`, difficulty/diversity default to `Medium+`, and the run publishes automatically since `publish` defaults to `yes`)
- `/generate-worksheet subject=math worksheettype=weekly gates=bypass all publish=no` (generate and stage only; do not publish)
- `/generate-worksheet subject=math worksheettype=weekly deliver=no` (generate, verify, and publish to `outputs/math/`, but do not put anything in front of parents)
- `/generate-worksheet subject=math worksheettype=class week=5 grades=1,4,5,6,9-10`
- `/generate-worksheet subject=math worksheettype=weekly gates="bypass scope_review,formatting_review"`
- `/generate-worksheet subject=math worksheettype=weekly grades=4,5 week=current`
- `/generate-worksheet subject=math worksheettype=weekly difficulty="High" diversity="Very High"`
- `/generate-worksheet subject=math worksheettype=weekly topic_overrides="grade_1:60%:Count on and Count down using add and subtract; grade_4:30%:data and graphing; grade_5:20%:coordinate geometry; grade_6:20%:prime factorization"`

## Relationship to existing commands

This is the primary generation entry point. When `subject=math`, it invokes
`subjects/math/commands/generate-weekly-classworksheets.md`, which still documents Math-specific
defaults but no longer resolves worksheet type or gates on its own — both are resolved here first and
passed through.
