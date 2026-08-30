"""Form Diversity integration coverage for the Grade 5 weekly vertical slice."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "subjects" / "math" / "src"))

import subject_module


def _authored_spec(plan):
    sections = []
    number = 1
    for day_id, entries in plan.items():
        questions = []
        for entry in entries:
            questions.append({
                "number": number,
                "prompt": f"Use {entry['form_family']} to solve distinct problem {number}.",
                "skill": entry["skill"],
                "difficulty": entry["difficulty"],
                "form_family": entry["form_family"],
                "cognitive_action": entry["cognitive_action"],
                "representation": entry["representation"],
                "response_type": entry["response_type"],
                "variation_seed": entry["variation_seed"],
            })
            number += 1
        sections.append({"id": day_id, "questions": questions})
    return {"sections": sections}


def test_grade_5_seeded_coordinate_geometry_plan_passes_form_diversity_qa():
    math = subject_module.MathSubjectModule(REPO / "subjects" / "math")
    sections = [{"id": day} for day in ("monday", "tuesday", "wednesday", "thursday", "friday")]
    plan = math.build_week_plan(
        sections,
        primary_skills=["coordinate geometry basics"],
        spiral_skills=None,
        slots_per_day=2,
        difficulty="medium_plus",
        diversity="medium_plus",
        form_diversity="high",
        variation_seed=20260830,
        grade_or_course="grade_5",
    )
    assert plan == math.build_week_plan(
        sections,
        primary_skills=["coordinate geometry basics"],
        spiral_skills=None,
        slots_per_day=2,
        difficulty="medium_plus",
        diversity="medium_plus",
        form_diversity="high",
        variation_seed=20260830,
        grade_or_course="grade_5",
    )
    assert all(len({question["form_family"] for question in day}) == 2 for day in plan.values())
    result = math.check_form_diversity(
        _authored_spec(plan), grade_or_course="grade_5", form_diversity="high"
    )
    assert result["status"] == "PASS"