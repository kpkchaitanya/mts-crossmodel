# Form Diversity - M0-M8 Feature Record

Status: In progress
Owner: MTS Math
Requested: 2026-08-30
Change type: Enhancement

## Intent and scope

Form Diversity prevents a worksheet from appearing repetitive when a skill occurs several times. It
keeps curriculum coverage, topic-override counts, and difficulty progression intact while varying the
mathematical action, representation, context, and response type used to assess a skill.

This feature is not a prewritten Grade 1-12 question bank. It uses reusable form families and compact
topic compatibility profiles. It begins with Grade 5 coordinate geometry. Existing Specs without form
metadata remain renderable and verifiable.

## Decisions

- The capability is named `form_diversity`.
- Its levels are `low`, `low_plus`, `medium`, `medium_plus`, `high`, and `very_high`; the configured
  default level is `high`.
- A generated run uses one persisted `variation_seed`; an explicit seed reproduces the same form plan.
- AI-assisted authoring supplies prompts within a selected form. Deterministic planning and QA select,
  record, and validate form use.
- `high` requires no repeated form family in a day and uses unused compatible forms before weekly reuse.
- The first activation boundary is Grade 5 coordinate geometry. Other topics preserve current behavior
  until their compatibility profile is added and tested.

## Acceptance criteria

1. Each planned profiled slot records `form_family`, `cognitive_action`, `representation`,
   `response_type`, and `variation_seed`.
2. The same inputs and seed reproduce an identical plan; a different seed may vary eligible forms.
3. At `high`, a form family does not repeat within a day and unused compatible forms are selected before
   weekly reuse.
4. A repeated skill in one day changes form family or representation.
5. Deterministic QA fails missing metadata, repeated daily forms, repeated skill/form combinations before
   the profile is exhausted, and normalized duplicate prompts.
6. Existing unprofiled topics and legacy Specs retain their existing behavior until a profile is enabled.

## M0-M8 status

| Milestone | Status | Evidence / next action |
|---|---|---|
| M0 | Complete | Seeded Grade 5 form-plan test and repeated coordinate-retrieval negative fixture pass. |
| M1 | Complete | Intent, vocabulary, scope, and exclusions in this record. |
| M2 | Complete | Acceptance criteria above; canonical requirements update remains in M5 change set. |
| M3 | Complete | Deterministic selector/validator; AI authoring; config and knowledge ownership decided. |
| M4 | Complete | Form metadata, compatibility profile, seeded algorithm, and failure rules defined below. |
| M5 | Complete | Config default, compact compatibility profile, planner, validator, Math module, schema, command, and runbook updated. |
| M6 | Complete | 24 focused planner, module, schema, and weekly integration tests pass. |
| M7 | Ready for review | Grade 5 staging-only worksheet run with explicit feature activation and normal human gates. |
| M8 | Not started | Review staging evidence and decide broader activation. |

## Detailed design

`config/base.yaml` owns feature level defaults. `subjects/math/knowledge/question-form-compatibility.json`
owns Math topic compatibility. `question_plan.py` assigns compatible forms to planned slots using a local
seeded random generator. It does not generate student wording. The canonical Spec stores selected form
metadata, and `validate_form_diversity` validates the authored result before Gate 2.

The selector uses an unused compatible form before reuse. It shuffles only equally eligible candidates
with `random.Random(variation_seed)`, making the result reproducible without requiring a large static
question bank. A missing profile returns no form assignment and preserves legacy behavior; a profiled
topic with no valid compatible form fails closed.

## Rollout and rollback

The initial profile is activated only for Grade 5 coordinate geometry. Remove the profile or pass
`form_diversity=low` to revert form assignment for a future run; no previously persisted or published
Spec is changed. A profile change invalidates planned Questions and downstream evidence for runs using it.