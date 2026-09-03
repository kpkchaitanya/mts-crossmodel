from pathlib import Path
import importlib.util
import json
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]


def test_generate_worksheet_runner_accepts_command_style_defaults_without_live_render():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_worksheet.py",
            "subject=math",
            "worksheettype=weekly",
            "week=2026-09-07",
            "grades=6",
            "gates=bypass all",
            "render=no",
            "publish=no",
            "deliver=no",
            "delivery_dry_run=no",
            "run=run-test-generate-worksheet-cli",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "RESOLVED_PARAMETERS" in completed.stdout
    assert "week=2026-09-07" in completed.stdout
    assert "GENERATE_WORKSHEET_PASS run-test-generate-worksheet-cli week=2026-09-07 worksheets=1 gates_bypassed=5" in completed.stdout


def test_generate_worksheet_runner_requires_explicit_gate_bypass():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_worksheet.py",
            "subject=math",
            "worksheettype=weekly",
            "week=2026-09-07",
            "gates=all",
            "render=no",
            "publish=no",
            "delivery_dry_run=no",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    assert completed.returncode != 0
    assert "requires explicit gates=bypass" in completed.stderr


def test_generate_worksheet_runner_builds_real_skill_based_questions_not_placeholders():
    run_id = "run-test-generate-real-questions"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_worksheet.py",
            "subject=math",
            "worksheettype=weekly",
            "week=2026-09-07",
            "grades=6",
            "gates=bypass all",
            "render=no",
            "publish=no",
            "deliver=no",
            "delivery_dry_run=no",
            "run=" + run_id,
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "Sample question" not in completed.stdout
    references = json.loads(
        (REPO / "data" / "transactions" / "runs" / run_id / "entity_references.json").read_text(encoding="utf-8")
    )["references"]
    spec_path = REPO / references[0]["spec"]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    questions = [question for section in spec["sections"] for question in section["questions"]]
    assert questions
    assert all("Sample question" not in question["prompt"] for question in questions)
    assert any("ratio" in question["skill"].lower() or "factor" in question["skill"].lower() for question in questions)
    assert any(question["prompt"] for question in questions)


def test_generate_worksheet_runner_rejects_unsupported_subject_or_type():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_worksheet.py",
            "subject=ela",
            "worksheettype=weekly",
            "gates=bypass all",
            "render=no",
            "publish=no",
            "delivery_dry_run=no",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    assert completed.returncode != 0
    assert "currently supports subject=math worksheettype=weekly" in completed.stderr


def test_generate_worksheet_runner_prefers_venv_for_operational_subprocesses():
    module_path = REPO / "scripts" / "generate_worksheet.py"
    spec = importlib.util.spec_from_file_location("generate_worksheet", module_path)
    assert spec is not None and spec.loader is not None
    generate_worksheet = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generate_worksheet)

    expected = REPO / ".venv" / "Scripts" / "python.exe"
    if expected.is_file():
        assert generate_worksheet.operational_python() == str(expected)
    else:
        assert generate_worksheet.operational_python() == sys.executable


def test_generate_worksheet_runner_rejects_singular_grade_alias_without_model_confirmation():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_worksheet.py",
            "grade=1,5,9-10",
            "week=2026-09-07",
            "gates=bypass all",
            "render=no",
            "publish=no",
            "deliver=no",
            "delivery_dry_run=no",
            "run=run-test-generate-worksheet-grade-alias",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    assert completed.returncode != 0
    assert "Did you mean 'grades'?" in completed.stderr
    assert "must confirm that interpretation" in completed.stderr


def test_generate_worksheet_runner_accepts_confirmed_canonical_grades_without_live_render():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_worksheet.py",
            "grades=1,5,9-10",
            "week=2026-09-07",
            "gates=bypass all",
            "render=no",
            "publish=no",
            "deliver=no",
            "delivery_dry_run=no",
            "run=run-test-generate-worksheet-confirmed-grades",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "grades=['grade_1', 'grade_5', 'grade_9_10']" in completed.stdout
    assert "GENERATE_WORKSHEET_PASS run-test-generate-worksheet-confirmed-grades week=2026-09-07 worksheets=3 gates_bypassed=15" in completed.stdout
    manifest = json.loads(
        (REPO / "data" / "transactions" / "runs" / "run-test-generate-worksheet-confirmed-grades" / "run_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["status"] == "publish_ready_sample"
    references = json.loads(
        (REPO / "data" / "transactions" / "runs" / "run-test-generate-worksheet-confirmed-grades" / "entity_references.json").read_text(
            encoding="utf-8"
        )
    )["references"]
    assert [reference["grade_or_course"] for reference in references] == ["grade_1", "grade_5", "grade_9_10"]
    for reference in references:
        worksheet_plan_path = REPO / reference["worksheet_plan"]
        question_plan_path = REPO / reference["question_plan"]
        spec_path = REPO / reference["spec"]
        assert worksheet_plan_path.is_file()
        assert question_plan_path.is_file()
        question_plan = json.loads(question_plan_path.read_text(encoding="utf-8"))
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        planned_slots = [slot for section in question_plan["sections"] for slot in section["slots"]]
        actual_questions = [question for section in spec["sections"] for question in section["questions"]]
        assert question_plan["source_chain"] == "yearly_curriculum -> weekly_curriculum -> worksheet_plan -> question_plan -> worksheet_spec"
        assert len(planned_slots) == spec["worksheet"]["question_count"] == len(actual_questions)
        assert {slot["source_kind"] for slot in planned_slots}
        for planned, actual in zip(planned_slots, actual_questions):
            assert actual["number"] == planned["number"]
            assert actual["section_id"] == planned["section_id"]
            assert actual["skill"] == planned["skill"]
            assert actual["difficulty"] == planned["difficulty"]
            assert actual["source_scope"] == planned["source_scope"]
            assert actual["source_kind"] == planned["source_kind"]
            assert actual["form_family"] == planned["form_family"]
    combined = next(reference for reference in references if reference["grade_or_course"] == "grade_9_10")
    combined_root = REPO / combined["worksheet_root"]
    cycle_root = combined_root.parents[3]
    assert (cycle_root / "curriculum_scopes" / "math_1.json").is_file()
    assert (cycle_root / "curriculum_scopes" / "math_2.json").is_file()
