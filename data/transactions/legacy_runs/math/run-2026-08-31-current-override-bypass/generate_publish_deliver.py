import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUN_ID = Path(__file__).resolve().parent.name
RUNS = REPO / "runs"
RUN_ROOT = RUNS / "math" / RUN_ID
WEEK_OF = "2026-08-31"
STAGING_FOLDER = "1FUZ5hC4hpKEZwirG-p4bKpDlPiN8IBfL"
FINAL_FOLDER = "1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS"
TOKEN_PATH = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]
GATE_IDS = ["scope_review", "question_review", "verification_review", "formatting_review", "publish_approval"]
DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday"]

RAW_USER_TOPIC_OVERRIDES = (
    "grade_1:33%:Count on and Count down using add and substract; "
    "grade_4:20%:data and graphing basics; "
    "grade_5:20%:coordinate geometry basics; "
    "grade_6:20%:prime factorization basics"
)
EFFECTIVE_TOPIC_OVERRIDES = RAW_USER_TOPIC_OVERRIDES.replace("substract", "subtract")
VARIATION_SEED = 2026083101
REVISION = "r2"

sys.path.extend([
    str(REPO / "src" / "runtime"),
    str(REPO / "src" / "rendering"),
    str(REPO / "subjects" / "math" / "src"),
    str(REPO / "scripts"),
])

import gates
import google_docs_adapter
import p0_runtime
import policy
import question_plan
import render_weekly_specs_to_drive as renderer
import run_repository
import spec_repository
import subject_module
import weekly_workflow


SKILL_BASIS = {
    "grade_1": {
        "primary": [
            "Count on and count down using addition and subtraction",
            "addition and subtraction within 20",
            "unknown-addend and unknown-subtrahend equations",
        ],
        "spiral": ["counting sequence", "compare numbers"],
    },
    "grade_4": {
        "primary": ["data and graphing basics", "multi-digit place value", "compare multi-digit numbers", "addition and subtraction"],
        "spiral": ["multiplication facts", "rounding"],
    },
    "grade_5": {
        "primary": ["coordinate geometry basics", "numerical expressions", "patterns", "whole-number multiplication"],
        "spiral": ["place value", "multi-digit operations"],
    },
    "grade_6": {
        "primary": ["prime factorization basics", "factor pairs and multiples", "ratio concepts", "ratio reasoning"],
        "spiral": ["fractions and decimals", "coordinate plane"],
    },
    "grade_9_10": {
        "primary": [
            "solve linear equations and inequalities",
            "create equations from contexts",
            "function notation and evaluation",
            "simplify expressions",
            "rational exponents and radicals",
        ],
        "spiral": ["slope", "transformations", "polynomial operations"],
    },
}


def arithmetic(prompt, expression):
    return {
        "prompt": prompt,
        "answer": p0_runtime.safe_number_expression(expression),
        "verification": {"method": "arithmetic_expression", "inputs": {"expression": expression}},
    }


def gcf(prompt, left, right):
    return {
        "prompt": prompt,
        "answer": p0_runtime.compute("gcf", {"a": left, "b": right}),
        "verification": {"method": "gcf", "inputs": {"a": left, "b": right}},
    }


def midpoint(prompt, x1, y1, x2, y2):
    return {
        "prompt": prompt,
        "answer": p0_runtime.compute("midpoint", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}),
        "verification": {"method": "midpoint", "inputs": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}},
    }


def coordinate_question(number, slot):
    index = number + 2
    form = slot.get("form_family", "coordinate.read_component")
    x = index % 8
    y = 2 + index % 7
    if form == "coordinate.write_ordered_pair":
        return midpoint(f"Item {number}: Find the midpoint of A({x}, {y}) and B({x + 4}, {y + 6}).", x, y, x + 4, y + 6)
    if form == "coordinate.axis_proximity":
        return arithmetic(f"Item {number}: Point P is at ({x}, {-y}). What is its distance from the x-axis?", str(y))
    if form == "coordinate.translate_point":
        shift = 1 + index % 4
        rise = 2 + index % 3
        return arithmetic(f"Item {number}: Point A is at ({x}, {y}). Move it {shift} right and {rise} up. What is the new y-coordinate?", f"{y}+{rise}")
    if form == "coordinate.verbal_location":
        return arithmetic(f"Item {number}: Start at the origin, move {x} units right and {y} units up. What is the y-coordinate?", str(y))
    return arithmetic(f"Item {number}: Point P is at ({x}, {y}). What is the y-coordinate of P?", str(y))


