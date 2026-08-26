"""Run the behavior-preserving Math migration validation gate."""

from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
TESTS = [
    REPO / "subjects/math/tests/test_p0_runtime.py",
    REPO / "subjects/math/tests/test_curriculum_backbone.py",
    REPO / "subjects/math/tests/test_repo_reconciliation.py",
]


def main() -> int:
    passed = 0
    for test_file in TESTS:
        print(f"\n== {test_file.relative_to(REPO)} ==", flush=True)
        completed = subprocess.run([sys.executable, str(test_file)], cwd=REPO)
        if completed.returncode:
            print("\nMATH_MIGRATION_GATE FAIL")
            return completed.returncode
        passed += 1
    print(f"\nMATH_MIGRATION_GATE PASS ({passed}/{len(TESTS)} suites, 14 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
