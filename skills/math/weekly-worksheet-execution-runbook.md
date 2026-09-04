# Runbook: Math Weekly Worksheet — Execution Steps

Self-contained execution reference. This is the only file you need to run a Math Weekly Worksheet
generation once `subject`, `worksheettype`, and `gates` are resolved by
[`/generate-worksheet`](../../../commands/generate-worksheet.md). Do not re-derive this sequence from
`specs/generate_math_worksheets/03. design/design.md`/`specs/generate_math_worksheets/01. intent/requirements.md` — those remain background rationale, not execution steps.
Every function below is real, tested code (see `tests/integration/test_weekly_math_lifecycle.py`).

## Module setup (do this once per run)

```python
import sys
from pathlib import Path

REPO = Path(r"c:\Users\neeli\kpkDevelopment\mts-crossmodel")
sys.path.insert(0, str(REPO / "src"))

from mts.setup_project.configure import resolve_effective_config
from mts.workflow_management import gates
from mts.workflow_management.run_loader import RunLoader
from mts.workflow_management.run_writer import RunWriter
from mts.worksheets.spec_writer import SpecWriter
from mts.infrastructure.google_docs.google_docs_adapter import GoogleDocsAdapter
from mts.subjects.math import subject_module, weekly_workflow, question_plan
```

## Gate IDs (must match `src/mts/workflow_management/gates.py` exactly)

| Gate id | Human name | Forward status |
|---|---|---|
| `scope_review` | Gate 1: Curriculum Scope Review | `worksheet_prepared` |
| `question_review` | Gate 2: Question Review | `verification_in_progress` |
| `verification_review` | Gate 3: Verification Review | `render_ready` |
| `formatting_review` | Gate 4: Formatting Review | `publish_approval_pending` |
| `publish_approval` | Gate 5: Publish Approval | `published` |

`gates=bypass all` (or `bypass <id>[,<id>...]`) means: do not stop and wait for the user at the listed
checkpoints. It does **not** mean skip `gates.record_approval(...)` — every gate still needs a
recorded approval entry for `gates.require_approval(...)` to advance, because `SpecWriter` and
`RunWriter` fail closed without it. When a gate is bypassed, record the approval yourself with
`reviewer="auto-bypass"` and note the user's explicit instruction in `notes`; never fabricate a human
reviewer name.

## Pre-run

1. Resolve effective config once: `effective_config = resolve_effective_config({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)`. This merges `data/config/project/base.yaml` + `data/config/subjects/math.yaml` + `data/config/worksheet_types/weekly_worksheet.yaml` and resolves the active template registration. It raises `EffectiveConfigError` if the worksheet type is not `status: active` or not compatible with the subject.
2. Resolve `week` against `data/config/project/base.yaml` `calendar.week_1_start` (`2026-08-17`, instructional week 1, a Monday):
   - `week=<n>` (integer): `on_date = week_1_start + timedelta(days=7 * (n - 1))`.
   - `week=current` (default): `today = date.today()` (project timezone); `on_date = p0_runtime.week_start_iso(today)` (Monday of the current calendar week); derive the instructional week number as `(on_date - week_1_start).days // 7 + 1` for reporting only.
   - `week=<ISO date>`: use the date as given; `p0_runtime.week_start_iso` still snaps it to that week's Monday before curriculum lookup.
   Resolve `grades` (default `all`) → `grade_ids = None` (every enabled grade/course); an explicit list/range (e.g. `1,4,5,6,9-10`) → `grade_ids = ["grade_1", "grade_4", "grade_5", "grade_6", "grade_9_10"]`.
3. Create/resume the run: `math = subject_module.MathSubjectModule()`; use `RunLoader`/`RunWriter` under `data/transactions/runs/<run_id>/` to persist `run_manifest.json`, `effective_config.json`, and `entity_references.json`.
4. Record the resolved `gates` decision on the manifest before proceeding (e.g. `manifest["gates"] = {"mode": "bypass_all", "bypassed": ["scope_review", "question_review", "verification_review", "formatting_review", "publish_approval"], "requested_by": "current_user"}`; `RunWriter.write_manifest(manifest)`).

## Run

