"""Deterministic question diversity/difficulty planning and validation for Math worksheets.

Design (see subjects/math/skills/weekly-worksheet-execution-runbook.md for how this is invoked):

- `difficulty` and `diversity` are independently configurable, parametrizable, and defaultable
  levels on the same 6-point ordinal scale: low < low_plus < medium < medium_plus < high < very_high.
  Both default to "medium_plus" (see config/base.yaml `question_design`).
- `difficulty` selects a (start_rank, end_rank) band on that scale; a slot's difficulty ramps across
  that band based on its position in the day *and* its day's position in the week (Monday easier,
  Friday harder; Q1 easier than Q10 within a day).
- `diversity` selects a minimum distinct-skill count per day and how often a spiral-review skill is
  injected into an otherwise-rotating sequence of current-week skills, so no day is a single drilled
  skill.
- `validate_progression` is the deterministic QA check: difficulty must be non-decreasing within a
  day and distinct-skill count must meet the configured minimum.
- `topic_overrides` lets a run force a subset of each grade's *daily* questions onto a specific
  topic (e.g. "60% of Grade 1's questions every day this week are addition/subtraction counting").
  Override slots are spread evenly across the day (not clustered) and still get the same
  position-based difficulty as any other slot; only the skill/topic label is overridden.
"""
from __future__ import annotations

from typing import Any

LEVELS = ["low", "low_plus", "medium", "medium_plus", "high", "very_high"]

LEVEL_ALIASES = {
    "low": "low",
    "low+": "low_plus", "low_plus": "low_plus", "low plus": "low_plus",
    "medium": "medium",
    "medium+": "medium_plus", "medium_plus": "medium_plus", "medium plus": "medium_plus",
    "high": "high",
    "very high": "very_high", "very_high": "very_high", "veryhigh": "very_high", "very+high": "very_high",
    # Backward-compatible aliases for older easy/medium/hard question tags.
    "easy": "low_plus", "hard": "high",
}

DEFAULT_DIFFICULTY = "medium_plus"
DEFAULT_DIVERSITY = "medium_plus"

# difficulty level -> (start_rank, end_rank) band on the 0..5 LEVELS scale the week/day ramps across.
_DIFFICULTY_BANDS = {
    "low": (0, 1),
    "low_plus": (0, 2),
    "medium": (1, 3),
    "medium_plus": (1, 4),
    "high": (2, 5),
    "very_high": (3, 5),
}

# diversity level -> minimum distinct skills required per day, and how often (every Nth slot) a
# spiral-review skill is injected into the rotation. None disables spiral injection.
_DIVERSITY_SETTINGS = {
    "low": {"min_distinct_skills_per_day": 1, "spiral_interval": None},
    "low_plus": {"min_distinct_skills_per_day": 2, "spiral_interval": 6},
    "medium": {"min_distinct_skills_per_day": 2, "spiral_interval": 5},
    "medium_plus": {"min_distinct_skills_per_day": 3, "spiral_interval": 4},
    "high": {"min_distinct_skills_per_day": 4, "spiral_interval": 3},
    "very_high": {"min_distinct_skills_per_day": 5, "spiral_interval": 2},
}

_LEVEL_RANK = {level: rank for rank, level in enumerate(LEVELS)}


class QuestionPlanError(ValueError):
    """Raised when a difficulty/diversity level or plan request is invalid."""


def normalize_level(value: str | None, *, default: str) -> str:
    """Normalize a user-facing spelling (e.g. "Medium+", "Very High") to a canonical level id."""
    if value is None or value == "":
        return default
    key = str(value).strip().lower()
    normalized = LEVEL_ALIASES.get(key)
    if normalized is None:
        raise QuestionPlanError(f"Unknown level {value!r}; expected one of {LEVELS} (Low/Low+/Medium/Medium+/High/Very High).")
    return normalized


def difficulty_rank_to_label(rank: int) -> str:
    return LEVELS[max(0, min(len(LEVELS) - 1, rank))]


