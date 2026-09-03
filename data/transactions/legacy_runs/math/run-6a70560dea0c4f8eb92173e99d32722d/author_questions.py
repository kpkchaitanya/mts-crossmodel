import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.extend([str(REPO / "src" / "runtime"), str(REPO / "subjects" / "math" / "src")])

import p0_runtime
import run_repository
import spec_repository

RUN_ID = "run-6a70560dea0c4f8eb92173e99d32722d"
RUNS = REPO / "runs"
DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday"]


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


def question_for(grade, skill, number):
    index = number + 2
    if grade == "grade_1":
        if skill.startswith("Count on"):
            start, steps = 4 + index % 6, 1 + index % 4
            if number % 2:
                return arithmetic(f"Start at {start}. Count on {steps}. What number do you say?", f"{start}+{steps}")
            return arithmetic(f"Start at {start + steps}. Count down {steps}. What number do you say?", f"{start + steps}-{steps}")
        if skill == "addition and subtraction within 20":
            left, right = 5 + index % 8, 2 + index % 5
            return arithmetic(f"Solve: {left} + {right} = ___.", f"{left}+{right}")
        if skill == "unknown-addend and unknown-subtrahend equations":
            total, addend = 12 + index % 8, 3 + index % 6
            return arithmetic(f"Find the missing number: ___ + {addend} = {total}.", f"{total}-{addend}")
        if skill == "counting sequence":
            return arithmetic(f"What number comes after {8 + index}?", f"{8 + index}+1")
        return arithmetic(f"Which number is greater: {10 + index} or {9 + index}? Write the greater number.", f"{10 + index}")

    if grade == "grade_4":
        if skill == "data and graphing basics":
            apples, pears, bananas = 8 + index, 5 + index % 4, 6 + index % 3
            return arithmetic(f"A bar graph shows {apples} apples, {pears} pears, and {bananas} bananas. How many apples and pears are shown altogether?", f"{apples}+{pears}")
        if skill == "multi-digit place value":
            value = 3000 + 100 * (index % 6)
            return arithmetic(f"What is the value of the digit 3 in {value + 450}?", "3000")
        if skill == "compare multi-digit numbers":
            larger = 4200 + 10 * index
            return arithmetic(f"Which number is greater: {larger} or {larger - 19}? Write the greater number.", str(larger))
        if skill == "addition and subtraction":
            left, right = 1200 + 13 * index, 300 + 7 * index
            return arithmetic(f"Solve: {left} - {right} = ___.", f"{left}-{right}")
        if skill == "multiplication facts":
            return arithmetic(f"Solve: {3 + index % 6} x {4 + index % 5} = ___.", f"{3 + index % 6}*{4 + index % 5}")
        return arithmetic(f"Round {1240 + 10 * index} to the nearest hundred.", str(round((1240 + 10 * index) / 100) * 100))

    if grade == "grade_5":
        if skill == "coordinate geometry basics":
            x, y = index % 8, 2 + index % 7
            return arithmetic(f"Point P is at ({x}, {y}). What is the y-coordinate of P?", str(y))
        if skill == "numerical expressions":
            left, right = 3 + index % 5, 4 + index % 4
            return arithmetic(f"Evaluate: {left} x ({right} + 2).", f"{left}*({right}+2)")
        if skill == "patterns":
            start, step = 4 + index, 3 + index % 4
            return arithmetic(f"The pattern is {start}, {start + step}, {start + 2 * step}, ___. What is next?", f"{start}+3*{step}")
        if skill == "whole-number multiplication":
            left, right = 12 + index, 6 + index % 5
            return arithmetic(f"Solve: {left} x {right} = ___.", f"{left}*{right}")
        if skill == "place value":
            return arithmetic(f"What is the value of the digit 6 in {60000 + 100 * index + 4}?", "60000")
        return arithmetic(f"Solve: {2500 + 20 * index} + {700 + index} = ___.", f"{2500 + 20 * index}+{700 + index}")

    if grade == "grade_6":
        if skill == "prime factorization basics":
            prime_sets = [(2, 2, 3), (2, 3, 5), (2, 2, 5), (3, 3, 2)]
            factors = prime_sets[index % len(prime_sets)]
            expression = "*".join(map(str, factors))
            return arithmetic(f"The prime factors { ' x '.join(map(str, factors)) } multiply to what number?", expression)
        if skill == "factor pairs and multiples":
            left, right = 12 + 2 * (index % 5), 18 + 3 * (index % 5)
            return gcf(f"Find the greatest common factor of {left} and {right}.", left, right)
        if skill == "ratio concepts":
            red, blue = 2 + index % 3, 3 + index % 4
            return arithmetic(f"A bag has {red} red counters and {blue} blue counters. How many counters are in the bag?", f"{red}+{blue}")
        if skill == "ratio reasoning":
            left, right, known = 2, 3 + index % 3, 8 + 2 * (index % 3)
            return arithmetic(f"The ratio of red to blue tiles is {left}:{right}. If there are {known} red tiles, how many blue tiles are there?", f"{known}*{right}/{left}")
        if skill == "fractions and decimals":
            return arithmetic(f"Write {index + 3} tenths as a decimal.", f"{index + 3}/10")
        return arithmetic(f"Point Q is at ({index % 6}, {2 + index % 5}). What is its x-coordinate?", str(index % 6))

    if skill == "solve linear equations and inequalities":
        solution = 2 + index % 7
        return arithmetic(f"Solve for x: 3x + 4 = {3 * solution + 4}.", str(solution))
    if skill == "create equations from contexts":
        price, count = 4 + index % 5, 3 + index % 4
        return arithmetic(f"Tickets cost ${price} each. What is the cost of {count} tickets?", f"{price}*{count}")
    if skill == "function notation and evaluation":
        value = 2 + index % 6
        return arithmetic(f"If f(x) = 2x + 5, find f({value}).", f"2*{value}+5")
    if skill == "simplify expressions":
        value = 2 + index % 5
        return arithmetic(f"Evaluate 4x - 3 when x = {value}.", f"4*{value}-3")
    if skill == "slope":
        return arithmetic(f"A line rises {2 + index % 4} units and runs 1 unit. What is its slope?", str(2 + index % 4))
    if skill == "rational exponents and radicals":
        base, exponent = 2 + index % 3, 2 + index % 2
        return arithmetic(f"Evaluate: {base}^{exponent}.", f"{base}**{exponent}")
    if skill == "transformations":
        x, shift = index % 5, 2 + index % 3
        return arithmetic(f"Point A is at ({x}, 4). Translate it {shift} units right. What is the new x-coordinate?", f"{x}+{shift}")
    if skill == "congruence":
        side = 5 + index % 9
        return arithmetic(f"A side of triangle ABC is {side} cm. A congruent triangle has the matching side length of how many centimeters?", str(side))
    if skill == "polynomial operations":
        value = 2 + index % 4
        return arithmetic(f"Evaluate x^2 + 3x when x = {value}.", f"{value}**2+3*{value}")
    return arithmetic(f"Evaluate x^2 - 4 when x = {3 + index % 4}.", f"{3 + index % 4}**2-4")


