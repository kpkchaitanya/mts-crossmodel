# Command: Generate Weekly Class Worksheets

Math-specific entry point, invoked by `/generate-worksheet subject=math` (or directly for Math-only
use). For `worksheettype=weekly`, execute the concrete, code-grounded steps in
[`skills/weekly-worksheet-execution-runbook.md`](../skills/weekly-worksheet-execution-runbook.md)
directly — do not re-derive the process from `specs/generate_math_worksheets/03. design/design.md`/`requirements.md` first. Use all enabled
grades (`grades=all`) for the current week (`week=current`) if not otherwise specified.

For combined Grades 9/10, resolve Grade 9 and Grade 10 independently and preserve the configured
split; the runbook and `weekly_workflow.prepare_scope_review` already do this.

Apply the `gates` resolution from `/generate-worksheet` when present; default to
`data/config/project/base.yaml` `gates` (all gates enabled) when invoked directly. Present the
configured Gate 1 curriculum scope first and stop for approval unless Gate 1 was explicitly bypassed
for this run.

Apply the `publish` resolution from `/generate-worksheet` when present; default to `publish=yes`
(`data/config/project/base.yaml` `publishing.default_publish`), which publishes automatically once
Gate 5 is recorded. Pass `publish=no` to stage artifacts only and stop before the publish step.

Apply `difficulty`/`diversity` from `/generate-worksheet` when present; default to `medium_plus`
(`data/config/project/base.yaml` `question_design`). Call `MathSubjectModule.build_week_plan(...)` before authoring
questions and `check_diversity_and_progression(spec)` after, per
[`skills/weekly-worksheet-execution-runbook.md`](../skills/weekly-worksheet-execution-runbook.md).

Apply `topic_overrides` from `/generate-worksheet` when present (default none); parse once with
`question_plan.parse_topic_overrides` and pass each grade's slice into that grade's `build_week_plan(...)` call.

## Copilot output location
When this command is executed from the Copilot repository context, dump/stage generated artifacts under `outputs-copilot/`. Canonical `outputs/` is reserved for the approved publish step.
