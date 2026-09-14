"""Prepare a Weekly Worksheet Spec from configured counts and source questions."""
from __future__ import annotations

from copy import deepcopy
import argparse
import json
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO / "data" / "config" / "worksheet_types" / "weekly_worksheet.yaml"
GRADE_CATALOG = REPO / "data" / "master" / "subjects" / "math" / "grade_course_catalog.json"


def load_questions(source: Path) -> list[dict]:
    data = json.loads(source.read_text(encoding="utf-8"))
    return [question for section in data.get("sections", []) for question in section.get("questions", [])]


def select_questions(questions: list[dict], grade_config: dict) -> list[dict]:
    split = grade_config.get("grade_split")
    source_split = grade_config.get("source_selector")
    if not split:
        return questions[: grade_config["questions_per_week"]]
    if not source_split or set(split) != set(source_split):
        raise ValueError("A split requires matching source_selector values.")
    selected = []
    for key, count in split.items():
        group = [question for question in questions if question.get("grade") == source_split[key]]
        if len(group) < count:
            raise ValueError(f"Source does not contain {count} questions for split {key}.")
        selected.extend(group[:count])
    return selected


def grade_display_name(grade_id: str) -> str:
    catalog = json.loads(GRADE_CATALOG.read_text(encoding="utf-8"))
    for entry in catalog.get("grades_and_courses", []):
        if entry.get("id") == grade_id:
            return str(entry["display_name"])
    raise ValueError(f"Grade/course {grade_id!r} is not registered in the Math grade catalog.")


def build_spec(source_data: dict, questions: list[dict], sections: list[dict], grade_config: dict, grade_id: str) -> dict:
    expected = grade_config["questions_per_week"]
    daily = grade_config["questions_per_day"]
    if expected != daily * len(sections):
        raise ValueError("questions_per_week must equal questions_per_day times configured sections.")
    if len(questions) != expected:
        raise ValueError(f"Selected question count {len(questions)} does not equal configured total {expected}.")

    output_sections = []
    offset = 0
    for section in sections:
        day_questions = questions[offset:offset + daily]
        offset += daily
        output_sections.append({
            "id": section["id"],
            "title": section["title"],
            "questions": [dict(question, number=number) for number, question in enumerate(day_questions, start=offset - daily + 1)],
        })

    worksheet = deepcopy(source_data.get("worksheet", {}))
    worksheet.update({
        "question_count": expected,
        "grade_or_course": grade_id,
        "grade_display_name": grade_display_name(grade_id),
    })
    return {
        "worksheet": worksheet,
        "curriculum": deepcopy(source_data.get("curriculum", {})),
        "sections": output_sections,
        "verification": {"status": "PENDING"},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a configured Weekly Worksheet Spec.")
    parser.add_argument("--source", type=Path, required=True, help="Source Spec containing candidate questions.")
    parser.add_argument("--destination", type=Path, required=True, help="Output Spec path.")
    parser.add_argument("--grade-id", required=True, help="Grade/course key from the Worksheet Type configuration.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Weekly Worksheet Type YAML.")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    grade_config = config["grade_defaults"][args.grade_id]
    source_data = json.loads(args.source.read_text(encoding="utf-8"))
    questions = select_questions(load_questions(args.source), grade_config)
    spec = build_spec(source_data, questions, config["sections"], grade_config, args.grade_id)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {args.destination}")
    print(f"COUNT {len(questions)} DAILY {grade_config['questions_per_day']}")


if __name__ == "__main__":
    main()