def difficulty_for_slot(
    *, difficulty: str, day_index: int, num_days: int, slot_index: int, slots_per_day: int,
) -> str:
    """Return the difficulty level for one slot, ramping across both the day and the week."""
    start_rank, end_rank = _DIFFICULTY_BANDS[normalize_level(difficulty, default=DEFAULT_DIFFICULTY)]
    day_progress = day_index / max(1, num_days - 1)
    slot_progress = slot_index / max(1, slots_per_day - 1)
    progress = 0.5 * day_progress + 0.5 * slot_progress
    rank = round(start_rank + (end_rank - start_rank) * progress)
    return difficulty_rank_to_label(rank)


def build_skill_sequence(
    *, primary_skills: list[str], spiral_skills: list[str] | None, length: int, diversity: str,
) -> list[str]:
    """Deterministic weighted round-robin: rotate primary skills, inject spiral skills periodically."""
    if not primary_skills:
        raise QuestionPlanError("primary_skills must be non-empty.")
    spiral_skills = spiral_skills or []
    interval = _DIVERSITY_SETTINGS[normalize_level(diversity, default=DEFAULT_DIVERSITY)]["spiral_interval"]
    sequence: list[str] = []
    primary_index = spiral_index = 0
    for slot in range(length):
        use_spiral = bool(spiral_skills) and interval is not None and (slot + 1) % interval == 0
        if use_spiral:
            sequence.append(spiral_skills[spiral_index % len(spiral_skills)])
            spiral_index += 1
        else:
            sequence.append(primary_skills[primary_index % len(primary_skills)])
            primary_index += 1
    return sequence


def parse_topic_overrides(raw: str | None) -> dict[str, list[dict[str, Any]]]:
    """Parse 'grade_1:60%:Topic A; grade_4:5:Topic B' into {grade_id: [{topic, kind, value}, ...]}.

    `kind` is "percent" (value 0-100, share of that grade's per-day slot count) or "count" (a fixed
    number of slots per day). Malformed entries or out-of-range values raise QuestionPlanError.
    """
    if not raw or not raw.strip():
        return {}
    result: dict[str, list[dict[str, Any]]] = {}
    for raw_entry in raw.split(";"):
        entry = raw_entry.strip()
        if not entry:
            continue
        parts = entry.split(":", 2)
        if len(parts) != 3:
            raise QuestionPlanError(f"Malformed topic override {entry!r}; expected 'grade:amount:topic'.")
        grade_id, amount_raw, topic = (part.strip() for part in parts)
        if not grade_id or not topic:
            raise QuestionPlanError(f"Malformed topic override {entry!r}; grade and topic are required.")
        if amount_raw.endswith("%"):
            value = float(amount_raw[:-1])
            if not 0 <= value <= 100:
                raise QuestionPlanError(f"Percent override out of range in {entry!r}: {amount_raw!r}.")
            kind = "percent"
        else:
            value = int(amount_raw)
            if value < 0:
                raise QuestionPlanError(f"Count override cannot be negative in {entry!r}: {amount_raw!r}.")
            kind = "count"
        result.setdefault(grade_id, []).append({"topic": topic, "kind": kind, "value": value})
    return result


def _override_slot_count(override: dict[str, Any], slots_per_day: int) -> int:
    if override["kind"] == "percent":
        return round(slots_per_day * override["value"] / 100)
    if override["value"] > slots_per_day:
        raise QuestionPlanError(f"Fixed override count {override['value']} exceeds slots_per_day ({slots_per_day}).")
    return override["value"]


def _assign_evenly_spaced(count: int, total_slots: int, taken: set[int]) -> list[int]:
    """Return `count` slot indices spread evenly across [0, total_slots), avoiding `taken`."""
    assigned: list[int] = []
    for i in range(count):
        target = int((i + 0.5) * total_slots / count)
        slot = target
        offset = 0
        while slot in taken or slot in assigned:
            offset += 1
            if offset > total_slots:
                raise QuestionPlanError("Not enough slots to place topic overrides without overlap.")
            slot = (target + offset) % total_slots
        assigned.append(slot)
    return assigned


def _apply_topic_overrides(
    slots_per_day: int, topic_overrides: list[dict[str, Any]] | None,
) -> dict[int, str]:
    """Resolve topic overrides into {slot_index: topic}, spread evenly and non-overlapping."""
    if not topic_overrides:
        return {}
    taken: set[int] = set()
    slot_topic: dict[int, str] = {}
    total_override_slots = 0
    for override in topic_overrides:
        count = _override_slot_count(override, slots_per_day)
        total_override_slots += count
        if total_override_slots > slots_per_day:
            raise QuestionPlanError("Combined topic overrides exceed the day's slot count.")
        for slot in _assign_evenly_spaced(count, slots_per_day, taken):
            slot_topic[slot] = override["topic"]
            taken.add(slot)
    return slot_topic


