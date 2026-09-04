"""Tests for reconstructing a WorksheetSpec from a rendered worksheet and key."""
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.publishing import reconstruct  # noqa: E402

SECTION_TITLES = {"monday": "Foundation", "tuesday": "Discover"}
SOURCES = {"student_worksheet": "doc-w", "answer_key": "doc-k"}

WORKSHEET = [
    "MTS - Weekly Math Worksheet",
    "Grade 4 - Week of September 7, 2026",
    "Monday - Foundation",
    "1. Which graph compares categories?",
    "2. What is the value of the digit 4 in 482,716?",
    "",
    "Tuesday - Discover",
    "1. How many students read exactly 2 books?",
]
KEY = [
    "ANSWER KEY",
    "Monday - Foundation",
    "1. Bar graph",
    "2. 400,000",
    "Tuesday - Discover",
    "1. 3",
]


def build(worksheet=None, key=None):
    return reconstruct.reconstruct_spec(
        worksheet or WORKSHEET,
        key or KEY,
        grade_id="grade_4",
        week_of="2026-09-07",
        title="MTS - Weekly Math Worksheet",
        section_titles=SECTION_TITLES,
        source_documents=SOURCES,
    )


def test_a_pair_reconstructs_into_globally_numbered_sections():
    spec = build()

    assert spec["worksheet"]["question_count"] == 3
    assert [section["id"] for section in spec["sections"]] == ["monday", "tuesday"]
    numbers = [q["number"] for section in spec["sections"] for q in section["questions"]]
    assert numbers == [1, 2, 3]
    # Local numbering in the document becomes global numbering in the Spec.
    assert spec["sections"][1]["questions"][0]["number"] == 3


def test_prompts_and_answers_are_paired_in_document_order():
    spec = build()
    monday = spec["sections"][0]["questions"]

    assert monday[0]["prompt"] == "Question 1: Which graph compares categories?"
    assert monday[0]["answer"] == "Bar graph"
    assert monday[1]["answer"] == 400000


def test_numeric_answers_are_coerced_and_text_answers_are_preserved():
    spec = build()
    answers = [q["answer"] for section in spec["sections"] for q in section["questions"]]
    assert answers == ["Bar graph", 400000, 3]


def test_verification_records_that_answers_were_inherited_not_recomputed():
    spec = build()

    assert spec["verification"]["status"] == "PASS"
    assert spec["verification"]["recomputed"] is False
    assert spec["verification"]["method"] == "inherited_from_source_document"
    assert spec["verification"]["source_documents"] == SOURCES
    question = spec["sections"][0]["questions"][0]
    assert question["verification"]["recomputed"] is False
    assert question["source_kind"] == "reconstructed"


def test_a_missing_answer_fails_closed():
    with pytest.raises(reconstruct.ReconstructionError, match="2 questions but 1 answers"):
        build(key=["ANSWER KEY", "Monday - Foundation", "1. Bar graph", "Tuesday - Discover", "1. 3"])


def test_a_section_present_only_in_one_document_fails_closed():
    with pytest.raises(reconstruct.ReconstructionError, match="do not match"):
        build(key=["ANSWER KEY", "Monday - Foundation", "1. Bar graph", "2. 400,000"])


def test_non_contiguous_numbering_fails_closed():
    with pytest.raises(reconstruct.ReconstructionError, match="neither local"):
        build(worksheet=["Monday - Foundation", "1. a", "3. b", "Tuesday - Discover", "1. c"])


def test_globally_numbered_source_documents_are_accepted():
    """The real orphan this feature recovers numbers Tuesday from 3, not from 1."""
    spec = build(
        worksheet=["Monday - Foundation", "1. Which graph compares categories?", "2. What is the value of the digit 4 in 482,716?", "Tuesday - Discover", "3. How many students read exactly 2 books?"],
        key=["ANSWER KEY", "Monday - Foundation", "1. Bar graph", "2. 400,000", "Tuesday - Discover", "3. 3"],
    )
    numbers = [q["number"] for section in spec["sections"] for q in section["questions"]]
    assert numbers == [1, 2, 3]


def test_a_gap_in_globally_numbered_sections_still_fails_closed():
    with pytest.raises(reconstruct.ReconstructionError, match="neither local"):
        build(worksheet=["Monday - Foundation", "1. a", "2. b", "Tuesday - Discover", "5. c"])


def test_a_numbered_line_before_any_heading_fails_closed():
    with pytest.raises(reconstruct.ReconstructionError, match="before any day heading"):
        build(worksheet=["1. stray", "Monday - Foundation", "1. a"])


def test_a_document_with_no_day_headings_fails_closed():
    with pytest.raises(reconstruct.ReconstructionError, match="No day headings"):
        build(worksheet=["MTS - Weekly Math Worksheet", "Grade 4", "some prose with no headings"])


def test_a_reconstructed_spec_renders_with_the_same_local_numbering():
    """The reconstructed Spec must round-trip back to the numbering it was parsed from."""
    import importlib.util

    spec_loader = importlib.util.spec_from_file_location(
        "render_weekly_rt", REPO / "scripts" / "render_weekly_specs_to_drive.py"
    )
    render_weekly = importlib.util.module_from_spec(spec_loader)
    spec_loader.loader.exec_module(render_weekly)

    spec = build()
    spec["worksheet"]["grade_display_name"] = "Grade 4"
    rendered = render_weekly.projection(spec, False, numbering="local")
    numbers = [line.split(".")[0] for line in rendered.splitlines() if line and line[0].isdigit()]
    assert numbers == ["1", "2", "1"]
    assert "1. Which graph compares categories?" in rendered
