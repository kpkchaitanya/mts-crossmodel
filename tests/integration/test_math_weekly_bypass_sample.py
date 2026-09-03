from pathlib import Path
import json
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
RUN_ID = "run-2026-09-07-weekly-bypass-sample"
WEEK_START = "2026-09-07"
BATCH_ID = "weekly_math_2026_09_07_bypass"
WORKSHEET_TYPE = "weekly_worksheet"
GRADES = ["grade_1", "grade_4", "grade_5", "grade_6", "grade_9_10"]
GATES = {"scope_review", "question_review", "verification_review", "formatting_review", "publish_approval"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_math_weekly_bypass_sample_writes_target_transaction_evidence():
    completed = subprocess.run(
        [sys.executable, "scripts/run_math_weekly_bypass_sample.py"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "SAMPLE_RUN_PASS" in completed.stdout

    run_root = REPO / "data" / "transactions" / "runs" / RUN_ID
    manifest = load_json(run_root / "run_manifest.json")
    references = load_json(run_root / "entity_references.json")["references"]
    assert manifest["status"] == "publish_ready_sample"
    assert manifest["week_start"] == WEEK_START
    assert len(manifest["gate_bypasses"]) == len(GRADES) * len(GATES)
    assert all(record["bypass"] is True and record["status"] == "approved" for record in manifest["gate_bypasses"])
    assert {record["gate"] for record in manifest["gate_bypasses"]} == GATES
    assert [reference["grade_or_course"] for reference in references] == GRADES

    for grade in GRADES:
        cycle_root = REPO / "data" / "transactions" / "subjects" / "math" / "grades" / grade / "cycles" / WEEK_START
        worksheet_root = cycle_root / "batches" / BATCH_ID / "worksheets" / WORKSHEET_TYPE
        assert (cycle_root / "cycle.json").is_file()
        assert (cycle_root / "weekly_curriculum.json").is_file()
        assert not (cycle_root / "batches" / "cycle.json").exists()
        assert not (cycle_root / "batches" / "weekly_curriculum.json").exists()
        assert (worksheet_root / "worksheet_plan.json").is_file()
        question_plan = load_json(worksheet_root / "question_plan.json")
        spec = load_json(worksheet_root / "specs" / "r1.json")
        verification = load_json(worksheet_root / "verification" / "verification-r1.json")
        planned_slots = [slot for section in question_plan["sections"] for slot in section["slots"]]
        actual_questions = [question for section in spec["sections"] for question in section["questions"]]
        assert len(planned_slots) == len(actual_questions)
        assert all(question["skill"] == slot["skill"] for question, slot in zip(actual_questions, planned_slots))
        assert all(question["difficulty"] == slot["difficulty"] for question, slot in zip(actual_questions, planned_slots))
        assert spec["verification"]["status"] == "PASS"
        assert verification["status"] == "PASS"
        assert (worksheet_root / "qa" / "student_worksheet.json").is_file()
        assert (worksheet_root / "qa" / "answer_key.json").is_file()
        for gate in GATES:
            approval = load_json(worksheet_root / "approvals" / f"{gate}-r1.json")
            assert approval["bypass"] is True
            assert approval["status"] == "approved"