5. Build the Gate 1 scope: `workflow = weekly_workflow.prepare_scope_review(effective_config, on_date=<resolved on_date>, subject_module=math, grade_ids=<resolved grade_ids>)`. Returns one plan per resolved grade/course (`grade_1`, `grade_4`, `grade_5`, `grade_6`, `grade_9_10` when `grades=all`), with `grade_9_10` pre-split into `math_1`/`math_2` per config.
6. **Gate 1 (`scope_review`)**: present `workflow["worksheet_plans"]` alongside the resolved instructional week number and `on_date` for approval. If not bypassed, stop and wait. Then `manifest = gates.record_approval(manifest, gate="scope_review", artifact_revision=<scope-revision-id>, status="approved", reviewer=<teacher-or-"auto-bypass">)`; `RunWriter.write_manifest(manifest)`; confirm `gates.require_approval(manifest, gate="scope_review", artifact_revision=<id>) == "worksheet_prepared"`.
7. Resolve `topic_overrides` once (if the user passed any): `topic_overrides_by_grade = question_plan.parse_topic_overrides(<raw topic_overrides string>)`. Resolve `form_diversity` (default `high`), generate one integer `variation_seed` when the user did not provide one, and persist both in the Run Manifest before authoring.
8. For each `plan_entry` in `workflow["worksheet_plans"]`:
   a. Build the authoring plan: `week_plan = math.build_week_plan(effective_config["sections"], primary_skills=<current-week topics for this grade>, spiral_skills=<current-week spiral topics for this grade>, slots_per_day=plan_entry["plan"]["questions_per_day"], difficulty=<resolved difficulty>, diversity=<resolved diversity>, topic_overrides=topic_overrides_by_grade.get(plan_entry["grade_or_course"]), form_diversity=<resolved form_diversity>, variation_seed=<persisted seed>, grade_or_course=plan_entry["grade_or_course"])`. `primary_skills`/`spiral_skills` come from the same curriculum scope already resolved in step 5 (`plan_entry["curriculum_scopes"]`, `topics`/`spiral` fields).
   b. Author the candidate question set (this step is agent reasoning, not deterministic code) as a dict shaped like `{"worksheet": {"grade": ..., "title": ..., "question_count": ...}, "sections": [{"id": "monday", "questions": [{"number", "prompt", "answer", "skill", "difficulty", "form_family", "cognitive_action", "representation", "response_type", "variation_seed", "verification": {"method", "inputs"}}, ...]}, ...], "verification": {"status": "PENDING"}}`, matching `plan_entry["plan"]["questions_per_week"]`/`questions_per_day` and the 5 weekday sections. Tag every question's `skill`/`difficulty` and, when the planned slot has form metadata, every Form Diversity field to match its planned slot.
   c. `spec = math.build_spec(plan_entry["plan"], {"spec": <candidate>})`.
   d. **Diversity/progression QA**: `progression = math.check_diversity_and_progression(spec, diversity=<resolved diversity>)`; must be `status == "PASS"` before persisting — this requires difficulty to be non-decreasing *and* net-increasing across the day (a flat, all-one-tier day fails) plus the configured minimum distinct-skill count. **Form Diversity QA**: `forms = math.check_form_diversity(spec, grade_or_course=plan_entry["grade_or_course"], form_diversity=<resolved form_diversity>)`; must also be `status == "PASS"`. If either fails, revise the authored questions and recheck — do not persist or silently pass a `FAIL`.
   e. Persist it immutably under `data/transactions/subjects/<subject>/grades/<grade>/cycles/<cycle>/batches/<batch>/worksheets/<worksheet_type>/specs/` with `SpecWriter`; update `entity_references.json` with the written path.
   f. **Gate 2 (`question_review`)**: present questions for approval unless bypassed. `manifest = gates.record_approval(manifest, gate="question_review", artifact_revision=<questions-revision-id>, status="approved", reviewer=...)`; `RunWriter.write_manifest(manifest)`; this call raises if the run lacks persisted Spec references, so step 8e must run first.
   g. Verify deterministically: `verification = math.verify_spec(spec)`. Manually recompute/reason through anything flagged `REASONING_REQUIRED`; never treat the generated answer as its own proof. Set `spec["verification"]["status"] = verification["status"]`.
   h. **Gate 3 (`verification_review`)**: present the verification summary unless bypassed, then record approval the same way as steps 6/8f.
   i. Render: `adapter = google_docs_adapter.GoogleDocsAdapter(drive_client, docs_client)`; `rendered = adapter.render_pair(spec, {"student_template_id": ..., "answer_key_template_id": ...}, staging_folder_id, {"student_worksheet": <name>, "answer_key": <name>}, {"student_worksheet": <projection text>, "answer_key": <projection text with answers>})`. `render_pair` raises unless `spec["verification"]["status"] == "PASS"`. In Copilot context this always targets the `outputs-copilot/` staging Drive folder, never a final destination.

   Document names are **not** free choice. Derive both from configuration:
   `student, key = mts.publishing.deliver.document_names(effective_config["naming"]["weekly"], grade_id, week_of)`.
   Folder-anchored Final Delivery pairs staged documents back to grades by these names, so an ad-hoc
   name renders a worksheet undeliverable until it is renamed.

   **No document without a Spec.** Never author question or answer text straight into a Drive
   document. Persist the Spec revision first, render from it, and stamp the result with
   `adapter.stamp_document(id, mts.publishing.deliver.provenance_properties(...))`. An unstamped
   document has no run, Spec, or verification behind it, cannot be regenerated or corrected by any
   tool here, and is reported by delivery as `missing_provenance`. Recovering one requires
   `/format-and-deliver-worksheets`, which reconstructs a Spec by parsing the document — inference
   that the authoring step could have made unnecessary.
   j. QA the rendered text: `qa = math.validate_subject_output({"student_worksheet": <rendered student text>, "answer_key": <rendered key text>}, spec)`; both must report `status == "PASS"`. This is required regardless of gate bypass.
   k. **Gate 4 (`formatting_review`)**: present QA results unless bypassed, then record approval.