def build_day_plan(
    *,
    day_id: str,
    day_index: int,
    num_days: int,
    slots_per_day: int,
    primary_skills: list[str],
    spiral_skills: list[str] | None = None,
    difficulty: str = DEFAULT_DIFFICULTY,
    diversity: str = DEFAULT_DIVERSITY,
    topic_overrides: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return one plan entry per slot: {day, slot, skill, difficulty, topic_override?}."""
    slot_topic = _apply_topic_overrides(slots_per_day, topic_overrides)
    remaining_slots = [slot for slot in range(slots_per_day) if slot not in slot_topic]
    rotation = build_skill_sequence(primary_skills=primary_skills, spiral_skills=spiral_skills, length=len(remaining_slots), diversity=diversity)
    skills: list[str] = [""] * slots_per_day
    for slot, topic in slot_topic.items():
        skills[slot] = topic
    for rotation_index, slot in enumerate(remaining_slots):
        skills[slot] = rotation[rotation_index]
    return [
        {
            "day": day_id,
            "slot": slot_index + 1,
            "skill": skills[slot_index],
            "difficulty": difficulty_for_slot(
                difficulty=difficulty, day_index=day_index, num_days=num_days,
                slot_index=slot_index, slots_per_day=slots_per_day,
            ),
            **({"topic_override": True} if slot_index in slot_topic else {}),
        }
        for slot_index in range(slots_per_day)
    ]


def build_week_plan(
    *,
    sections: list[dict[str, Any]],
    primary_skills: list[str],
    spiral_skills: list[str] | None = None,
    slots_per_day: int,
    difficulty: str = DEFAULT_DIFFICULTY,
    diversity: str = DEFAULT_DIVERSITY,
    topic_overrides: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build a full week's slot-by-slot plan, keyed by section/day id, for authoring to fill in.

    `topic_overrides` (if any) is applied identically to every day — e.g. "60% Grade 1" means 60%
    of *each* day's questions, not 60% of the week's total.
    """
    num_days = len(sections)
    return {
        section["id"]: build_day_plan(
            day_id=section["id"], day_index=day_index, num_days=num_days, slots_per_day=slots_per_day,
            primary_skills=primary_skills, spiral_skills=spiral_skills, difficulty=difficulty, diversity=diversity,
            topic_overrides=topic_overrides,
        )
        for day_index, section in enumerate(sections)
    }


def validate_progression(spec: dict[str, Any], *, diversity: str = DEFAULT_DIVERSITY) -> dict[str, Any]:
    """Deterministic QA: difficulty must be non-decreasing and net-increasing per day; skills must meet the diversity minimum."""
    min_distinct = _DIVERSITY_SETTINGS[normalize_level(diversity, default=DEFAULT_DIVERSITY)]["min_distinct_skills_per_day"]
    sections_report = []
    for section in spec.get("sections", []):
        questions = section.get("questions", [])
        ranks = [_LEVEL_RANK.get(normalize_level(q.get("difficulty"), default=DEFAULT_DIFFICULTY), _LEVEL_RANK[DEFAULT_DIFFICULTY]) for q in questions]
        skills = [q.get("skill") for q in questions]
        monotonic = all(ranks[i] >= ranks[i - 1] for i in range(1, len(ranks)))
        # A flat sequence (all equal ranks) is technically non-decreasing but is not "progressive".
        net_progresses = len(ranks) < 2 or ranks[-1] > ranks[0]
        distinct_skills = len(set(skills))
        required = min(min_distinct, len(questions))
        sections_report.append({
            "section": section.get("id"),
            "monotonic_difficulty": monotonic,
            "net_progresses": net_progresses,
            "distinct_skills": distinct_skills,
            "required_distinct_skills": required,
            "meets_diversity_minimum": distinct_skills >= required,
        })
    status = "PASS" if all(s["monotonic_difficulty"] and s["net_progresses"] and s["meets_diversity_minimum"] for s in sections_report) else "FAIL"
    return {"status": status, "sections": sections_report}
