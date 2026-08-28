# Runbook: Math Weekly Worksheet — Execution Steps

Self-contained execution reference. This is the only file you need to run a Math Weekly Worksheet
generation once `subject`, `worksheettype`, and `gates` are resolved by
[`/generate-worksheet`](../../../commands/generate-worksheet.md). Do not re-derive this sequence from
`specs/generate_math_worksheets/03. design/design.md`/`docs/requirements.md` — those remain background rationale, not execution steps.
Every function below is real, tested code (see `tests/integration/test_weekly_math_lifecycle.py`).

## Module setup (do this once per run)

```python
import sys
from pathlib import Path

REPO = Path(r"c:\Users\neeli\kpkDevelopment\mts-crossmodel")
sys.path.insert(0, str(REPO / "src" / "runtime"))     # policy, gates, run_repository, spec_repository
sys.path.insert(0, str(REPO / "src" / "rendering"))   # google_docs_adapter
sys.path.insert(0, str(REPO / "subjects" / "math" / "src"))  # subject_module, weekly_workflow, p0_runtime, question_plan

import gates, policy, run_repository, spec_repository, google_docs_adapter
import subject_module, weekly_workflow, question_plan
```

## Gate IDs (must match `src/runtime/gates.py` exactly)

| Gate id | Human name | Forward status |
|---|---|---|
| `scope_review` | Gate 1: Curriculum Scope Review | `worksheet_prepared` |
| `question_review` | Gate 2: Question Review | `verification_in_progress` |
| `verification_review` | Gate 3: Verification Review | `render_ready` |
| `formatting_review` | Gate 4: Formatting Review | `publish_approval_pending` |
| `publish_approval` | Gate 5: Publish Approval | `published` |

`gates=bypass all` (or `bypass <id>[,<id>...]`) means: do not stop and wait for the user at the listed
checkpoints. It does **not** mean skip `gates.record_approval(...)` — every gate still needs a
recorded approval entry for `gates.require_approval(...)` to advance, because `spec_repository` and
`run_repository` fail closed without it. When a gate is bypassed, record the approval yourself with
`reviewer="auto-bypass"` and note the user's explicit instruction in `notes`; never fabricate a human
reviewer name.

## Pre-run

1. Resolve policy once: `resolved_policy = policy.resolve({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)`. This merges `config/base.yaml` + `config/math.yaml` + `config/worksheet-types/weekly-worksheet.yaml` and resolves the active template registration. It raises `PolicyError` if the worksheet type is not `status: active` or not compatible with the subject.
2. Resolve `week` against `config/base.yaml` `calendar.week_1_start` (`2026-08-17`, instructional week 1, a Monday):
   - `week=<n>` (integer): `on_date = week_1_start + timedelta(days=7 * (n - 1))`.
   - `week=current` (default): `today = date.today()` (project timezone); `on_date = p0_runtime.week_start_iso(today)` (Monday of the current calendar week); derive the instructional week number as `(on_date - week_1_start).days // 7 + 1` for reporting only.
   - `week=<ISO date>`: use the date as given; `p0_runtime.week_start_iso` still snaps it to that week's Monday before curriculum lookup.
   Resolve `grades` (default `all`) → `grade_ids = None` (every enabled grade/course); an explicit list/range (e.g. `1,4,5,6,9-10`) → `grade_ids = ["grade_1", "grade_4", "grade_5", "grade_6", "grade_9_10"]`.
3. Create/resume the run: `math = subject_module.MathSubjectModule(REPO / "subjects" / "math")`; `repo = run_repository.RunRepository(REPO / "runs")`; `manifest = repo.create_or_resume({"subject": "math", "worksheet_type": "weekly-worksheet"}, resolved_policy, run_id=<chosen-run-id>)`.
4. Record the resolved `gates` decision on the manifest before proceeding (e.g. `manifest["gates"] = {"mode": "bypass_all", "bypassed": ["scope_review", "question_review", "verification_review", "formatting_review", "publish_approval"], "requested_by": "current_user"}`; `repo.save_manifest(manifest)`).

## Run

