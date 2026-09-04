"""Tests for per-day local display numbering in Weekly rendering and QA."""
from pathlib import Path
import importlib.util
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.subjects.math import p0_runtime  # noqa: E402

_spec = importlib.util.spec_from_file_location("render_weekly", REPO / "scripts" / "render_weekly_specs_to_drive.py")
render_weekly = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render_weekly)


def weekly_spec(per_day=(3, 3)):
    number = 0
    sections = []
    for index, count in enumerate(per_day):
        questions = []
        for _ in range(count):
            number += 1
            questions.append({
                "number": number,
                "prompt": f"Question {number}: prompt {number}",
                "answer": number * 2,
            })
        sections.append({"id": ["monday", "tuesday"][index], "title": "Foundation", "questions": questions})
    return {
        "worksheet": {
            "title": "MTS - Weekly Math Worksheet",
            "grade_display_name": "Grade 4",
            "week_start": "2026-09-07",
            "question_count": number,
        },
        "sections": sections,
    }


def test_local_numbering_restarts_each_day_in_the_worksheet():
    text = render_weekly.projection(weekly_spec(), False, numbering="local")
    numbered = [line for line in text.splitlines() if line and line[0].isdigit()]
    assert [line.split(".")[0] for line in numbered] == ["1", "2", "3", "1", "2", "3"]
    # The Spec's global prompt text still follows its local number.
    assert "1. prompt 4" in text


def test_the_answer_key_uses_the_same_local_numbers_as_the_worksheet():
    worksheet = render_weekly.projection(weekly_spec(), False, numbering="local")
    key = render_weekly.projection(weekly_spec(), True, numbering="local")
    worksheet_numbers = [line.split(".")[0] for line in worksheet.splitlines() if line and line[0].isdigit()]
    key_numbers = [line.split(".")[0] for line in key.splitlines() if line and line[0].isdigit()]
    assert worksheet_numbers == key_numbers
    assert "ANSWER KEY" in key


def test_global_numbering_remains_available_and_unchanged():
    text = render_weekly.projection(weekly_spec(), False, numbering="global")
    numbered = [line.split(".")[0] for line in text.splitlines() if line and line[0].isdigit()]
    assert numbered == ["1", "2", "3", "4", "5", "6"]


def test_qa_accepts_local_numbering_that_global_mode_would_reject():
    spec = weekly_spec()
    rendered = render_weekly.projection(spec, False, numbering="local")

    assert p0_runtime.targeted_text_qa_v2(rendered, spec, numbering="local")["status"] == "PASS"
    # The pre-existing global check is what produced false failures on Weekly renders.
    assert p0_runtime.targeted_text_qa_v2(rendered, spec)["status"] == "FAIL"


def test_qa_local_mode_still_fails_a_missing_day():
    spec = weekly_spec()
    rendered = render_weekly.projection(spec, False, numbering="local")
    truncated = rendered.split("Foundation")[0] + "Foundation\n1. only one\n"

    assert p0_runtime.targeted_text_qa_v2(truncated, spec, numbering="local")["status"] == "FAIL"


def test_the_weekly_worksheet_type_declares_local_numbering():
    from mts.setup_project.configure import resolve_effective_config

    resolved = resolve_effective_config(
        {"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO
    )
    assert resolved["display_numbering"] == "local"
