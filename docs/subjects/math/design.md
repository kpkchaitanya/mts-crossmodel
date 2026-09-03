# Math Design

Resolve progressive context, pacing evidence, and standards; construct the configured question mix;
create the canonical Worksheet Spec; apply deterministic checks where supported; independently review
conceptual and wording quality; then use the shared rendering, QA, gate, and publishing components.

## Question authoring: difficulty, diversity, and topic overrides

Question authoring is agent-owned (see `skills/weekly-worksheet-execution-runbook.md`), but its
*shape* — difficulty ramp, skill diversity, and any forced topic mix — is planned and validated by
deterministic code in `src/question_plan.py`, not left to authoring judgment alone.

- **`difficulty`** and **`diversity`** are independent, configurable, parametrizable, and defaultable
  settings on one shared 6-point ordinal scale (`low < low_plus < medium < medium_plus < high <
  very_high`), defaulting to `medium_plus` (`config/base.yaml` `question_design`). `/generate-worksheet`
  can override either per run.
  - `difficulty` selects a `(start_rank, end_rank)` band on that scale; each question's difficulty
    ramps across the band based on its day's position in the week (Monday easier, Friday harder) and
    its position within the day (Q1 easier than Q10).
  - `diversity` selects a minimum distinct-skill count per day and how often (every Nth slot) a
    spiral-review skill is substituted into the rotating current-week skill sequence.
  - `question_plan.validate_progression(spec)` is the deterministic QA gate: difficulty must be both
    non-decreasing *and* net-increasing per day (a flat day fails), and distinct-skill count must meet
    the configured minimum.
- **`topic_overrides`** lets a run force a subset of a specific grade's *daily* questions onto a named
  topic — e.g. `grade_1:60%:Count on and Count down using add and subtract` means 60% of Grade 1's
  questions *every day this week*, not 60% of the week's total. Accepted as `grade:amount:topic`
  entries (percent or fixed count per day), semicolon-separated, parsed by
  `question_plan.parse_topic_overrides`. Override slots are spread evenly across the day (not
  clustered at the start/end) and still receive the same position-based difficulty as any other slot —
  overrides change which skill fills a slot, never the difficulty ramp. Default: no overrides.

`subject_module.MathSubjectModule.build_week_plan(...)` resolves all three into one slot-by-slot plan
(`{day_id: [{slot, skill, difficulty}, ...]}`) before authoring; `check_diversity_and_progression(spec)`
validates the authored result before it is persisted.