5. Build the Gate 1 scope: `workflow = weekly_workflow.prepare_scope_review(resolved_policy, on_date=<resolved on_date>, subject_module=math, grade_ids=<resolved grade_ids>)`. Returns one plan per resolved grade/course (`grade_1`, `grade_4`, `grade_5`, `grade_6`, `grade_9_10` when `grades=all`), with `grade_9_10` pre-split into `math_1`/`math_2` per config.
6. **Gate 1 (`scope_review`)**: present `workflow["worksheet_plans"]` alongside the resolved instructional week number and `on_date` for approval. If not bypassed, stop and wait. Then `manifest = gates.record_approval(manifest, gate="scope_review", artifact_revision=<scope-revision-id>, status="approved", reviewer=<teacher-or-"auto-bypass">)`; `repo.save_manifest(manifest)`; confirm `gates.require_approval(manifest, gate="scope_review", artifact_revision=<id>) == "worksheet_prepared"`.
7. Resolve `topic_overrides` once (if the user passed any): `topic_overrides_by_grade = question_plan.parse_topic_overrides(<raw topic_overrides string>)`.
8. For each `plan_entry` in `workflow["worksheet_plans"]`:
   a. Build the authoring plan: `week_plan = math.build_week_plan(resolved_policy["sections"], primary_skills=<current-week topics for this grade>, spiral_skills=<current-week spiral topics for this grade>, slots_per_day=plan_entry["plan"]["questions_per_day"], difficulty=<resolved difficulty>, diversity=<resolved diversity>, topic_overrides=topic_overrides_by_grade.get(plan_entry["grade_or_course"]))`. `primary_skills`/`spiral_skills` come from the same curriculum scope already resolved in step 5 (`plan_entry["curriculum_scopes"]`, `topics`/`spiral` fields).
   b. Author the candidate question set (this step is agent reasoning, not deterministic code) as a dict shaped like `{"worksheet": {"grade": ..., "title": ..., "question_count": ...}, "sections": [{"id": "monday", "questions": [{"number", "prompt", "answer", "skill", "difficulty", "verification": {"method", "inputs"}}, ...]}, ...], "verification": {"status": "PENDING"}}`, matching `plan_entry["plan"]["questions_per_week"]`/`questions_per_day` and the 5 weekday sections. Tag each question's `skill`/`difficulty` to match its planned slot in `week_plan[<day_id>][<slot_index>]`.
   c. `spec = math.build_spec(plan_entry["plan"], {"spec": <candidate>})`.
   d. **Diversity/progression QA**: `progression = math.check_diversity_and_progression(spec, diversity=<resolved diversity>)`; must be `status == "PASS"` before persisting — this requires difficulty to be non-decreasing *and* net-increasing across the day (a flat, all-one-tier day fails) plus the configured minimum distinct-skill count. If `FAIL`, revise the authored questions (skill tagging or difficulty ordering) and recheck — do not persist or silently pass a `FAIL`.
   e. Persist it immutably: `spec_repo = spec_repository.SpecRepository(REPO / "runs")`; `ref = spec_repo.write_revision(manifest, spec, worksheet_id=plan_entry["grade_or_course"], revision=<revision-id>)`; `manifest = repo.add_spec_reference(manifest, ref)`.
   f. **Gate 2 (`question_review`)**: present questions for approval unless bypassed. `manifest = gates.record_approval(manifest, gate="question_review", artifact_revision=<questions-revision-id>, status="approved", reviewer=...)`; `repo.save_manifest(manifest)`; this call raises if `manifest["spec_references"]` is empty (Gate 2 fails closed on missing Spec references), so step 8e must run first.
   g. Verify deterministically: `verification = math.verify_spec(spec)`. Manually recompute/reason through anything flagged `REASONING_REQUIRED`; never treat the generated answer as its own proof. Set `spec["verification"]["status"] = verification["status"]`.
   h. **Gate 3 (`verification_review`)**: present the verification summary unless bypassed, then record approval the same way as steps 6/8f.
   i. Render: `adapter = google_docs_adapter.GoogleDocsAdapter(drive_client, docs_client)`; `rendered = adapter.render_pair(spec, {"student_template_id": ..., "answer_key_template_id": ...}, staging_folder_id, {"student_worksheet": <name>, "answer_key": <name>}, {"student_worksheet": <projection text>, "answer_key": <projection text with answers>})`. `render_pair` raises unless `spec["verification"]["status"] == "PASS"`. In Copilot context this always targets the `outputs-copilot/` staging Drive folder, never a final destination.
   j. QA the rendered text: `qa = math.validate_subject_output({"student_worksheet": <rendered student text>, "answer_key": <rendered key text>}, spec)`; both must report `status == "PASS"`. This is required regardless of gate bypass.
   k. **Gate 4 (`formatting_review`)**: present QA results unless bypassed, then record approval.
9. After all plans reach `formatting_review` approval, set `manifest["status"] = "publish_approval_pending"` and `repo.save_manifest(manifest)`.

## Post-run

10. **Gate 5 (`publish_approval`)**: present the full batch (all grades/courses, staged Drive links) for final approval unless bypassed, then `manifest = gates.record_approval(manifest, gate="publish_approval", artifact_revision=<batch-revision-id>, status="approved", reviewer=...)`.
11. Resolve `publish` (default `yes` per `config/base.yaml` `publishing.default_publish`): once step 10's approval is recorded, `publish=yes` (default) immediately runs `adapter.publish_pair(student_artifact, answer_key_artifact, final_destination_id)` per grade/course, moving staged documents into `outputs/math/`. `publish=no` stops here and leaves artifacts staged only. Never call `publish_pair` before step 10's approval is recorded, even when `gates=bypass all` — bypass skips the stop-and-wait UI step, not the recorded approval itself.
12. Persist final manifest status (`"status": "published"` when published this run, otherwise `"status": "publish_approval_pending"` when `publish=no`), telemetry, and output links; `repo.save_manifest(manifest)`.
13. Report a compact summary back to the user: worksheets generated, grades/week resolved, gates bypassed (explicit list), the `publish` decision, topic overrides applied, verification/QA outcomes, and Drive links (staged and/or published).

## Fast-path reminders

- One `runs/math/<run_id>/run-manifest.json` per run; `RunRepository.create_or_resume` fails if a resumed run's request/policy fingerprint doesn't match — don't hand-edit the manifest's `request`/policy snapshot.
- `SpecRepository.write_revision` enforces immutability: writing a different payload to an existing `revision` path raises. Use a new `revision` id for edits.
- `scripts/prepare_weekly_spec.py --source <path> --destination <path> --grade-id <id>` is an optional CLI alternative to steps 8b–8e for building a spec from a larger source question bank; it still requires manual verification/QA afterward.
- `scripts/render_weekly_specs_to_drive.py` is a standalone reference implementation of step 8i/10 for ad hoc Drive rendering outside this in-process flow; prefer `google_docs_adapter.GoogleDocsAdapter` directly when already in a Python session.