def main():
    manifest_path = RUNS / "math" / RUN_ID / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plans = manifest["question_plan"]["plans"]
    repository = run_repository.RunRepository(RUNS)
    specs = spec_repository.SpecRepository(RUNS)
    references = []
    for grade, day_plans in plans.items():
        sections = []
        number = 1
        for day in DAY_ORDER:
            slots = day_plans[day]
            questions = []
            for slot in slots:
                question = question_for(grade, slot["skill"], number)
                question.update({
                    "number": number,
                    "skill": slot["skill"],
                    "difficulty": slot["difficulty"],
                    **({"topic_override": True} if slot.get("topic_override") else {}),
                    **({"course": slot["course"]} if slot.get("course") else {}),
                })
                questions.append(question)
                number += 1
            sections.append({"id": day, "title": day.title(), "questions": questions})
        spec = {
            "worksheet": {
                "grade": grade,
                "week_start": "2026-08-31",
                "question_count": number - 1,
                "duration_minutes": None,
                "title": "MTS - WEEKLY MATH WORKSHEET",
            },
            "sections": sections,
            "verification": {"status": "PENDING"},
        }
        verification = p0_runtime.verify_spec(spec)
        if verification["status"] != "PASS":
            raise RuntimeError(f"Verification failed for {grade}: {verification}")
        spec["verification"] = {"status": "PASS", "summary": verification}
        reference = specs.write_revision(manifest, spec, worksheet_id=grade, revision="questions-r3")
        references.append(reference)
    manifest["spec_references"] = references
    manifest["status"] = "questions_generated"
    repository.save_manifest(manifest)
    print(json.dumps({"run_id": RUN_ID, "references": references, "status": manifest["status"]}, indent=2))


if __name__ == "__main__":
    main()