9. After all plans reach `formatting_review` approval, set `manifest["status"] = "publish_approval_pending"` and `RunWriter.write_manifest(manifest)`.

## Post-run

10. **Gate 5 (`publish_approval`)**: present the full batch (all grades/courses, staged Drive links) for final approval unless bypassed, then `manifest = gates.record_approval(manifest, gate="publish_approval", artifact_revision=<batch-revision-id>, status="approved", reviewer=...)`.
11. Resolve `publish` (default `yes` per `data/config/project/base.yaml` `publishing.default_publish`): once step 10's approval is recorded, `publish=yes` (default) immediately runs `adapter.publish_pair(student_artifact, answer_key_artifact, final_destination_id)` per grade/course, moving staged documents into `outputs/math/`. `publish=no` stops here and leaves artifacts staged only. Never call `publish_pair` before step 10's approval is recorded, even when `gates=bypass all` — bypass skips the stop-and-wait UI step, not the recorded approval itself.
12. Persist final manifest status (`"status": "published"` when published this run, otherwise `"status": "publish_approval_pending"` when `publish=no`), telemetry, and output links; `RunWriter.write_manifest(manifest)`.
13. **Final Delivery** (audience-facing). Resolve `deliver` (default `yes` per `data/config/project/base.yaml` `publishing.final_delivery.default_deliver`); `deliver=no` ends the run here, and `deliver=yes` with `publish=no` is a refused combination, not a silent downgrade. Staging is everything up to and including step 11; Final Delivery distributes the published pair to parents and runs only after step 10's `publish_approval` is recorded. Per grade: `week_folder = adapter.ensure_child_folder(<parent folder id from data/config/subjects/math.yaml `publishing.final_delivery.destinations_by_grade`>, effective_config["publishing"]["final_delivery"]["week_folder_pattern"].replace("{{WEEK_OF}}", <ISO Monday>))`, then `adapter.deliver_pair(student_artifact, answer_key_artifact, week_folder["id"], mode=<configured mode>, deliver_answer_key=<configured flag>)`. `ensure_child_folder` is idempotent, so re-delivering a week reuses its folder instead of creating a duplicate. Default `mode: copy` leaves staging intact as the audit trail. `scripts/deliver_weekly_worksheets.py --run-root data/transactions/runs/<run_id> --week-of <ISO date|week number|current>` performs this for a whole batch and writes delivery evidence; add `--dry-run` to review the grade -> folder mapping first. Never deliver an artifact that has not passed verification, visual QA, and Gate 5.
14. Report a compact summary back to the user: worksheets generated, grades/week resolved, gates bypassed (explicit list), the `publish` and `deliver` decisions, topic overrides applied, verification/QA outcomes, and Drive links (staged, published, and delivered).

## Fast-path reminders

- One `data/transactions/runs/<run_id>/run_manifest.json` per run; do not hand-edit the manifest's request or effective config snapshot.
- `SpecWriter.write_revision` enforces immutability: writing a different payload to an existing `revision` path raises. Use a new `revision` id for edits.
- `scripts/prepare_weekly_spec.py --source <path> --destination <path> --grade-id <id>` is an optional CLI alternative to steps 8b–8e for building a spec from a larger source question bank; it still requires manual verification/QA afterward.
- `scripts/render_weekly_specs_to_drive.py` is a standalone reference implementation of step 8i/10 for ad hoc Drive rendering outside this in-process flow; prefer `google_docs_adapter.GoogleDocsAdapter` directly when already in a Python session.
- `scripts/deliver_weekly_worksheets.py` reads a run's `published-artifacts.json` (falling back to `rendered-artifacts.json`) and is the batch entry point for step 13. It refuses any grade with no configured Final Delivery parent folder.

## Run-mode failure and change control

During a worksheet-generation run, treat shared source code, configuration, master templates, and
canonical workflow documents as immutable operational infrastructure. Do not repair, refactor, or
otherwise edit them while executing a run unless the current user explicitly authorizes the proposed
change. This applies even when a failed check reveals an apparent local implementation defect.

On any execution, verification, rendering, QA, authentication, or publication failure:

1. Stop the affected run step before retrying or creating replacement artifacts.
2. Report the observed issue and supporting evidence, the affected run/artifact state, and any
   produced-but-invalid staged artifacts.
3. Identify the exact file or external dependency involved, the smallest proposed change, its gate
   invalidation impact, and the focused validation that would be run after approval.
4. Wait for the user's explicit approval before modifying shared code, configuration, templates, or
   canonical workflow documents. A request to continue a run does not itself authorize such changes.
5. Keep operational evidence under `runs/math/<run_id>/` only. Run-local files may record commands,
   diagnostics, and QA evidence, but may not silently alter the approved workflow, policy, or gate
   requirements.

After an approved build-mode change, rerun only the affected validation and apply the normal
revision/invalidation contract before resuming the run. Never substitute an auto-bypass approval for
required verification or visual QA.