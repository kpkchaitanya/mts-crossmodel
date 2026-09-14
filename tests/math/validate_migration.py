"""Run the behavior-preserving Math migration validation gate."""

from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
TESTS = [
    REPO / "tests/subjects/math/test_p0_runtime.py",
    REPO / "tests/subjects/math/test_curriculum_backbone.py",
    REPO / "tests/test_target_structure.py",
    REPO / "tests/test_target_data_layout.py",
]


def main() -> int:
    passed = 0
    for test_file in TESTS:
        print(f"\n== {test_file.relative_to(REPO)} ==", flush=True)
        completed = subprocess.run([sys.executable, "-m", "pytest", str(test_file)], cwd=REPO)
        if completed.returncode:
            print("\nMATH_MIGRATION_GATE FAIL")
            return completed.returncode
        passed += 1
    print(f"\nMATH_MIGRATION_GATE PASS ({passed}/{len(TESTS)} suites)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