def question_for(grade, slot, number):
    skill = slot["skill"]
    index = number + 2
    lead = f"Item {number}: "
    if grade == "grade_1":
        if skill.startswith("Count on"):
            start, steps = 4 + index % 6, 1 + index % 4
            if number % 2:
                return arithmetic(f"{lead}Start at {start}. Count on {steps}. What number do you say?", f"{start}+{steps}")
            return arithmetic(f"{lead}Start at {start + steps}. Count down {steps}. What number do you say?", f"{start + steps}-{steps}")
        if skill == "addition and subtraction within 20":
            left, right = 5 + index % 8, 2 + index % 5
            return arithmetic(f"{lead}Solve: {left} + {right} = ___.", f"{left}+{right}")
        if skill == "unknown-addend and unknown-subtrahend equations":
            total, addend = 12 + index % 8, 3 + index % 6
            return arithmetic(f"{lead}Find the missing number: ___ + {addend} = {total}.", f"{total}-{addend}")
        if skill == "counting sequence":
            return arithmetic(f"{lead}What number comes after {8 + index}?", f"{8 + index}+1")
        return arithmetic(f"{lead}Which number is greater: {10 + index} or {9 + index}? Write the greater number.", f"{10 + index}")

    if grade == "grade_4":
        if skill == "data and graphing basics":
            apples, pears, bananas = 8 + index, 5 + index % 4, 6 + index % 3
            return arithmetic(f"{lead}A bar graph shows {apples} apples, {pears} pears, and {bananas} bananas. How many apples and pears are shown altogether?", f"{apples}+{pears}")
        if skill == "multi-digit place value":
            value = 3000 + 100 * (index % 6)
            return arithmetic(f"{lead}What is the value of the digit 3 in {value + 450}?", "3000")
        if skill == "compare multi-digit numbers":
            larger = 4200 + 10 * index
            return arithmetic(f"{lead}Which number is greater: {larger} or {larger - 19}? Write the greater number.", str(larger))
        if skill == "addition and subtraction":
            left, right = 1200 + 13 * index, 300 + 7 * index
            return arithmetic(f"{lead}Solve: {left} - {right} = ___.", f"{left}-{right}")
        if skill == "multiplication facts":
            return arithmetic(f"{lead}Solve: {3 + index % 6} x {4 + index % 5} = ___.", f"{3 + index % 6}*{4 + index % 5}")
        return arithmetic(f"{lead}Round {1240 + 10 * index} to the nearest hundred.", str(round((1240 + 10 * index) / 100) * 100))

    if grade == "grade_5":
        if skill == "coordinate geometry basics":
            return coordinate_question(number, slot)
        if skill == "numerical expressions":
            left, right = 3 + index % 5, 4 + index % 4
            return arithmetic(f"{lead}Evaluate: {left} x ({right} + 2).", f"{left}*({right}+2)")
        if skill == "patterns":
            start, step = 4 + index, 3 + index % 4
            return arithmetic(f"{lead}The pattern is {start}, {start + step}, {start + 2 * step}, ___. What is next?", f"{start}+3*{step}")
        if skill == "whole-number multiplication":
            left, right = 12 + index, 6 + index % 5
            return arithmetic(f"{lead}Solve: {left} x {right} = ___.", f"{left}*{right}")
        if skill == "place value":
            return arithmetic(f"{lead}What is the value of the digit 6 in {60000 + 100 * index + 4}?", "60000")
        return arithmetic(f"{lead}Solve: {2500 + 20 * index} + {700 + index} = ___.", f"{2500 + 20 * index}+{700 + index}")

    if grade == "grade_6":
        if skill == "prime factorization basics":
            prime_sets = [(2, 2, 3), (2, 3, 5), (2, 2, 5), (3, 3, 2)]
            factors = prime_sets[index % len(prime_sets)]
            expression = "*".join(map(str, factors))
            return arithmetic(f"{lead}The prime factors {' x '.join(map(str, factors))} multiply to what number?", expression)
        if skill == "factor pairs and multiples":
            left, right = 12 + 2 * (index % 5), 18 + 3 * (index % 5)
            return gcf(f"{lead}Find the greatest common factor of {left} and {right}.", left, right)
        if skill == "ratio concepts":
            red, blue = 2 + index % 3, 3 + index % 4
            return arithmetic(f"{lead}A bag has {red} red counters and {blue} blue counters. How many counters are in the bag?", f"{red}+{blue}")
        if skill == "ratio reasoning":
            left, right, known = 2, 3 + index % 3, 8 + 2 * (index % 3)
            return arithmetic(f"{lead}The ratio of red to blue tiles is {left}:{right}. If there are {known} red tiles, how many blue tiles are there?", f"{known}*{right}/{left}")
        if skill == "fractions and decimals":
            return arithmetic(f"{lead}Write {index + 3} tenths as a decimal.", f"{index + 3}/10")
        return arithmetic(f"{lead}Point Q is at ({index % 6}, {2 + index % 5}). What is its x-coordinate?", str(index % 6))

    if skill == "solve linear equations and inequalities":
        solution = 2 + index % 7
        return arithmetic(f"{lead}Solve for x: 3x + 4 = {3 * solution + 4}.", str(solution))
    if skill == "create equations from contexts":
        price, count = 4 + index % 5, 3 + index % 4
        return arithmetic(f"{lead}Tickets cost ${price} each. What is the cost of {count} tickets?", f"{price}*{count}")
    if skill == "function notation and evaluation":
        value = 2 + index % 6
        return arithmetic(f"{lead}If f(x) = 2x + 5, find f({value}).", f"2*{value}+5")
    if skill == "simplify expressions":
        value = 2 + index % 5
        return arithmetic(f"{lead}Evaluate 4x - 3 when x = {value}.", f"4*{value}-3")
    if skill == "slope":
        return arithmetic(f"{lead}A line rises {2 + index % 4} units and runs 1 unit. What is its slope?", str(2 + index % 4))
    if skill == "rational exponents and radicals":
        base, exponent = 2 + index % 3, 2 + index % 2
        return arithmetic(f"{lead}Evaluate: {base}^{exponent}.", f"{base}**{exponent}")
    if skill == "transformations":
        x, shift = index % 5, 2 + index % 3
        return arithmetic(f"{lead}Point A is at ({x}, 4). Translate it {shift} units right. What is the new x-coordinate?", f"{x}+{shift}")
    if skill == "polynomial operations":
        value = 2 + index % 4
        return arithmetic(f"{lead}Evaluate x^2 + 3x when x = {value}.", f"{value}**2+3*{value}")
    return arithmetic(f"{lead}Evaluate x^2 - 4 when x = {3 + index % 4}.", f"{3 + index % 4}**2-4")


