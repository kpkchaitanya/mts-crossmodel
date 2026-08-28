"""Tests for the Math question diversity/difficulty planning and validation module."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
import question_plan as qp


SECTIONS = [{"id": "monday"}, {"id": "tuesday"}, {"id": "wednesday"}, {"id": "thursday"}, {"id": "friday"}]


def test_normalize_level_accepts_aliases_and_rejects_unknown():
    assert qp.normalize_level("Medium+", default=qp.DEFAULT_DIFFICULTY) == "medium_plus"
    assert qp.normalize_level("very high", default=qp.DEFAULT_DIFFICULTY) == "very_high"
    assert qp.normalize_level("Low+", default=qp.DEFAULT_DIFFICULTY) == "low_plus"
    assert qp.normalize_level("easy", default=qp.DEFAULT_DIFFICULTY) == "low_plus"
    assert qp.normalize_level("hard", default=qp.DEFAULT_DIFFICULTY) == "high"
    assert qp.normalize_level(None, default=qp.DEFAULT_DIFFICULTY) == qp.DEFAULT_DIFFICULTY
    try:
        qp.normalize_level("nonsense", default=qp.DEFAULT_DIFFICULTY)
    except qp.QuestionPlanError:
        pass
    else:
        raise AssertionError("Unknown level must raise QuestionPlanError.")


def test_difficulty_ramps_within_day_and_across_week_for_default_band():
    ranks = [qp._LEVEL_RANK[qp.difficulty_for_slot(difficulty="medium_plus", day_index=0, num_days=5, slot_index=i, slots_per_day=10)] for i in range(10)]
    assert ranks == sorted(ranks), "Difficulty must be non-decreasing within a day."
    monday_last = qp._LEVEL_RANK[qp.difficulty_for_slot(difficulty="medium_plus", day_index=0, num_days=5, slot_index=9, slots_per_day=10)]
    friday_first = qp._LEVEL_RANK[qp.difficulty_for_slot(difficulty="medium_plus", day_index=4, num_days=5, slot_index=0, slots_per_day=10)]
    assert friday_first >= monday_last - 1, "Friday should start at least as hard as Monday roughly ends."


def test_difficulty_band_scales_with_level():
    low_ranks = [qp._LEVEL_RANK[qp.difficulty_for_slot(difficulty="low", day_index=d, num_days=5, slot_index=9, slots_per_day=10)] for d in range(5)]
    very_high_ranks = [qp._LEVEL_RANK[qp.difficulty_for_slot(difficulty="very_high", day_index=d, num_days=5, slot_index=0, slots_per_day=10)] for d in range(5)]
    assert max(low_ranks) <= 1
    assert min(very_high_ranks) >= 3


def test_build_skill_sequence_rotates_without_immediate_repeats_and_injects_spiral_on_interval():
    seq = qp.build_skill_sequence(primary_skills=["a", "b", "c"], spiral_skills=["x"], length=8, diversity="medium_plus")
    assert len(seq) == 8
    assert all(seq[i] != seq[i - 1] for i in range(1, len(seq)))
    # medium_plus -> spiral_interval=4, so slots 4 and 8 (1-indexed) are spiral.
    assert seq[3] == "x"
    assert seq[7] == "x"


def test_build_skill_sequence_low_diversity_never_injects_spiral():
    seq = qp.build_skill_sequence(primary_skills=["a", "b"], spiral_skills=["x"], length=6, diversity="low")
    assert "x" not in seq


def test_build_week_plan_shape():
    plan = qp.build_week_plan(sections=SECTIONS, primary_skills=["a", "b", "c"], spiral_skills=["x"], slots_per_day=10)
    assert list(plan.keys()) == ["monday", "tuesday", "wednesday", "thursday", "friday"]
    for day_id, entries in plan.items():
        assert len(entries) == 10
        assert all(entry["day"] == day_id for entry in entries)
        assert [entry["slot"] for entry in entries] == list(range(1, 11))


def _spec_from_skills_and_difficulties(skills: list[str], difficulties: list[str]) -> dict:
    return {"sections": [{"id": "monday", "questions": [
        {"number": i + 1, "skill": skill, "difficulty": difficulty}
        for i, (skill, difficulty) in enumerate(zip(skills, difficulties))
    ]}]}


def test_validate_progression_passes_for_well_formed_spec():
    spec = _spec_from_skills_and_difficulties(
        ["a", "b", "c", "a", "b", "c", "a", "b"],
        ["low", "low", "low_plus", "medium", "medium", "medium_plus", "high", "high"],
    )
    result = qp.validate_progression(spec, diversity="medium_plus")
    assert result["status"] == "PASS"


def test_validate_progression_fails_on_flat_difficulty():
    spec = _spec_from_skills_and_difficulties(["a", "b", "c", "a"], ["medium", "medium", "medium", "medium"])
    result = qp.validate_progression(spec, diversity="low")
    assert result["status"] == "FAIL"
    assert result["sections"][0]["net_progresses"] is False


def test_validate_progression_fails_on_low_diversity():
    spec = _spec_from_skills_and_difficulties(["a", "a", "a", "a"], ["low", "medium", "medium_plus", "high"])
    result = qp.validate_progression(spec, diversity="medium_plus")
    assert result["status"] == "FAIL"
    assert result["sections"][0]["meets_diversity_minimum"] is False


def test_parse_topic_overrides_parses_percent_and_count_entries():
    parsed = qp.parse_topic_overrides(
        "grade_1:60%:Count on and Count down using add and subtract; grade_4:3:data and graphing"
    )
    assert parsed["grade_1"] == [{"topic": "Count on and Count down using add and subtract", "kind": "percent", "value": 60.0}]
    assert parsed["grade_4"] == [{"topic": "data and graphing", "kind": "count", "value": 3}]


def test_parse_topic_overrides_empty_and_malformed():
    assert qp.parse_topic_overrides(None) == {}
    assert qp.parse_topic_overrides("") == {}
    try:
        qp.parse_topic_overrides("grade_1:60%")
    except qp.QuestionPlanError:
        pass
    else:
        raise AssertionError("Malformed override must raise QuestionPlanError.")
    try:
        qp.parse_topic_overrides("grade_1:150%:Topic")
    except qp.QuestionPlanError:
        pass
    else:
        raise AssertionError("Out-of-range percent must raise QuestionPlanError.")


def test_build_day_plan_applies_topic_override_evenly_spaced_and_keeps_difficulty_ramp():
    plan = qp.build_day_plan(
        day_id="monday", day_index=0, num_days=5, slots_per_day=10,
        primary_skills=["a", "b", "c"], spiral_skills=["x"],
        topic_overrides=[{"topic": "override_topic", "kind": "percent", "value": 60}],
    )
    override_slots = [entry["slot"] for entry in plan if entry.get("topic_override")]
    assert len(override_slots) == 6
    assert all(entry["skill"] == "override_topic" for entry in plan if entry.get("topic_override"))
    # Overridden slots must not all cluster at one end of the day.
    assert min(override_slots) <= 4 and max(override_slots) >= 7
    ranks = [qp._LEVEL_RANK[entry["difficulty"]] for entry in plan]
    assert ranks == sorted(ranks), "Override slots must not break the difficulty ramp."


def test_build_day_plan_rejects_overrides_exceeding_slot_count():
    try:
        qp.build_day_plan(
            day_id="monday", day_index=0, num_days=5, slots_per_day=4,
            primary_skills=["a", "b"],
            topic_overrides=[{"topic": "x", "kind": "count", "value": 3}, {"topic": "y", "kind": "count", "value": 3}],
        )
    except qp.QuestionPlanError:
        pass
    else:
        raise AssertionError("Combined overrides exceeding slots_per_day must raise QuestionPlanError.")
