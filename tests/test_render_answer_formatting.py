"""Tests for the configurable answer-key decimal rounding in render_weekly_specs_to_drive."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import render_weekly_specs_to_drive as render  # noqa: E402


def test_display_answer_rounds_only_when_more_than_noise_threshold_decimals():
    # Floating-point noise (many raw decimal digits) gets rounded for display.
    assert render.display_answer(3.9999999999999996) == "4.00"


def test_display_answer_leaves_clean_short_decimals_unrounded():
    # Already-clean values with <= 3 decimal digits are shown as-is, not force-padded/truncated.
    assert render.display_answer(3.0) == "3.0"
    assert render.display_answer(0.125) == "0.125"
    assert render.display_answer(9.0) == "9.0"


def test_display_answer_decimal_places_is_configurable():
    assert render.display_answer(3.14159265, decimal_places=4) == "3.1416"
    assert render.display_answer(3.9999999999999996, decimal_places=0) == "4"


def test_display_answer_noise_threshold_is_configurable():
    assert render.display_answer(3.14159, noise_threshold=1) == "3.14"
    assert render.display_answer(3.14, noise_threshold=1) == "3.14"


def test_display_answer_leaves_ints_and_lists_readable():
    assert render.display_answer(7) == "7"
    assert render.display_answer([2, 11]) == "2, 11"
    assert render.display_answer([2, 3.9999999999999996]) == "2, 4.00"


def test_grade_display_name_prefers_human_label_and_preserves_legacy_specs():
    assert render.grade_display_name({"worksheet": {"grade": "grade_5", "grade_display_name": "Grade 5"}}) == "Grade 5"
    assert render.grade_display_name({"worksheet": {"grade": "grade_5"}}) == "grade_5"


def test_display_question_prompt_removes_canonical_storage_prefix():
    assert render.display_question_prompt({"number": 12, "prompt": "Question 12: Solve: 3 + 4."}) == "Solve: 3 + 4."
    assert render.display_question_prompt({"number": 12, "prompt": "Solve: 3 + 4."}) == "Solve: 3 + 4."


def test_answer_key_line_uses_only_number_and_answer():
    assert render.answer_key_line({"number": 12, "answer": 7}) == "12. 7"


def test_spec_paths_for_run_prefers_target_entity_references(tmp_path):
    run_root = tmp_path / "data" / "transactions" / "runs" / "run-test"
    spec_path = render.REPO / "data" / "transactions" / "subjects" / "math" / "grades" / "grade_4" / "cycles" / "2026-09-07" / "batches" / "sample" / "worksheets" / "weekly_worksheet" / "specs" / "r1.json"
    run_root.mkdir(parents=True)
    (run_root / "entity_references.json").write_text(
        '{"references": [{"grade_or_course": "grade_4", "spec": "'
        + spec_path.relative_to(render.REPO).as_posix()
        + '"}]}\n',
        encoding="utf-8",
    )

    assert render.spec_paths_for_run(run_root) == [("grade_4", spec_path)]
    assert render.spec_paths_for_run(run_root, "grade-4") == [("grade_4", spec_path)]