def approval(manifest, gate, revision):
    return gates.record_approval(
        manifest,
        gate=gate,
        artifact_revision=revision,
        status="approved",
        reviewer="auto-bypass",
        notes="Explicit current-user instruction for this run: gates=bypass all.",
    )


def build_clients():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return build("drive", "v3", credentials=credentials), build("docs", "v1", credentials=credentials)


def document_text(docs, document_id):
    body = docs.documents().get(documentId=document_id).execute().get("body", {}).get("content", [])
    text = "".join(
        element.get("textRun", {}).get("content", "")
        for item in body
        for element in item.get("paragraph", {}).get("elements", [])
    )
    return text, len(body)


def build_run_state():
    resolved = policy.resolve({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)
    math = subject_module.MathSubjectModule(REPO / "subjects" / "math")
    workflow = weekly_workflow.prepare_scope_review(resolved, on_date=WEEK_OF, subject_module=math, grade_ids=None)
    overrides = question_plan.parse_topic_overrides(EFFECTIVE_TOPIC_OVERRIDES)
    week_1 = date.fromisoformat(str(resolved["calendar"]["week_1_start"]))
    instructional_week = (date.fromisoformat(WEEK_OF) - week_1).days // 7 + 1
    return resolved, math, workflow, overrides, instructional_week


def build_plans(resolved, math, workflow, overrides):
    plans = {}
    for entry in workflow["worksheet_plans"]:
        grade = entry["grade_or_course"]
        basis = SKILL_BASIS[grade]
        plan = math.build_week_plan(
            [dict(section) for section in resolved["sections"]],
            primary_skills=basis["primary"],
            spiral_skills=basis["spiral"],
            slots_per_day=entry["plan"]["questions_per_day"],
            difficulty="medium_plus",
            diversity="medium_plus",
            topic_overrides=overrides.get(grade),
            form_diversity="high",
            variation_seed=VARIATION_SEED,
            grade_or_course=grade,
        )
        if grade == "grade_9_10":
            courses = ["math_1"] * 13 + ["math_2"] * 12
            index = 0
            for day in DAY_ORDER:
                for slot in plan[day]:
                    slot["course"] = courses[index]
                    index += 1
        plans[grade] = plan
    return plans


def build_specs(resolved, math, workflow, plans):
    specs = {}
    reports = {}
    for entry in workflow["worksheet_plans"]:
        grade = entry["grade_or_course"]
        sections = []
        number = 1
        for section_config in resolved["sections"]:
            day = section_config["id"]
            questions = []
            for slot in plans[grade][day]:
                question = question_for(grade, slot, number)
                question.update({
                    "number": number,
                    "skill": slot["skill"],
                    "difficulty": slot["difficulty"],
                    **({"topic_override": True} if slot.get("topic_override") else {}),
                    **({"course": slot["course"]} if slot.get("course") else {}),
                    **{field: slot[field] for field in ("form_family", "cognitive_action", "representation", "response_type", "variation_seed") if field in slot},
                })
                questions.append(question)
                number += 1
            sections.append({"id": day, "title": section_config.get("title", day.title()), "questions": questions})
        spec = {
            "worksheet": {
                "grade": grade,
                "grade_or_course": grade,
                "grade_display_name": entry["plan"].get("grade_display_name", grade),
                "week_start": WEEK_OF,
                "question_count": number - 1,
                "duration_minutes": None,
                "title": "MTS - WEEKLY MATH WORKSHEET",
            },
            "sections": sections,
            "verification": {"status": "PENDING"},
        }
        progression = math.check_diversity_and_progression(spec, diversity="medium_plus")
        forms = math.check_form_diversity(spec, grade_or_course=grade, form_diversity="high")
        verification = math.verify_spec(spec)
        if progression["status"] != "PASS" or forms["status"] != "PASS" or verification["status"] != "PASS":
            raise RuntimeError(json.dumps({"grade": grade, "progression": progression, "forms": forms, "verification": verification}, indent=2))
        spec["verification"] = {"status": "PASS", "summary": verification}
        specs[grade] = spec
        reports[grade] = {"progression": progression, "forms": forms, "verification": verification}
    return specs, reports


def preflight():
    resolved, math, workflow, overrides, instructional_week = build_run_state()
    plans = build_plans(resolved, math, workflow, overrides)
    specs, reports = build_specs(resolved, math, workflow, plans)
    return {
        "run_id": RUN_ID,
        "instructional_week": instructional_week,
        "on_date": WEEK_OF,
        "gates": {"mode": "bypass_all", "bypassed": GATE_IDS, "requested_by": "current_user"},
        "publish": {"requested": "yes", "resolved": True},
        "deliver": {"requested": "yes", "resolved": True},
        "topic_overrides_raw_user": RAW_USER_TOPIC_OVERRIDES,
        "topic_overrides_effective": overrides,
        "worksheets": {grade: specs[grade]["worksheet"]["question_count"] for grade in specs},
        "qa": {grade: {"progression": data["progression"]["status"], "forms": data["forms"]["status"], "verification": data["verification"]["status"]} for grade, data in reports.items()},
    }


def execute():
    resolved, math, workflow, overrides, instructional_week = build_run_state()
    plans = build_plans(resolved, math, workflow, overrides)
    specs, reports = build_specs(resolved, math, workflow, plans)
    repository = run_repository.RunRepository(RUNS)
    manifest = repository.create_or_resume({"subject": "math", "worksheet_type": "weekly-worksheet"}, resolved, run_id=RUN_ID)
    manifest.update({
        "status": "scope_resolved",
        "week": {"requested": "08/31/2026", "on_date": WEEK_OF, "instructional_week": instructional_week},
        "gates": {"mode": "bypass_all", "bypassed": GATE_IDS, "requested_by": "current_user"},
        "publish": {"requested": "yes", "resolved": True},
        "deliver": {"requested": "yes", "resolved": True},
        "question_design": {"difficulty": "medium_plus", "diversity": "medium_plus", "form_diversity": "high", "variation_seed": VARIATION_SEED},
        "topic_overrides_raw_user": RAW_USER_TOPIC_OVERRIDES,
        "topic_overrides": overrides,
        "scope_review": workflow,
        "skill_basis": {"confidence": "inferred", "basis": SKILL_BASIS},
        "question_plan": {"revision": f"question-plan-2026-08-31-{REVISION}", "difficulty": "medium_plus", "diversity": "medium_plus", "form_diversity": "high", "plans": plans},
    })
    manifest = approval(manifest, "scope_review", "scope-2026-08-31-r1")
    gates.require_approval(manifest, gate="scope_review", artifact_revision="scope-2026-08-31-r1")
    repository.save_manifest(manifest)

    spec_repo = spec_repository.SpecRepository(RUNS)
    references = []
    for grade, spec in specs.items():
        reference = spec_repo.write_revision(manifest, spec, worksheet_id=grade, revision=f"questions-{REVISION}")
        references.append(reference)
    manifest["spec_references"] = references
    manifest["status"] = "questions_generated"
    for reference in references:
        manifest = approval(manifest, "question_review", f"{reference['worksheet_id']}-questions-{REVISION}")
        gates.require_question_review(manifest, artifact_revision=f"{reference['worksheet_id']}-questions-{REVISION}")
        manifest = approval(manifest, "verification_review", f"{reference['worksheet_id']}-verification-{REVISION}")
        gates.require_approval(manifest, gate="verification_review", artifact_revision=f"{reference['worksheet_id']}-verification-{REVISION}")
    manifest["verification"] = {"revision": f"verification-2026-08-31-{REVISION}", "results": {grade: report["verification"] for grade, report in reports.items()}}
    manifest["progression_qa"] = {"revision": f"progression-2026-08-31-{REVISION}", "results": {grade: report["progression"] for grade, report in reports.items()}}
    manifest["form_diversity_qa"] = {"revision": f"forms-2026-08-31-{REVISION}", "results": {grade: report["forms"] for grade, report in reports.items()}}
    manifest["status"] = "render_ready"
    repository.save_manifest(manifest)

    drive, docs = build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    template_manifest = json.loads((REPO / resolved["template_selection"]["template_manifest"]).read_text(encoding="utf-8"))
    templates = {
        "student_template_id": template_manifest["worksheet_template"]["id"],
        "answer_key_template_id": template_manifest["answer_key_template"]["id"],
    }
    artifacts = []
    rendered_record = []
    qa_results = {}
    for grade, spec in specs.items():
        base_name = renderer.name_for(grade, WEEK_OF)
        student = renderer.copy_document(drive, templates["student_template_id"], base_name)
        key = renderer.copy_document(drive, templates["answer_key_template_id"], base_name + "_KEY")
        renderer.render_document(docs, student["id"], renderer.projection(spec, False), spec, False)
        renderer.render_document(docs, key["id"], renderer.projection(spec, True), spec, True)
        student_artifact = {"artifact_kind": "student_worksheet", "status": "validated", "worksheet_id": grade, "document": student}
        key_artifact = {"artifact_kind": "answer_key", "status": "validated", "worksheet_id": grade, "document": key}
        student_text, student_blocks = document_text(docs, student_artifact["document"]["id"])
        key_text, key_blocks = document_text(docs, key_artifact["document"]["id"])
        qa = math.validate_subject_output({"student_worksheet": student_text, "answer_key": key_text}, spec)
        if qa["student_worksheet"]["status"] != "PASS" or qa["answer_key"]["status"] != "PASS" or "{{" in student_text or "{{" in key_text:
            raise RuntimeError(json.dumps({"grade": grade, "qa": qa}, indent=2))
        qa_results[grade] = {"status": "PASS", "student_content_blocks": student_blocks, "answer_key_content_blocks": key_blocks, "text_qa": qa}
        artifacts.extend([student_artifact, key_artifact])
        rendered_record.append({"worksheet_id": grade, "worksheet": student_artifact["document"], "answer_key": key_artifact["document"], "status": "rendered"})
        manifest = approval(manifest, "formatting_review", f"{grade}-render-{REVISION}")
        gates.require_approval(manifest, gate="formatting_review", artifact_revision=f"{grade}-render-{REVISION}")
    manifest["artifacts"] = artifacts
    manifest["formatting_qa"] = {"revision": f"render-2026-08-31-{REVISION}", "results": qa_results}
    manifest["status"] = "publish_approval_pending"
    manifest = approval(manifest, "publish_approval", f"batch-2026-08-31-{REVISION}")
    gates.require_approval(manifest, gate="publish_approval", artifact_revision=f"batch-2026-08-31-{REVISION}")
    repository.save_manifest(manifest)
    (RUN_ROOT / "rendered-artifacts.json").write_text(json.dumps({"status": "rendered_to_staging", "staging_folder": STAGING_FOLDER, "artifacts": rendered_record}, indent=2) + "\n", encoding="utf-8")

    publication_pairs = {}
    published_artifacts = []
    for grade in specs:
        student_artifact = next(item for item in artifacts if item["worksheet_id"] == grade and item["artifact_kind"] == "student_worksheet")
        key_artifact = next(item for item in artifacts if item["worksheet_id"] == grade and item["artifact_kind"] == "answer_key")
        published = adapter.publish_pair(student_artifact, key_artifact, FINAL_FOLDER)
        publication_pairs[grade] = published
        published_artifacts.extend([
            {"artifact_kind": "student_worksheet", "status": "published", "worksheet_id": grade, "document": published["student_worksheet"]},
            {"artifact_kind": "answer_key", "status": "published", "worksheet_id": grade, "document": published["answer_key"]},
        ])
    manifest["artifacts"] = published_artifacts
    manifest["publication"] = {"status": "published", "destination_folder_id": FINAL_FOLDER, "pairs": publication_pairs}
    manifest["status"] = "published"
    repository.save_manifest(manifest)
    (RUN_ROOT / "published-artifacts.json").write_text(json.dumps(manifest["publication"], indent=2) + "\n", encoding="utf-8")

    delivery = resolved["publishing"]["final_delivery"]
    folder_name = delivery["week_folder_pattern"].replace("{{WEEK_OF}}", WEEK_OF)
    delivery_results = {}
    for grade, pair in publication_pairs.items():
        destination = delivery["destinations_by_grade"][grade]
        week_folder = adapter.ensure_child_folder(destination["folder_id"], folder_name)
        delivered = adapter.deliver_pair(
            {"artifact_kind": "student_worksheet", "status": "published", "document": pair["student_worksheet"]},
            {"artifact_kind": "answer_key", "status": "published", "document": pair["answer_key"]},
            week_folder["id"],
            mode=delivery["mode"],
            deliver_answer_key=delivery["deliver_answer_key"],
        )
        delivery_results[grade] = {"parent_folder_id": destination["folder_id"], "week_folder": week_folder, **delivered}
    manifest["delivery"] = {"status": "delivered", "audience": delivery["audience"], "week_of": WEEK_OF, "week_folder_name": folder_name, "mode": delivery["mode"], "grades": delivery_results}
    manifest["status"] = "delivered"
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    repository.save_manifest(manifest)
    (RUN_ROOT / "delivered-artifacts.json").write_text(json.dumps(manifest["delivery"], indent=2) + "\n", encoding="utf-8")
    return {"run_id": RUN_ID, "status": manifest["status"], "qa": preflight()["qa"], "publication": publication_pairs, "delivery": delivery_results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = execute() if args.execute else preflight()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()