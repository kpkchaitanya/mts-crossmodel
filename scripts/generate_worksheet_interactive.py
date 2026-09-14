"""Gate-preserving interactive runner for Math Weekly Worksheets."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import generate_worksheet as batch
from mts.setup_project.configure import resolve_effective_config
from mts.subjects.math.generation import MathGeneration
from mts.subjects.math.question_plan import parse_topic_overrides
from mts.subjects.math.weekly_workflow import prepare_scope_review
from mts.workflow_management import gates
from mts.workflow_management.run_writer import RunWriter

GATE_NAMES = {
    "scope_review": "Gate 1: Curriculum Scope Review",
    "question_review": "Gate 2: Question Review",
    "verification_review": "Gate 3: Verification Review",
    "formatting_review": "Gate 4: Formatting Review",
    "publish_approval": "Gate 5: Publish Approval",
}


def approve(manifest: dict[str, Any], gate_id: str, revision: str, summary: str) -> dict[str, Any]:
    print(f"\n{GATE_NAMES[gate_id]}\n{summary}")
    if input("Approve this gate? [y/N]: ").strip().lower() not in {"y", "yes"}:
        raise RuntimeError(f"{GATE_NAMES[gate_id]} was not approved.")
    return gates.record_approval(
        manifest,
        gate=gate_id,
        artifact_revision=revision,
        status="approved",
        reviewer="current-user",
    )


def generate_interactive(params: dict[str, str]) -> dict[str, Any]:
    subject = params.get("subject", "math")
    worksheet_type = batch.WORKSHEET_TYPE_ALIASES.get(params.get("worksheettype", "weekly"), params.get("worksheettype", "weekly"))
    if subject != "math" or worksheet_type != "weekly-worksheet":
        raise ValueError("The interactive runner currently supports subject=math worksheettype=weekly.")
    config = resolve_effective_config({"subject": subject, "worksheet_type": worksheet_type}, repository_root=REPO)
    publish = batch.bool_param(params.get("publish"), default=bool(config["publishing"]["default_publish"]))
    deliver = batch.bool_param(params.get("deliver"), default=bool(config["publishing"]["final_delivery"]["default_deliver"]))
    if deliver and not publish:
        raise ValueError("deliver=yes requires publish=yes.")
    week = batch.resolve_week(params.get("week", "current"), config["calendar"])
    grades = batch.resolve_grades(params.get("grades"))
    overrides = parse_topic_overrides(params.get("topic_overrides"))
    difficulty = batch.configured_level(params, config, "difficulty")
    diversity = batch.configured_level(params, config, "diversity")
    form_diversity = batch.configured_level(params, config, "form_diversity")
    seed = batch.variation_seed(params)
    run_id = params.get("run") or f"run-{week}-weekly-interactive"
    batch_id = f"weekly_math_{week.replace('-', '_')}_interactive"
    writer = RunWriter(REPO / "data")
    manifest: dict[str, Any] = {
        "run_id": run_id, "subject": subject, "worksheet_type": worksheet_type,
        "week_start": week, "status": "initialized",
        "gates": {"mode": "interactive", "bypassed": [], "requested_by": "current_user"},
        "verification_required": True, "qa_required": True, "variation_seed": seed,
        "publish": publish, "deliver": deliver, "topic_overrides": overrides or {},
    }
    writer.write_manifest(manifest)
    math = MathGeneration()
    scope = prepare_scope_review(config, on_date=week, subject_module=math, grade_ids=grades)
    counts = "; ".join(f"{p['grade_or_course']}={p['plan']['questions_per_week']} questions" for p in scope["worksheet_plans"])
    manifest = approve(manifest, "scope_review", f"scope-{week}", f"Week of {week}; {counts}")
    manifest["status"] = "worksheet_prepared"
    writer.write_manifest(manifest)

    references = []
    specs = []
    for entry in scope["worksheet_plans"]:
        grade = entry["grade_or_course"]
        plan = batch.build_question_plan(
            math=math, plan_entry=entry, effective_config=config,
            difficulty=difficulty, diversity=diversity, form_diversity=form_diversity,
            seed=seed, topic_overrides=overrides.get(grade),
        )
        spec = math.build_spec(entry["plan"], {"spec": batch.candidate_spec_from_question_plan(plan, week)})
        batch.validate_spec_matches_question_plan(spec, plan)
        progression = math.check_diversity_and_progression(spec, diversity=diversity)
        forms = math.check_form_diversity(spec, grade_or_course=grade, form_diversity=form_diversity)
        if progression["status"] != "PASS" or forms["status"] != "PASS":
            raise ValueError(f"Planning QA failed for {grade}: {progression}; {forms}")
        verification = math.verify_spec(spec)
        if verification["status"] != "PASS":
            raise ValueError(f"Verification failed for {grade}: {verification}")
        spec["verification"]["status"] = "PASS"
        numbering = config.get("display_numbering", "global")
        qa = math.validate_subject_output(
            {"student_worksheet": batch.projection(spec, numbering=numbering), "answer_key": batch.projection(spec, answer_key=True, numbering=numbering)},
            spec, numbering=numbering,
        )
        if qa["student_worksheet"]["status"] != "PASS" or qa["answer_key"]["status"] != "PASS":
            raise ValueError(f"QA failed for {grade}: {qa}")
        root = batch.transaction_root(grade, week, batch_id, worksheet_type)
        batch.write_json(root / "question_plan.json", plan)
        batch.write_json(root / "specs" / "r1.json", spec)
        batch.write_json(root / "verification" / "verification-r1.json", verification)
        batch.write_json(root / "qa" / "student_worksheet.json", qa["student_worksheet"])
        batch.write_json(root / "qa" / "answer_key.json", qa["answer_key"])
        references.append({"grade_or_course": grade, "worksheet_root": root.relative_to(REPO).as_posix(), "spec": (root / "specs" / "r1.json").relative_to(REPO).as_posix()})
        specs.append(spec)

    writer.write_effective_config(run_id, config)
    writer.write_entity_references(run_id, {"references": references})
    manifest["entity_references"] = references
    manifest["status"] = "questions_generated"
    writer.write_manifest(manifest)
    manifest = approve(manifest, "question_review", f"questions-{week}", f"Persisted specs: {len(specs)} worksheets.")
    manifest["status"] = "verification_in_progress"
    writer.write_manifest(manifest)
    manifest = approve(manifest, "verification_review", f"verification-{week}", "Independent verification passed for every question.")
    manifest["status"] = "render_ready"
    writer.write_manifest(manifest)

    subprocess.run([batch.operational_python(), "scripts/render_weekly_specs_to_drive.py", "--run-root", f"data/transactions/runs/{run_id}", "--date", week], cwd=REPO, check=True)
    manifest["status"] = "rendered_to_staging"
    writer.write_manifest(manifest)
    manifest = approve(manifest, "formatting_review", f"formatting-{week}", "Rendered artifacts are ready for formatting review.")
    manifest["status"] = "publish_approval_pending"
    writer.write_manifest(manifest)
    manifest = approve(manifest, "publish_approval", f"publish-{week}", "Final worksheet and answer-key pairs are ready to publish.")
    subprocess.run([batch.operational_python(), "scripts/publish_weekly_artifacts.py", "--run-root", f"data/transactions/runs/{run_id}"], cwd=REPO, check=True)
    manifest["status"] = "published"
    writer.write_manifest(manifest)
    if deliver:
        subprocess.run([batch.operational_python(), "scripts/deliver_weekly_worksheets.py", "--run-root", f"data/transactions/runs/{run_id}", "--week-of", week], cwd=REPO, check=True)
        manifest["status"] = "delivered"
        writer.write_manifest(manifest)
    return {"run_id": run_id, "week_start": week, "worksheets": len(specs), "status": manifest["status"]}


if __name__ == "__main__":
    result = generate_interactive(batch.parse_key_value_args(sys.argv[1:]))
    print(f"GENERATE_WORKSHEET_INTERACTIVE_PASS {result['run_id']} week={result['week_start']} worksheets={result['worksheets']} status={result['status']}")