"""Focused tests for Subject/Worksheet Type template registry routing."""
from pathlib import Path
import json
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.setup_project.configure import EffectiveConfigError, resolve_effective_config


def copy_repository(destination: Path) -> None:
    for name in ["data"]:
        shutil.copytree(REPO / name, destination / name)


def test_registered_weekly_pair_resolves_dedicated_manifest():
    resolved = resolve_effective_config({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)
    assert resolved["template_selection"]["template_manifest"] == "data/master/subjects/math/template_manifests/weekly-worksheet.json"
    assert resolved["template_selection"]["template_registry_entry"]["status"] == "active"


def test_missing_registration_fails_closed():
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        copy_repository(root)
        registry_path = root / "data" / "master" / "templates" / "registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["entries"] = [entry for entry in registry["entries"] if entry["worksheet_type_id"] != "weekly-worksheet" or entry["subject"] != "math"]
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        try:
            resolve_effective_config({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=root)
        except EffectiveConfigError as error:
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
