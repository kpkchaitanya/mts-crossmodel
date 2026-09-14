"""Focused tests for the Duplicate Worksheet publishing utility."""
from pathlib import Path
import importlib.util
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.publishing import duplicate  # noqa: E402


def config(subject, prefix, *, key_suffix="_KEY", extension=""):
    return {
        "subject": subject,
        "calendar": {"week_1_start": "2026-08-17"},
        "naming": {
            "weekly": {
                "document_name_pattern": "{{PREFIX}}-{{WEEK_OF}}",
                "answer_key_suffix": key_suffix,
                "file_extension": extension,
                "prefix_by_grade": {"grade_1": prefix, "grade_6": f"{prefix}-Grade6"},
            }
        },
        "publishing": {
            "staging": {"approved_folder_id": "staging-folder"},
            "duplicate_worksheet": {
                "enabled": True,
                "default_worksheet_type": "weekly",
                "default_source_folder": "staging",
                "folders": {"staging": "publishing.staging.approved_folder_id"},
            },
        },
    }


SOURCE = config("math", "MTS-Math-Weekly")
TARGET = config("ela", "MTS-ELA-Weekly", key_suffix="-KEY", extension=".pdf")


class FakeAdapter:
    def __init__(self, files):
        self.files = files
        self.copies = []

    def list_child_files(self, folder_id):
        return [dict(item) for item in self.files.get(folder_id, [])]

    def copy_file(self, file_id, destination_id, name):
        copied = {"id": f"copy-{file_id}", "name": name, "parents": [destination_id]}
        self.copies.append((file_id, destination_id, name))
        return copied


def doc(file_id, name):
    return {"id": file_id, "name": name}


def source_files(folder="source-folder"):
    return {
        folder: [
            doc("student", "MTS-Math-Weekly-Grade6-2026-08-31"),
            doc("key", "MTS-Math-Weekly-Grade6-2026-08-31_KEY"),
        ]
    }


def request(**overrides):
    values = {
        "from_subject": "math",
        "from_worksheet_type": "weekly",
        "from_grade": "grade_6",
        "to_subject": "ela",
        "to_worksheet_type": "weekly",
        "to_grade": "grade_1",
        "week": "3",
    }
    values.update(overrides)
    return values


def test_folder_resolution_supports_default_preset_raw_id_and_url():
    assert duplicate.resolve_folder(None, SOURCE) == "staging-folder"
    assert duplicate.resolve_folder("rawFolderId123", SOURCE) == "rawFolderId123"
    assert duplicate.resolve_folder("https://drive.google.com/drive/folders/urlFolderId123", SOURCE) == "urlFolderId123"


def test_dry_run_resolves_separate_folders_and_does_not_copy():
    adapter = FakeAdapter(source_files())

    record = duplicate.run_duplicate(
        request(), SOURCE, TARGET, adapter,
        source_folder_id="source-folder", target_folder_id="target-folder", dry_run=True,
    )

    assert record["status"] == "dry_run"
    assert record["week"] == "2026-08-31"
    assert record["target_names"] == {
        "student_worksheet": "MTS-ELA-Weekly-2026-08-31.pdf",
        "answer_key": "MTS-ELA-Weekly-2026-08-31-KEY.pdf",
    }
    assert adapter.copies == []


def test_apply_copies_both_files_to_the_target_folder_under_target_names():
    adapter = FakeAdapter(source_files())

    record = duplicate.run_duplicate(
        request(), SOURCE, TARGET, adapter,
        source_folder_id="source-folder", target_folder_id="target-folder",
    )

    assert record["status"] == "duplicated"
    assert adapter.copies == [
        ("student", "target-folder", "MTS-ELA-Weekly-2026-08-31.pdf"),
        ("key", "target-folder", "MTS-ELA-Weekly-2026-08-31-KEY.pdf"),
    ]


def test_target_collision_refuses_before_copying():
    files = source_files()
    files["target-folder"] = [doc("existing", "MTS-ELA-Weekly-2026-08-31.pdf")]
    adapter = FakeAdapter(files)

    with pytest.raises(duplicate.DuplicateWorksheetError, match="already exist"):
        duplicate.run_duplicate(
            request(), SOURCE, TARGET, adapter,
            source_folder_id="source-folder", target_folder_id="target-folder",
        )
    assert adapter.copies == []


def test_ambiguous_or_incomplete_source_pair_refuses():
    adapter = FakeAdapter({"source-folder": [doc("student", "MTS-Math-Weekly-Grade6-2026-08-31")]})

    with pytest.raises(duplicate.DuplicateWorksheetError, match="one source pair"):
        duplicate.run_duplicate(
            request(), SOURCE, TARGET, adapter,
            source_folder_id="source-folder", target_folder_id="target-folder",
        )


def test_cli_requires_both_grades_and_defaults_to_apply():
    spec = importlib.util.spec_from_file_location("duplicate_worksheet_cli", REPO / "scripts" / "duplicate_worksheet.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    args = module.build_parser().parse_args([
        "--from-subject", "math", "--from-grade", "grade_6",
        "--to-subject", "ela", "--to-grade", "grade_1",
    ])

    resolved = module.resolve_request(args, SOURCE, TARGET)
    assert resolved["from_worksheet_type"] == "weekly"
    assert resolved["to_worksheet_type"] == "weekly"
    assert args.source_folder is None and args.target_folder is None
    assert args.dry_run is False
    assert module.resolve_folders(args, SOURCE, TARGET) == ("staging-folder", "staging-folder")