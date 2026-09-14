"""Unified worksheet-generation CLI for the migrated MTS layout."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timezone
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from mts.subjects.math.p0_runtime import safe_number_expression

from mts.setup_project.configure import resolve_effective_config
from mts.subjects.math.generation import MathGeneration
from mts.subjects.math.question_plan import parse_topic_overrides
from mts.subjects.math.weekly_workflow import prepare_scope_review
from mts.workflow_management.run_writer import RunWriter


GATES = ["scope_review", "question_review", "verification_review", "formatting_review", "publish_approval"]
WORKSHEET_TYPE_ALIASES = {"weekly": "weekly-worksheet", "class": "class-worksheet"}
GRADE_ALIASES = {"1": "grade_1", "4": "grade_4", "5": "grade_5", "6": "grade_6", "9-10": "grade_9_10", "9_10": "grade_9_10"}
ALLOWED_PARAMETERS = {
    "subject",
    "worksheettype",
    "gates",
    "grades",
    "week",
    "publish",
    "deliver",
    "render",
    "difficulty",
    "diversity",
    "form_diversity",
    "variation_seed",
    "topic_overrides",
    "run",
    "delivery_dry_run",
}
PARAMETER_SUGGESTIONS = {"grade": "grades", "worksheet_type": "worksheettype", "worksheet-type": "worksheettype"}


def plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [plain(item) for item in value]
    if isinstance(value, list):
        return [plain(item) for item in value]
    return value


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plain(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_key_value_args(raw_args: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in raw_args:
        if "=" not in raw:
            raise ValueError(f"Expected key=value argument, got {raw!r}.")
        key, value = raw.split("=", 1)
        normalized_key = key.strip().replace("-", "_")
        if normalized_key not in ALLOWED_PARAMETERS:
            suggestion = PARAMETER_SUGGESTIONS.get(normalized_key)
            if suggestion:
                raise ValueError(
                    f"Unknown parameter {normalized_key!r}. Did you mean {suggestion!r}? "
                    "The model/prompt layer must confirm that interpretation before invoking the CLI."
                )
            raise ValueError(f"Unknown parameter {normalized_key!r}.")
        values[normalized_key] = value.strip().strip('"')
    return values


def bool_param(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"yes", "true", "1", "y"}:
        return True
    if normalized in {"no", "false", "0", "n"}:
        return False
    raise ValueError(f"Expected yes/no value, got {value!r}.")


def resolve_week(value: str, calendar: Mapping[str, Any]) -> str:
    week_1_start = date.fromisoformat(str(calendar["week_1_start"]))
    if value == "current":
        today = date.today()
        return date.fromordinal(today.toordinal() - today.weekday()).isoformat()
    if value == "next":
        today = date.today()
        current_monday = date.fromordinal(today.toordinal() - today.weekday())
        return date.fromordinal(current_monday.toordinal() + 7).isoformat()
    if value.isdigit():
        return date.fromordinal(week_1_start.toordinal() + 7 * (int(value) - 1)).isoformat()
    parsed = date.fromisoformat(value)
    return date.fromordinal(parsed.toordinal() - parsed.weekday()).isoformat()


def resolve_grades(raw: str | None) -> list[str] | None:
    if raw is None or raw.strip().lower() == "all":
        return None
    grades = []
    for item in raw.split(","):
        key = item.strip().lower().replace("grade_", "").replace("grade-", "")
        grades.append(GRADE_ALIASES.get(key, f"grade_{key}"))
    return grades


def configured_level(params: Mapping[str, str], effective_config: Mapping[str, Any], key: str) -> str:
    return params.get(key, str(effective_config["question_design"][key]["default"]))


def variation_seed(params: Mapping[str, str]) -> int:
    raw = params.get("variation_seed")
    if raw:
        return int(raw)
    return int(datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))


def resolve_gate_bypasses(raw: str) -> list[str]:
    value = raw.strip().lower()
    if value == "all":
        raise ValueError("Non-interactive CLI generation requires explicit gates=bypass all or gates=bypass <gate_id>[,<gate_id>...].")
    if value == "bypass all":
        return list(GATES)
    prefix = "bypass "
    if value.startswith(prefix):
        requested = [item.strip() for item in value[len(prefix):].split(",") if item.strip()]
        unknown = [gate for gate in requested if gate not in GATES]
        if unknown:
            raise ValueError(f"Unknown gate id(s): {', '.join(unknown)}")
        return requested
    raise ValueError("Expected gates=bypass all or gates=bypass <gate_id>[,<gate_id>...].")


def scope_skills(scope: Mapping[str, Any]) -> tuple[list[str], str]:
    topics = [str(topic) for topic in scope.get("topics", []) if str(topic)]
    if topics:
        return topics, "current"
    current = [str(standard) for standard in scope.get("current", []) if str(standard)]
    if current:
        return current, "current"

    fallback = []
    units = scope.get("progressive_context", {}).get("units", {})
    for unit in units.values() if isinstance(units, Mapping) else []:
        fallback.extend(str(concept) for concept in unit.get("key_concepts", []) if str(concept))
    if fallback:
        return fallback[:8], "fallback"
    return ["grade appropriate review"], "fallback"


def source_lookup(scopes: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(scope.get("grade_or_course")): scope for scope in scopes}


def source_sequence(plan_entry: Mapping[str, Any]) -> list[str]:
    plan = plan_entry["plan"]
    split = plan.get("grade_split")
    if isinstance(split, Mapping):
        sequence = []
        for source_id, count in split.items():
            sequence.extend([str(source_id)] * int(count))
        return sequence
    return [str(plan_entry["grade_or_course"])] * int(plan["questions_per_week"])


def classify_source_kind(slot: Mapping[str, Any], scope: Mapping[str, Any], default_kind: str) -> str:
    if slot.get("topic_override"):
        return "topic_override"
    skill = slot.get("skill")
    if skill in scope.get("spiral", []):
        return "spiral"
    if skill in scope.get("topics", []) or skill in scope.get("current", []):
        return "current"
    return default_kind


def build_question_plan(
    *,
    math: MathGeneration,
    plan_entry: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    difficulty: str,
    diversity: str,
    form_diversity: str,
    seed: int,
    topic_overrides: list[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    scopes = [dict(scope) for scope in plan_entry["curriculum_scopes"]]
    primary_skills: list[str] = []
    spiral_skills: list[str] = []
    scope_default_kind: dict[str, str] = {}
    for scope in scopes:
        skills, default_kind = scope_skills(scope)
        scope_default_kind[str(scope["grade_or_course"])] = default_kind
        primary_skills.extend(skills)
        spiral_skills.extend(str(skill) for skill in scope.get("spiral", []) if str(skill))
    if not spiral_skills:
        spiral_skills = primary_skills[1:3]

    week_plan = math.build_week_plan(
        effective_config["sections"],
        primary_skills=primary_skills,
        spiral_skills=spiral_skills,
        slots_per_day=plan_entry["plan"]["questions_per_day"],
        difficulty=difficulty,
        diversity=diversity,
        topic_overrides=topic_overrides,
        form_diversity=form_diversity,
        variation_seed=seed,
        grade_or_course=plan_entry["grade_or_course"],
    )

    lookup = source_lookup(scopes)
    sequence = source_sequence(plan_entry)
    sections = []
    global_number = 1
    for section in effective_config["sections"]:
        section_id = section["id"]
        slots = []
        for slot in week_plan[section_id]:
            source_id = sequence[global_number - 1] if global_number <= len(sequence) else str(scopes[0]["grade_or_course"])
            scope = lookup.get(source_id, scopes[0])
            planned = {
                "number": global_number,
                "section_id": section_id,
                "section_title": section.get("title", section_id.title()),
                "slot": slot["slot"],
                "skill": slot["skill"],
                "difficulty": slot["difficulty"],
                "source_kind": classify_source_kind(slot, scope, scope_default_kind.get(source_id, "fallback")),
                "source_scope": source_id,
                "standards": list(scope.get("current", [])),
                "confidence": scope.get("confidence", "inferred"),
                "cache_hit": scope.get("cache_hit", False),
            }
            for field in ("form_family", "cognitive_action", "representation", "response_type", "variation_seed", "topic_override"):
                if field in slot:
                    planned[field] = slot[field]
            slots.append(planned)
            global_number += 1
        sections.append({"id": section_id, "title": section.get("title", section_id.title()), "slots": slots})
    return {
        "plan_version": "1.0",
        "grade_or_course": plan_entry["grade_or_course"],
        "worksheet_type": "weekly-worksheet",
        "source_chain": "yearly_curriculum -> weekly_curriculum -> worksheet_plan -> question_plan -> worksheet_spec",
        "difficulty": difficulty,
        "diversity": diversity,
        "form_diversity": form_diversity,
        "variation_seed": seed,
        "curriculum_scope_ids": [scope["grade_or_course"] for scope in scopes],
        "sections": sections,
    }


def arithmetic_question(prompt: str, expression: str):
    return {
        "prompt": prompt,
        "answer": safe_number_expression(expression),
        "verification": {"method": "arithmetic_expression", "inputs": {"expression": expression}},
    }


def gcf_question(prompt: str, left: int, right: int):
    return {
        "prompt": prompt,
        "answer": math.gcd(int(left), int(right)),
        "verification": {"method": "gcf", "inputs": {"a": left, "b": right}},
    }


def question_for(grade: str, skill: str, number: int):
    index = number + 2
    if grade == "grade_1":
        if skill.startswith("Count on"):
            start, steps = 4 + index % 6, 1 + index % 4
            if number % 2:
                return arithmetic_question(f"Start at {start}. Count on {steps}. What number do you say?", f"{start}+{steps}")
            return arithmetic_question(f"Start at {start + steps}. Count down {steps}. What number do you say?", f"{start + steps}-{steps}")
        if skill == "addition and subtraction within 20":
            left, right = 5 + index % 8, 2 + index % 5
            return arithmetic_question(f"Solve: {left} + {right} = ___.", f"{left}+{right}")
        if skill == "unknown-addend and unknown-subtrahend equations":
            total, addend = 12 + index % 8, 3 + index % 6
            return arithmetic_question(f"Find the missing number: ___ + {addend} = {total}.", f"{total}-{addend}")
        if skill == "counting sequence":
            return arithmetic_question(f"What number comes after {8 + index}?", f"{8 + index}+1")
        return arithmetic_question(f"Which number is greater: {10 + index} or {9 + index}? Write the greater number.", f"{10 + index}")

    if grade == "grade_4":
        if skill == "data and graphing basics":
            apples, pears, bananas = 8 + index, 5 + index % 4, 6 + index % 3
            return arithmetic_question(f"A bar graph shows {apples} apples, {pears} pears, and {bananas} bananas. How many apples and pears are shown altogether?", f"{apples}+{pears}")
        if skill == "multi-digit place value":
            value = 3000 + 100 * (index % 6)
            return arithmetic_question(f"What is the value of the digit 3 in {value + 450}?", "3000")
        if skill == "compare multi-digit numbers":
            larger = 4200 + 10 * index
            return arithmetic_question(f"Which number is greater: {larger} or {larger - 19}? Write the greater number.", str(larger))
        if skill == "addition and subtraction":
            left, right = 1200 + 13 * index, 300 + 7 * index
            return arithmetic_question(f"Solve: {left} - {right} = ___.", f"{left}-{right}")
        if skill == "multiplication facts":
            return arithmetic_question(f"Solve: {3 + index % 6} x {4 + index % 5} = ___.", f"{3 + index % 6}*{4 + index % 5}")
        return arithmetic_question(f"Round {1240 + 10 * index} to the nearest hundred.", str(round((1240 + 10 * index) / 100) * 100))

    if grade == "grade_5":
        if skill == "coordinate geometry basics":
            x, y = index % 8, 2 + index % 7
            return arithmetic_question(f"Point P is at ({x}, {y}). What is the y-coordinate of P?", str(y))
        if skill == "numerical expressions":
            left, right = 3 + index % 5, 4 + index % 4
            return arithmetic_question(f"Evaluate: {left} x ({right} + 2).", f"{left}*({right}+2)")
        if skill == "patterns":
            start, step = 4 + index, 3 + index % 4
            return arithmetic_question(f"The pattern is {start}, {start + step}, {start + 2 * step}, ___. What is next?", f"{start}+3*{step}")
        if skill == "whole-number multiplication":
            left, right = 12 + index, 6 + index % 5
            return arithmetic_question(f"Solve: {left} x {right} = ___.", f"{left}*{right}")
        if skill == "place value":
            return arithmetic_question(f"What is the value of the digit 6 in {60000 + 100 * index + 4}?", "60000")
        return arithmetic_question(f"Solve: {2500 + 20 * index} + {700 + index} = ___.", f"{2500 + 20 * index}+{700 + index}")

    if grade == "grade_6":
        if skill == "prime factorization basics":
            prime_sets = [(2, 2, 3), (2, 3, 5), (2, 2, 5), (3, 3, 2)]
            factors = prime_sets[index % len(prime_sets)]
            expression = "*".join(map(str, factors))
            return arithmetic_question(f"The prime factors {' x '.join(map(str, factors))} multiply to what number?", expression)
        if skill == "factor pairs and multiples":
            left, right = 12 + 2 * (index % 5), 18 + 3 * (index % 5)
            return gcf_question(f"Find the greatest common factor of {left} and {right}.", left, right)
        if skill == "ratio concepts":
            red, blue = 2 + index % 3, 3 + index % 4
            return arithmetic_question(f"A bag has {red} red counters and {blue} blue counters. How many counters are in the bag?", f"{red}+{blue}")
        if skill == "ratio reasoning":
            left, right, known = 2, 3 + index % 3, 8 + 2 * (index % 3)
            return arithmetic_question(f"The ratio of red to blue tiles is {left}:{right}. If there are {known} red tiles, how many blue tiles are there?", f"{known}*{right}/{left}")
        if skill == "fractions and decimals":
            return arithmetic_question(f"Write {index + 3} tenths as a decimal.", f"{index + 3}/10")
        return arithmetic_question(f"Point Q is at ({index % 6}, {2 + index % 5}). What is its x-coordinate?", str(index % 6))

    if skill == "solve linear equations and inequalities":
        solution = 2 + index % 7
        return arithmetic_question(f"Solve for x: 3x + 4 = {3 * solution + 4}.", str(solution))
    if skill == "create equations from contexts":
        price, count = 4 + index % 5, 3 + index % 4
        return arithmetic_question(f"Tickets cost ${price} each. What is the cost of {count} tickets?", f"{price}*{count}")
    if skill == "function notation and evaluation":
        value = 2 + index % 6
        return arithmetic_question(f"If f(x) = 2x + 5, find f({value}).", f"2*{value}+5")
    if skill == "simplify expressions":
        value = 2 + index % 5
        return arithmetic_question(f"Evaluate 4x - 3 when x = {value}.", f"4*{value}-3")
    if skill == "slope":
        return arithmetic_question(f"A line rises {2 + index % 4} units and runs 1 unit. What is its slope?", str(2 + index % 4))
    if skill == "rational exponents and radicals":
        base, exponent = 2 + index % 3, 2 + index % 2
        return arithmetic_question(f"Evaluate: {base}^{exponent}.", f"{base}**{exponent}")
    if skill == "transformations":
        x, shift = index % 5, 2 + index % 3
        return arithmetic_question(f"Point A is at ({x}, 4). Translate it {shift} units right. What is the new x-coordinate?", f"{x}+{shift}")
    if skill == "congruence":
        side = 5 + index % 9
        return arithmetic_question(f"A side of triangle ABC is {side} cm. A congruent triangle has the matching side length of how many centimeters?", str(side))
    if skill == "polynomial operations":
        value = 2 + index % 4
        return arithmetic_question(f"Evaluate x^2 + 3x when x = {value}.", f"{value}**2+3*{value}")
    return arithmetic_question(f"Evaluate x^2 - 4 when x = {3 + index % 4}.", f"{3 + index % 4}**2-4")


def candidate_spec_from_question_plan(question_plan: Mapping[str, Any], week_start: str) -> dict[str, Any]:
    sections = []
    for section in question_plan["sections"]:
        questions = []
        for planned in section["slots"]:
            number = planned["number"]
            skill = planned["skill"]
            generated = question_for(question_plan["grade_or_course"], skill, number)
            prompt = generated["prompt"]
            if not prompt.lower().startswith(f"question {number}:"):
                prompt = f"Question {number}: {prompt}"
            questions.append(
                {
                    "id": f"{question_plan['grade_or_course']}-q{number}",
                    "number": number,
                    "section_id": planned["section_id"],
                    "prompt": prompt,
                    "answer": generated["answer"],
                    "skill": skill,
                    "difficulty": planned["difficulty"],
                    "source_kind": planned["source_kind"],
                    "source_scope": planned["source_scope"],
                    "standards": planned["standards"],
                    "confidence": planned["confidence"],
                    "verification": generated["verification"],
                    **{
                        field: planned[field]
                        for field in ("form_family", "cognitive_action", "representation", "response_type", "variation_seed")
                        if field in planned
                    },
                }
            )
        sections.append({"id": section["id"], "title": section["title"], "questions": questions})
    return {
        "worksheet": {
            "grade": question_plan["grade_or_course"],
            "grade_or_course": question_plan["grade_or_course"],
            "title": "MTS - WEEKLY WORKSHEET SAMPLE",
            "week_start": week_start,
            "question_count": sum(len(section["slots"]) for section in question_plan["sections"]),
        },
        "sections": sections,
        "verification": {"status": "PENDING"},
    }


def validate_spec_matches_question_plan(spec: Mapping[str, Any], question_plan: Mapping[str, Any]) -> None:
    planned = [slot for section in question_plan["sections"] for slot in section["slots"]]
    actual = [question for section in spec["sections"] for question in section["questions"]]
    if len(planned) != len(actual):
        raise ValueError("Worksheet Spec question count does not match Question Plan.")
    for expected, question in zip(planned, actual):
        for field in ("number", "section_id", "skill", "difficulty", "source_kind", "source_scope"):
            if question.get(field) != expected.get(field):
                raise ValueError(f"Question {question.get('number')} does not preserve planned {field}.")
        for field in ("form_family", "cognitive_action", "representation", "response_type", "variation_seed"):
            if field in expected and question.get(field) != expected[field]:
                raise ValueError(f"Question {question.get('number')} does not preserve planned {field}.")


def projection(spec: Mapping[str, Any], *, answer_key: bool = False, numbering: str = "global") -> str:
    lines = [str(spec["worksheet"]["title"]), str(spec["worksheet"]["grade"]), f"Week of {spec['worksheet']['week_start']}"]
    if answer_key:
        lines.append("ANSWER KEY")
    for section in spec["sections"]:
        lines.append(str(section.get("title", section["id"])))
        for local_number, question in enumerate(section["questions"], start=1):
            shown = local_number if numbering == "local" else question["number"]
            value = question["answer"] if answer_key else question["prompt"]
            lines.append(f"{shown}. {value}")
    return "\n".join(lines)


def bypass_record(gate: str, artifact_revision: str) -> dict[str, Any]:
    return {
        "gate": gate,
        "artifact_revision": artifact_revision,
        "status": "approved",
        "bypass": True,
        "reviewer": "current-user-instruction",
        "notes": "Interactive gate wait bypassed for this run only; verification and QA remain required.",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def transaction_root(grade_or_course: str, week_start: str, batch_id: str, worksheet_type: str) -> Path:
    return (
        REPO
        / "data"
        / "transactions"
        / "subjects"
        / "math"
        / "grades"
        / grade_or_course
        / "cycles"
        / week_start
        / "batches"
        / batch_id
        / "worksheets"
        / worksheet_type.replace("-", "_")
    )


def operational_python() -> str:
    venv_python = REPO / ".venv" / "Scripts" / "python.exe"
    return str(venv_python) if venv_python.is_file() else sys.executable


def generate_math_weekly(params: Mapping[str, str]) -> dict[str, Any]:
    subject = params.get("subject", "math")
    worksheet_type = WORKSHEET_TYPE_ALIASES.get(params.get("worksheettype", "weekly"), params.get("worksheettype", "weekly"))
    if subject != "math" or worksheet_type != "weekly-worksheet":
        raise ValueError("The seamless runner currently supports subject=math worksheettype=weekly.")

    gate_bypasses = resolve_gate_bypasses(params.get("gates", "bypass all"))
    request = {
        "subject": subject,
        "worksheet_type": worksheet_type,
        "overrides": {"gates": {gate: "bypass" for gate in gate_bypasses}},
    }
    effective_config = resolve_effective_config(request, repository_root=REPO)
    render = bool_param(params.get("render"), default=True)
    publish = bool_param(params.get("publish"), default=bool(effective_config["publishing"]["default_publish"]))
    deliver = bool_param(params.get("deliver"), default=bool(effective_config["publishing"]["final_delivery"]["default_deliver"]))
    if deliver and not publish:
        raise ValueError("deliver=yes requires publish=yes; use deliver=no for staging-only generation.")
    if publish and not render:
        raise ValueError("publish=yes requires render=yes so there are staged artifacts to publish.")

    week_start = resolve_week(params.get("week", "current"), effective_config["calendar"])
    grade_ids = resolve_grades(params.get("grades"))
    topic_overrides = parse_topic_overrides(params.get("topic_overrides"))
    difficulty = configured_level(params, effective_config, "difficulty")
    diversity = configured_level(params, effective_config, "diversity")
    form_diversity = configured_level(params, effective_config, "form_diversity")
    seed = variation_seed(params)

    run_id = params.get("run") or f"run-{week_start}-weekly-bypass"
    batch_id = f"weekly_math_{week_start.replace('-', '_')}_bypass"
    math = MathGeneration()
    scope_review = prepare_scope_review(effective_config, on_date=week_start, subject_module=math, grade_ids=grade_ids)
    run_writer = RunWriter(REPO / "data")
    entity_references = []
    gate_records = []

    print("RESOLVED_PARAMETERS")
    print(f"  subject={subject}")
    print(f"  worksheettype={worksheet_type}")
    print(f"  grades={grade_ids or 'all'}")
    print(f"  week={week_start}")
    print(f"  gates=bypass {','.join(gate_bypasses)}")
    print(f"  publish={'yes' if publish else 'no'}")
    print(f"  deliver={'yes' if deliver else 'no'}")
    print(f"  difficulty={difficulty}")
    print(f"  diversity={diversity}")
    print(f"  form_diversity={form_diversity}")
    print(f"  variation_seed={seed}")
    print(f"  topic_overrides={topic_overrides or 'none'}")

    for plan_entry in scope_review["worksheet_plans"]:
        grade = plan_entry["grade_or_course"]
        per_grade_overrides = topic_overrides.get(grade)
        question_plan = build_question_plan(
            math=math,
            plan_entry=plan_entry,
            effective_config=effective_config,
            difficulty=difficulty,
            diversity=diversity,
            form_diversity=form_diversity,
            seed=seed,
            topic_overrides=per_grade_overrides,
        )
        spec = math.build_spec(plan_entry["plan"], {"spec": candidate_spec_from_question_plan(question_plan, week_start)})
        validate_spec_matches_question_plan(spec, question_plan)
        progression = math.check_diversity_and_progression(spec, diversity=diversity)
        forms = math.check_form_diversity(spec, grade_or_course=grade, form_diversity=form_diversity)
        if progression["status"] != "PASS":
            raise ValueError(f"Question Plan progression validation failed for {grade}: {progression}")
        if forms["status"] != "PASS":
            raise ValueError(f"Question Plan form diversity validation failed for {grade}: {forms}")
        verification = math.verify_spec(spec)
        if verification["status"] != "PASS":
            raise ValueError(f"Verification failed for {grade}: {verification}")
        spec["verification"]["status"] = "PASS"
        numbering = effective_config.get("display_numbering", "global")
        qa = math.validate_subject_output(
            {
                "student_worksheet": projection(spec, numbering=numbering),
                "answer_key": projection(spec, answer_key=True, numbering=numbering),
            },
            spec,
            numbering=numbering,
        )
        if qa["student_worksheet"]["status"] != "PASS" or qa["answer_key"]["status"] != "PASS":
            raise ValueError(f"QA failed for {grade}: {qa}")

        root = transaction_root(grade, week_start, batch_id, worksheet_type)
        revision = f"{grade}-r1"
        cycle_root = root.parents[3]
        write_json(cycle_root / "cycle.json", {"cycle_id": week_start, "cycle_type": "weekly", "week_start": week_start})
        write_json(cycle_root / "weekly_curriculum.json", {"scope_review": plain(plan_entry["curriculum_scopes"])})
        if len(plan_entry["curriculum_scopes"]) > 1:
            for scope in plan_entry["curriculum_scopes"]:
                write_json(cycle_root / "curriculum_scopes" / f"{scope['grade_or_course']}.json", scope)
        write_json(root.parent.parent / "batch.json", {"batch_id": batch_id, "subject": "math", "worksheet_type": worksheet_type, "week_start": week_start})
        write_json(root / "worksheet_plan.json", plan_entry["plan"])
        write_json(root / "question_plan.json", question_plan)
        write_json(root / "worksheet.json", {"worksheet_id": grade, "grade_or_course": grade, "worksheet_type": worksheet_type, "status": "qa_complete"})
        write_json(root / "specs" / "r1.json", spec)
        write_json(root / "verification" / "verification-r1.json", verification)
        write_json(root / "qa" / "student_worksheet.json", qa["student_worksheet"])
        write_json(root / "qa" / "answer_key.json", qa["answer_key"])
        for gate in gate_bypasses:
            record = bypass_record(gate, revision)
            gate_records.append({"grade_or_course": grade, **record})
            write_json(root / "approvals" / f"{gate}-r1.json", record)
        entity_references.append(
            {
                "grade_or_course": grade,
                "worksheet_root": root.relative_to(REPO).as_posix(),
                "worksheet_plan": (root / "worksheet_plan.json").relative_to(REPO).as_posix(),
                "question_plan": (root / "question_plan.json").relative_to(REPO).as_posix(),
                "spec": (root / "specs" / "r1.json").relative_to(REPO).as_posix(),
                "verification": (root / "verification" / "verification-r1.json").relative_to(REPO).as_posix(),
            }
        )

    run_writer.write_effective_config(run_id, effective_config)
    run_writer.write_entity_references(run_id, {"references": entity_references})
    manifest = {
        "run_id": run_id,
        "subject": subject,
        "worksheet_type": worksheet_type,
        "week_start": week_start,
        "status": "publish_ready_sample",
        "gates": {"mode": "bypass", "bypassed": gate_bypasses, "requested_by": "current_user"},
        "gate_bypasses": gate_records,
        "verification_required": True,
        "qa_required": True,
        "question_plan_required": True,
        "variation_seed": seed,
    }
    run_writer.write_manifest(manifest)
    write_json(run_writer.run_root(run_id) / "telemetry.json", {"token_usage": None, "mode": "generate_worksheet_cli"})

    if render:
        subprocess.run(
            [operational_python(), "scripts/render_weekly_specs_to_drive.py", "--run-root", f"data/transactions/runs/{run_id}", "--date", week_start],
            cwd=REPO,
            check=True,
        )
        manifest["status"] = "rendered_to_staging"
        manifest["rendered_artifacts"] = f"data/transactions/runs/{run_id}/rendered-artifacts.json"
        run_writer.write_manifest(manifest)
    if publish:
        subprocess.run(
            [operational_python(), "scripts/publish_weekly_artifacts.py", "--run-root", f"data/transactions/runs/{run_id}"],
            cwd=REPO,
            check=True,
        )
        manifest["status"] = "published"
        manifest["published_artifacts"] = f"data/transactions/runs/{run_id}/published-artifacts.json"
        run_writer.write_manifest(manifest)
    if deliver:
        try:
            subprocess.run(
                [operational_python(), "scripts/deliver_weekly_worksheets.py", "--run-root", f"data/transactions/runs/{run_id}", "--week-of", week_start],
                cwd=REPO,
                check=True,
            )
            manifest["status"] = "delivered"
            manifest["delivered_artifacts"] = f"data/transactions/runs/{run_id}/delivered-artifacts.json"
            run_writer.write_manifest(manifest)
        except subprocess.CalledProcessError:
            manifest["status"] = "delivery_failed"
            manifest["delivery_failure"] = f"data/transactions/runs/{run_id}/delivery-failure.json"
            run_writer.write_manifest(manifest)
            raise
    elif params.get("delivery_dry_run", "yes").lower() in {"yes", "true", "1"}:
        subprocess.run(
            [operational_python(), "scripts/deliver_weekly_worksheets.py", "--run-root", f"data/transactions/runs/{run_id}", "--week-of", week_start, "--dry-run"],
            cwd=REPO,
            check=True,
        )

    return {"run_id": run_id, "week_start": week_start, "worksheets": len(entity_references), "gates_bypassed": len(gate_records)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate MTS worksheets from command-style parameters.")
    parser.add_argument("params", nargs="*", help="key=value parameters, e.g. subject=math worksheettype=weekly week=next gates='bypass all'")
    args = parser.parse_args(argv)
    result = generate_math_weekly(parse_key_value_args(args.params))
    print(f"GENERATE_WORKSHEET_PASS {result['run_id']} week={result['week_start']} worksheets={result['worksheets']} gates_bypassed={result['gates_bypassed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())