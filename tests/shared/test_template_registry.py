"""Focused tests for Subject/Worksheet Type template registry routing."""
from pathlib import Path
import json
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "runtime"))
import policy


def copy_repository(destination: Path) -> None:
    for name in ["config", "templates"]:
        shutil.copytree(REPO / name, destination / name)


def test_registered_weekly_pair_resolves_dedicated_manifest():
    resolved = policy.resolve({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)
    assert resolved["template_selection"]["template_manifest"] == "subjects/math/config/template-manifests/weekly-worksheet.json"
    assert resolved["template_selection"]["template_registry_entry"]["status"] == "active"


def test_missing_registration_fails_closed():
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        copy_repository(root)
        registry_path = root / "templates" / "by-worksheet-type" / "template-manifest.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["entries"] = [entry for entry in registry["entries"] if entry["worksheet_type_id"] != "weekly-worksheet" or entry["subject"] != "math"]
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        try:
            policy.resolve({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=root)
        except policy.PolicyError as error:
            assert "template registration" in str(error)
        else:
            raise AssertionError("An unregistered Subject/Worksheet Type pair must fail closed.")


def main():
    tests = [test_registered_weekly_pair_resolves_dedicated_manifest, test_missing_registration_fails_closed]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
