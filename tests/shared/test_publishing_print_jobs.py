"""Focused tests for the Print Worksheets publishing utility."""
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.publishing import print_jobs  # noqa: E402

from test_publishing_archive import CONFIG as ARCHIVE_CONFIG, FakeAdapter, file_entry, folder_entry  # noqa: E402

WEEK = "2026-08-31"

CONFIG = {
    "calendar": {"week_1_start": "2026-08-10"},
    "naming": {
        "weekly": {
            "document_name_pattern": "{{PREFIX}}-{{WEEK_OF}}",
            "answer_key_suffix": "_KEY",
            "prefix_by_grade": {"grade_1": "MTS-1st", "grade_6": "MTS-6th"},
        }
    },
    "publishing": {
        **ARCHIVE_CONFIG["publishing"],
        "printing": {
            "enabled": True,
            "printer_name": "Brother HL-L2380DW series Printer",
            "duplex": "duplex_long",
            "default_source": "staging",
            "require_confirmation": True,
            "copies_by_grade": {
                "grade_1": {"student_worksheet": 5, "answer_key": 1},
                "grade_6": {"student_worksheet": 3, "answer_key": 1},
            },
        },
    },
}


class PrintAdapter(FakeAdapter):
    def __init__(self, files=None, folders=None, export_error_on=None):
        super().__init__(files=files, folders=folders)
        self.export_error_on = export_error_on
        self.exported = []

    def export_pdf(self, file_id):
        if file_id == self.export_error_on:
            raise RuntimeError("Drive export failed")
        self.exported.append(file_id)
        return b"%PDF-1.4 fake"


class FakePrinter:
    def __init__(self, error_on=None):
        self.error_on = error_on
        self.jobs = []

    def print_pdf(self, content, *, name, copies):
        if name == self.error_on:
            raise RuntimeError("printer offline")
        self.jobs.append((name, copies))
        return {"backend": "fake", "copies": copies, "file": name}


def staged_files():
    return [
        file_entry("g1w", f"MTS-1st-{WEEK}"),
        file_entry("g1k", f"MTS-1st-{WEEK}_KEY"),
        file_entry("g6w", f"MTS-6th-{WEEK}"),
        file_entry("g6k", f"MTS-6th-{WEEK}_KEY"),
    ]


def staging_adapter(**kwargs):
    return PrintAdapter(files={"staging-approved": staged_files()}, folders={"staging-approved": []}, **kwargs)


def test_dry_run_plans_configured_class_counts_and_prints_nothing():
    adapter = staging_adapter()
    printer = FakePrinter()
    record = print_jobs.run_print({"week": WEEK}, CONFIG, adapter, printer, dry_run=True)

    assert record["status"] == "dry_run"
    assert record["planned_copies"] == 5 + 1 + 3 + 1
    assert printer.jobs == []
    assert adapter.exported == []


def test_apply_spools_each_document_once_with_its_copy_count():
    adapter = staging_adapter()
    printer = FakePrinter()
    record = print_jobs.run_print({"week": WEEK}, CONFIG, adapter, printer, dry_run=False, confirm=10)

    assert record["status"] == "printed"
    assert printer.jobs == [
        (f"MTS-1st-{WEEK}", 5),
        (f"MTS-1st-{WEEK}_KEY", 1),
        (f"MTS-6th-{WEEK}", 3),
        (f"MTS-6th-{WEEK}_KEY", 1),
    ]
    assert adapter.exported == ["g1w", "g1k", "g6w", "g6k"]


def test_apply_without_a_matching_confirmation_prints_nothing():
    printer = FakePrinter()
    with pytest.raises(print_jobs.PrintError):
        print_jobs.run_print({"week": WEEK}, CONFIG, staging_adapter(), printer, dry_run=False, confirm=9)
    assert printer.jobs == []


def test_include_key_prints_only_answer_keys():
    printer = FakePrinter()
    record = print_jobs.run_print(
        {"week": WEEK, "include": "key"}, CONFIG, staging_adapter(), printer, dry_run=False, confirm=2
    )

    assert [name for name, _ in printer.jobs] == [f"MTS-1st-{WEEK}_KEY", f"MTS-6th-{WEEK}_KEY"]
    assert record["planned_copies"] == 2


def test_copies_override_replaces_only_the_named_counts():
    printer = FakePrinter()
    print_jobs.run_print(
        {"week": WEEK, "copies": "grade_6=7:2"}, CONFIG, staging_adapter(), printer, dry_run=False, confirm=15
    )

    assert dict(printer.jobs)[f"MTS-6th-{WEEK}"] == 7
    assert dict(printer.jobs)[f"MTS-6th-{WEEK}_KEY"] == 2
    assert dict(printer.jobs)[f"MTS-1st-{WEEK}"] == 5


