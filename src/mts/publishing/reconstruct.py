"""Reconstruct a WorksheetSpec from an already-rendered worksheet and answer key.

This exists for documents that were authored straight into Drive and have no Spec of record. Parsing
is inference, so every ambiguity fails closed rather than being resolved: a reconstructed Spec that
misstates a question or an answer is worse than no Spec at all.

Answers are carried over from the source key, not recomputed. The Spec records that explicitly so an
inherited answer is never mistaken for an independently verified one.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
import re

NUMBERED_LINE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")


class ReconstructionError(ValueError):
    """Raised when a document cannot be parsed into a trustworthy Spec."""


def parse_sections(lines: Sequence[str], section_ids: Sequence[str]) -> list[dict[str, Any]]:
    """Split numbered lines into the configured day sections, in document order."""
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    remaining = list(section_ids)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        heading = _matching_section(line, remaining)
        if heading:
            remaining.remove(heading)
            current = {"id": heading, "items": []}
            sections.append(current)
            continue
        match = NUMBERED_LINE.match(line)
        if not match:
            continue
        if current is None:
            raise ReconstructionError(f"Numbered line before any day heading: {line!r}")
        current["items"].append({"local_number": int(match.group(1)), "text": match.group(2)})

    if not sections:
        raise ReconstructionError(f"No day headings found; expected one of: {', '.join(section_ids)}")
    expected_start = 1
    for section in sections:
        expected_start = _check_local_numbering(section, expected_start=expected_start)
    return sections


def _matching_section(line: str, section_ids: Sequence[str]) -> str | None:
    lowered = line.lower()
    for section_id in section_ids:
        if lowered.startswith(section_id):
            return section_id
    return None


def _check_local_numbering(section: Mapping[str, Any], *, expected_start: int) -> int:
    """Accept either per-day local numbering (1..n) or global numbering continuing from
    the previous section. The printed number is not used to build the Spec (order is), so this
    exists only to reject a genuinely garbled document, not to enforce one authoring convention."""
    numbers = [item["local_number"] for item in section["items"]]
    if not numbers:
        raise ReconstructionError(f"Section {section['id']} has no numbered lines.")
    local = list(range(1, len(numbers) + 1))
    global_continuous = list(range(expected_start, expected_start + len(numbers)))
    if numbers not in (local, global_continuous):
        raise ReconstructionError(
            f"Section {section['id']} numbering is neither local ({local[0]}..{local[-1]}) nor "
            f"continuing globally ({global_continuous[0]}..{global_continuous[-1]}): {numbers}"
        )
    return expected_start + len(numbers)


def reconstruct_spec(
    worksheet_lines: Sequence[str],
    answer_key_lines: Sequence[str],
    *,
    grade_id: str,
    week_of: str,
    title: str,
    section_titles: Mapping[str, str],
    source_documents: Mapping[str, str],
) -> dict[str, Any]:
    """Build a Spec from a rendered pair, failing closed on any worksheet/key disagreement."""
    section_ids = list(section_titles)
    prompts = parse_sections(worksheet_lines, section_ids)
    answers = parse_sections(answer_key_lines, section_ids)

    if [section["id"] for section in prompts] != [section["id"] for section in answers]:
        raise ReconstructionError(
            f"Worksheet sections {[s['id'] for s in prompts]} do not match key sections {[s['id'] for s in answers]}."
        )
    for prompt_section, answer_section in zip(prompts, answers):
        if len(prompt_section["items"]) != len(answer_section["items"]):
            raise ReconstructionError(
                f"Section {prompt_section['id']}: {len(prompt_section['items'])} questions but "
                f"{len(answer_section['items'])} answers."
            )

    sections: list[dict[str, Any]] = []
    global_number = 0
    for prompt_section, answer_section in zip(prompts, answers):
        questions = []
        for prompt_item, answer_item in zip(prompt_section["items"], answer_section["items"]):
            global_number += 1
            questions.append({
                "id": f"{grade_id}-q{global_number}",
                "number": global_number,
                "section_id": prompt_section["id"],
                "prompt": f"Question {global_number}: {prompt_item['text']}",
                "answer": _coerce_answer(answer_item["text"]),
                "source_kind": "reconstructed",
                "source_scope": grade_id,
                "standards": [],
                "confidence": "inferred",
                "verification": {
                    "method": "inherited_from_source_document",
                    "recomputed": False,
                    "source_document_id": source_documents["answer_key"],
                },
            })
        sections.append({
            "id": prompt_section["id"],
            "title": section_titles[prompt_section["id"]],
            "questions": questions,
        })

    return {
        "worksheet": {
            "grade": grade_id,
            "grade_or_course": grade_id,
            "question_count": global_number,
            "title": title,
            "week_start": week_of,
        },
        "sections": sections,
        "verification": {
            "status": "PASS",
            "method": "inherited_from_source_document",
            "recomputed": False,
            "source_documents": dict(source_documents),
        },
    }


def _coerce_answer(text: str) -> Any:
    """Keep numeric answers numeric so downstream formatting behaves as it does for authored Specs."""
    candidate = text.replace(",", "")
    try:
        return int(candidate)
    except ValueError:
        pass
    try:
        return float(candidate)
    except ValueError:
        return text


__all__ = ["ReconstructionError", "parse_sections", "reconstruct_spec"]
