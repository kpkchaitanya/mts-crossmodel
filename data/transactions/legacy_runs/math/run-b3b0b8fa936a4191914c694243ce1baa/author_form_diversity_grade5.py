import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.extend([str(REPO / "src" / "runtime"), str(REPO / "subjects" / "math" / "src")])

import gates
import p0_runtime
import policy
import question_plan
import run_repository
import spec_repository
import subject_module
import weekly_workflow

RUN_ID = "run-b3b0b8fa936a4191914c694243ce1baa"
RUNS = REPO / "runs"


def arithmetic(prompt, expression):
    return {
        "prompt": prompt,
        "answer": p0_runtime.safe_number_expression(expression),
        "verification": {"method": "arithmetic_expression", "inputs": {"expression": expression}},
    }


def reasoning(prompt, answer, criterion):
    return {"prompt": prompt, "answer": answer, "verification": {"method": "reasoning_review", "criterion": criterion}}


def coordinate_question(form_family, number):
    coordinate_index = number // 5
    x, y = coordinate_index + 1, 1 + coordinate_index % 5
    label = chr(65 + number % 20)
    if form_family == "coordinate.read_component":
        component, answer = ("x", x) if number % 2 else ("y", y)
        return arithmetic(f"Point {label} is at ({x}, {y}). What is the {component}-coordinate?", str(answer))
    if form_family == "coordinate.write_ordered_pair":
        return reasoning(f"Write the ordered pair for point {label}, which is {x} units right of the y-axis and {y} units above the x-axis.", [x, y], "The coordinates are (x, y).")
    if form_family == "coordinate.axis_proximity":
        if x == y:
            x += 1
        answer = "x-axis" if y < x else "y-axis"
        return reasoning(f"Point {label} is at ({x}, {y}). Is it closer to the x-axis or the y-axis?", answer, "Compare the point's distances from each axis.")
    if form_family == "coordinate.translate_point":
        right, up = 1 + number % 3, 1 + (number + 1) % 3
        return reasoning(f"Move point {label} from ({x}, {y}) {right} units right and {up} units up. Write the new ordered pair.", [x + right, y + up], "Add the horizontal and vertical moves to the matching coordinates.")
    return reasoning(f"A point is {x} units right of the y-axis and {y} units above the x-axis. Write its ordered pair.", [x, y], "The horizontal distance is x and the vertical distance is y.")


def question_for(slot, number):
    skill = slot["skill"]
    if "form_family" in slot:
        question = coordinate_question(slot["form_family"], number)
        question.update({field: slot[field] for field in ("form_family", "cognitive_action", "representation", "response_type", "variation_seed")})
        return question
    if skill == "numerical expressions":
        left, right = number + 2, number + 1
        return arithmetic(f"Evaluate: {left} x ({right} + 3).", f"{left}*({right}+3)")
    if skill == "patterns":
        start, step = 5 + number, 2 + number
        return arithmetic(f"The pattern is {start}, {start + step}, {start + 2 * step}, ___. What is next?", f"{start}+3*{step}")
    if skill == "place value":
        return arithmetic(f"What is the value of the digit 6 in {60000 + 100 * number + 4}?", "60000")
    if skill == "whole-number multiplication":
        left, right = 12 + number, 4 + number
        return arithmetic(f"Solve: {left} x {right} = ___.", f"{left}*{right}")
    if skill == "multi-digit addition/subtraction":
        return arithmetic(f"Solve: {2450 + 10 * number} - {600 + number} = ___.", f"{2450 + 10 * number}-{600 + number}")
    left, right = 12 + 2 * number, 18 + 3 * number
    return arithmetic(f"Find the greatest common factor of {left} and {right}.", str(__import__("math").gcd(left, right)))


def main():
    repository = run_repository.RunRepository(RUNS)
    manifest_path = RUNS / "math" / RUN_ID / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["gates"] = {"mode": "bypass_all", "bypassed": list(gates.GATES), "requested_by": "current_user"}
    manifest = gates.record_approval(manifest, gate="scope_review", artifact_revision="scope-2026-08-24-r1", status="approved", reviewer="auto-bypass", notes="Explicit current-user instruction: All Gates Bypassed.")
    resolved = policy.resolve({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)
    math = subject_module.MathSubjectModule(REPO / "subjects" / "math")
    workflow = weekly_workflow.prepare_scope_review(resolved, on_date="2026-08-24", subject_module=math, grade_ids=["grade_5"])
    scope = workflow["worksheet_plans"][0]
    curriculum = scope["curriculum_scopes"][0]
    seed = manifest["question_design"]["variation_seed"]
    plan = math.build_week_plan(
        resolved["sections"], curriculum["topics"], curriculum["spiral"], scope["plan"]["questions_per_day"],
        difficulty=manifest["question_design"]["difficulty"], diversity=manifest["question_design"]["diversity"],
        topic_overrides=manifest["topic_overrides"]["grade_5"], form_diversity=manifest["question_design"]["form_diversity"],
        variation_seed=seed, grade_or_course="grade_5",
    )
    sections, number = [], 1
    for day in ("monday", "tuesday", "wednesday", "thursday", "friday"):
        questions = []
        for slot in plan[day]:
            question = question_for(slot, number)
            question.update({"number": number, "skill": slot["skill"], "difficulty": slot["difficulty"]})
            questions.append(question)
            number += 1
        sections.append({"id": day, "title": day.title(), "questions": questions})
    spec = {"worksheet": {"grade": "grade_5", "week_start": "2026-08-24", "question_count": 50, "duration_minutes": None, "title": "MTS - WEEKLY MATH WORKSHEET"}, "sections": sections, "verification": {"status": "PENDING"}}
    progression = math.check_diversity_and_progression(spec, diversity=manifest["question_design"]["diversity"])
    forms = math.check_form_diversity(spec, grade_or_course="grade_5", form_diversity=manifest["question_design"]["form_diversity"])
    if progression["status"] != "PASS" or forms["status"] != "PASS":
        raise RuntimeError({"progression": progression, "forms": forms})
    reference = spec_repository.SpecRepository(RUNS).write_revision(manifest, spec, worksheet_id="grade_5", revision="form-diversity-r2")
    manifest = repository.add_spec_reference(manifest, reference)
    manifest["question_plan"] = plan
    manifest["form_diversity_report"] = forms
    manifest["status"] = "questions_generated"
    repository.save_manifest(manifest)
    print(json.dumps({"run_id": RUN_ID, "spec_reference": reference, "progression": progression, "form_diversity": forms}, indent=2))


if __name__ == "__main__":
    main()