def test_grade_without_configured_counts_is_skipped_under_all_and_refused_when_named():
    config = {
        **CONFIG,
        "publishing": {
            **CONFIG["publishing"],
            "printing": {**CONFIG["publishing"]["printing"], "copies_by_grade": {"grade_1": {"student_worksheet": 5, "answer_key": 1}}},
        },
    }
    record = print_jobs.run_print({"week": WEEK}, config, staging_adapter(), FakePrinter(), dry_run=True)
    reasons = [issue["reason"] for target in record["targets"] for issue in target["issues"]]

    assert "no_copy_counts_configured" in reasons
    assert record["planned_copies"] == 6
    with pytest.raises(print_jobs.PrintError):
        print_jobs.run_print({"week": WEEK, "grades": "grade_6"}, config, staging_adapter(), FakePrinter(), dry_run=True)


def test_missing_pair_is_reported_and_the_ready_grade_still_prints():
    adapter = PrintAdapter(
        files={"staging-approved": [file_entry("g1w", f"MTS-1st-{WEEK}"), file_entry("g1k", f"MTS-1st-{WEEK}_KEY")]},
        folders={"staging-approved": []},
    )
    printer = FakePrinter()
    record = print_jobs.run_print({"week": WEEK}, CONFIG, adapter, printer, dry_run=False, confirm=6)

    reasons = [issue["reason"] for target in record["targets"] for issue in target["issues"]]
    assert "incomplete_pair" in reasons or "missing_pair" in reasons
    assert [name for name, _ in printer.jobs] == [f"MTS-1st-{WEEK}", f"MTS-1st-{WEEK}_KEY"]


def test_publish_source_prints_the_requested_week_folder_not_the_newest():
    adapter = PrintAdapter(
        files={"week-old": staged_files(), "week-current": staged_files()},
        folders={
            "parent-1": [folder_entry("week-old", "Week_2026-09-07"), folder_entry("week-current", f"Week_{WEEK}")],
            "parent-6": [folder_entry("week-current", f"Week_{WEEK}")],
        },
    )
    record = print_jobs.run_print(
        {"week": WEEK, "source": "publish", "grades": "grade_1"}, CONFIG, adapter, FakePrinter(), dry_run=True
    )

    assert record["targets"][0]["effective_folder"]["id"] == "week-current"


def test_a_printer_failure_stops_that_target_and_records_the_remainder():
    adapter = staging_adapter()
    printer = FakePrinter(error_on=f"MTS-6th-{WEEK}")
    record = print_jobs.run_print({"week": WEEK}, CONFIG, adapter, printer, dry_run=False, confirm=10)

    assert record["status"] == "failed"
    target = record["targets"][0]
    assert [job["name"] for job in target["printed"]] == [f"MTS-1st-{WEEK}", f"MTS-1st-{WEEK}_KEY"]
    assert [job["name"] for job in target["unprinted"]] == [f"MTS-6th-{WEEK}", f"MTS-6th-{WEEK}_KEY"]


def test_printing_disabled_is_a_hard_stop():
    config = {
        **CONFIG,
        "publishing": {**CONFIG["publishing"], "printing": {**CONFIG["publishing"]["printing"], "enabled": False}},
    }
    with pytest.raises(print_jobs.PrintError):
        print_jobs.run_print({"week": WEEK}, config, staging_adapter(), FakePrinter(), dry_run=True)


def test_copy_override_syntax_is_validated():
    for bad in ("grade_1", "grade_1=two", "grade_1=-1", "grade_1=1:2:3"):
        with pytest.raises(print_jobs.PrintError):
            print_jobs.parse_copy_overrides(bad)


def test_a_subject_staged_as_pdfs_pairs_on_names_that_carry_an_extension():
    config = {
        **CONFIG,
        "naming": {
            "weekly": {
                "document_name_pattern": "{{PREFIX}}-{{WEEK_OF}}",
                "answer_key_suffix": "-KEY",
                "file_extension": ".pdf",
                "prefix_by_grade": {"grade_1": "MTS-ELA-RC-1"},
            }
        },
    }
    adapter = PrintAdapter(
        files={"staging-approved": [
            file_entry("w", f"MTS-ELA-RC-1-{WEEK}.pdf"),
            file_entry("k", f"MTS-ELA-RC-1-{WEEK}-KEY.pdf"),
        ]},
        folders={"staging-approved": []},
    )
    printer = FakePrinter()
    record = print_jobs.run_print({"week": WEEK}, config, adapter, printer, dry_run=False, confirm=6)

    assert record["status"] == "printed"
    assert printer.jobs == [(f"MTS-ELA-RC-1-{WEEK}.pdf", 5), (f"MTS-ELA-RC-1-{WEEK}-KEY.pdf", 1)]


def test_cli_holds_no_policy():
    source = (REPO / "scripts" / "print_worksheets.py").read_text(encoding="utf-8")
    assert "copies_by_grade" not in source
    assert "run_print(" in source
