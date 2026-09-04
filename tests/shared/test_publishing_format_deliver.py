"""Tests for the format-and-deliver composition."""
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.publishing import format_deliver  # noqa: E402

from test_publishing_deliver import CONFIG as DELIVER_CONFIG, FakeAdapter, doc  # noqa: E402

CONFIG = {
    **DELIVER_CONFIG,
    "sections": [{"id": "monday", "title": "Foundation"}, {"id": "tuesday", "title": "Discover"}],
    "worksheet_title": "MTS - Weekly Math Worksheet",
    "publishing": {
        **DELIVER_CONFIG["publishing"],
        "provenance": {"enabled": True, "require_stamp_for_delivery": False},
    },
}

WORKSHEET_LINES = ["Monday - Foundation", "1. Which graph?", "Tuesday - Discover", "1. How many?"]
KEY_LINES = ["ANSWER KEY", "Monday - Foundation", "1. Bar graph", "Tuesday - Discover", "1. 3"]


def stamped(document, grade_id, week="2026-08-31"):
    return {**document, "appProperties": {"mts_run_id": "run-1", "mts_grade_id": grade_id, "mts_week_of": week}}


def staging(grade_6_stamped=False):
    six = [
        doc("g6", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31"),
        doc("g6k", "MTS-Math-6thGrade-WeeklyWorksheet-2026-08-31_KEY"),
    ]
    if grade_6_stamped:
        six = [stamped(six[0], "grade_6"), stamped(six[1], "grade_6")]
    return {"staging-approved": six}


class Recorder:
    def __init__(self, render_error=False):
        self.persisted = []
        self.rendered = []
        self.render_error = render_error

    def read_lines(self, document_id):
        return KEY_LINES if document_id.endswith("k") else WORKSHEET_LINES

    def persist(self, grade_id, week_of, spec):
        self.persisted.append((grade_id, week_of, spec))
        return f"data/.../{grade_id}/{week_of}/r1.json"

    def render(self, spec, grade_id, week_of):
        if self.render_error:
            raise RuntimeError("template unavailable")
        self.rendered.append((grade_id, week_of, spec["worksheet"]["question_count"]))
        return {
            "student_worksheet": {"id": f"new-{grade_id}", "name": "rendered"},
            "answer_key": {"id": f"new-{grade_id}k", "name": "rendered_KEY"},
        }


def run(adapter, recorder, dry_run=True, grades="grade_6"):
    return format_deliver.run_format_and_deliver(
        {"week": "2026-08-31", "grades": grades},
        CONFIG,
        adapter,
        read_document_lines=recorder.read_lines,
        persist_spec=recorder.persist,
        render_pair=recorder.render,
        dry_run=dry_run,
    )


def test_a_stamped_pair_is_classified_conformant_and_delivered_as_is():
    adapter = FakeAdapter(files=staging(grade_6_stamped=True))
    recorder = Recorder()
    record = run(adapter, recorder, dry_run=False)

    assert record["classification"]["grade_6"] == "conformant"
    assert recorder.persisted == [] and recorder.rendered == []
    assert adapter.deliveries == [("g6", "g6k", "week-of-parent-6", "copy")]


def test_an_unstamped_pair_is_reconstructed_re_rendered_then_delivered():
    adapter = FakeAdapter(files=staging())
    recorder = Recorder()
    record = run(adapter, recorder, dry_run=False)

    assert record["classification"]["grade_6"] == "orphan"
    assert recorder.persisted[0][0] == "grade_6"
    # Two days, one question each, globally numbered in the Spec.
    assert recorder.rendered == [("grade_6", "2026-08-31", 2)]
    # Delivery uses the freshly rendered documents, not the orphan originals.
    assert adapter.deliveries == [("new-grade_6", "new-grade_6k", "week-of-parent-6", "copy")]


def test_a_dry_run_reconstructs_nothing_and_delivers_nothing():
    adapter = FakeAdapter(files=staging())
    recorder = Recorder()
    record = run(adapter, recorder, dry_run=True)

    assert record["actions"][0]["action"] == "reconstruct_and_rerender"
    assert record["actions"][0]["status"] == "planned"
    assert recorder.persisted == [] and recorder.rendered == []
    assert adapter.deliveries == [] and adapter.week_folders == []


def test_a_grade_awaiting_rebuild_is_reported_as_pending_not_missing():
    """"No pair found" would misstate a dry run: the pair does not exist yet, by design."""
    record = run(FakeAdapter(files=staging()), Recorder(), dry_run=True)
    target = record["delivery"]["targets"][0]

    assert target["status"] == "pending_rebuild"
    assert target["error"] is None


def test_a_failed_rebuild_is_recorded_and_does_not_block_other_grades():
    adapter = FakeAdapter(files=staging())
    recorder = Recorder(render_error=True)
    record = run(adapter, recorder, dry_run=False)

    assert record["status"] == "failed"
    assert record["actions"][0]["status"] == "failed"
    assert "template unavailable" in record["actions"][0]["error"]
    assert adapter.deliveries == []


def test_the_record_names_the_documents_a_rebuild_replaced():
    adapter = FakeAdapter(files=staging())
    record = run(adapter, Recorder(), dry_run=False)

    assert record["actions"][0]["replaced"] == {"student_worksheet": "g6", "answer_key": "g6k"}
    assert record["actions"][0]["spec_path"].endswith("r1.json")


def test_a_mismatched_subject_filter_fails_closed_before_reconstructing_anything():
    adapter = FakeAdapter(files=staging())
    recorder = Recorder()
    with pytest.raises(format_deliver.delivery_policy.DeliveryError, match="does not match"):
        format_deliver.run_format_and_deliver(
            {"week": "2026-08-31", "grades": "grade_6", "subject": "ela"},
            CONFIG,
            adapter,
            read_document_lines=recorder.read_lines,
            persist_spec=recorder.persist,
            render_pair=recorder.render,
            dry_run=True,
        )
    assert recorder.persisted == [] and recorder.rendered == []
