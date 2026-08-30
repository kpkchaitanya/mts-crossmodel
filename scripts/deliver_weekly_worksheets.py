"""Final Delivery: copy approved staged weekly worksheets into per-grade parent Drive folders.

Staging (``outputs-copilot`` / the approved staging Drive folder) remains the audit trail. This step
creates one ``Week_<WEEK_OF>`` folder under each grade's configured parent folder and places the
approved Student Worksheet and Answer Key inside it.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import argparse
import json
import sys

SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")

sys.path.insert(0, str(REPO / "src" / "runtime"))
sys.path.insert(0, str(REPO / "src" / "rendering"))
import google_docs_adapter  # noqa: E402
import policy  # noqa: E402


def normalize_grade_id(worksheet_id: str) -> str:
    return worksheet_id.strip().replace("-", "_")


def load_pairs(run_root: Path) -> tuple[dict[str, dict], Path]:
    """Read staged pairs from a run's published or rendered artifact record."""
    for filename in ("published-artifacts.json", "rendered-artifacts.json"):
        path = run_root / filename
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "pairs" in payload:
            pairs = {
                normalize_grade_id(grade_id): {
                    "student_worksheet": pair["student_worksheet"],
                    "answer_key": pair["answer_key"],
                }
                for grade_id, pair in payload["pairs"].items()
            }
        else:
            pairs = {
                normalize_grade_id(entry["worksheet_id"]): {
                    "student_worksheet": entry["worksheet"],
                    "answer_key": entry["answer_key"],
                }
                for entry in payload["artifacts"]
            }
        return pairs, path
    raise FileNotFoundError(f"No published-artifacts.json or rendered-artifacts.json under {run_root}")


def resolve_week_of(value: str, calendar: dict) -> str:
    """Resolve --week-of as an ISO date, an instructional week number, or 'current'."""
    week_1_start = date.fromisoformat(str(calendar["week_1_start"]))
    if value == "current":
        today = date.today()
        return (today.fromordinal(today.toordinal() - today.weekday())).isoformat()
    if value.isdigit():
        return date.fromordinal(week_1_start.toordinal() + 7 * (int(value) - 1)).isoformat()
    parsed = date.fromisoformat(value)
    return date.fromordinal(parsed.toordinal() - parsed.weekday()).isoformat()


def build_clients():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds), build("docs", "v1", credentials=creds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--week-of", required=True, help="ISO date, instructional week number, or 'current'.")
    parser.add_argument("--subject", default="math")
    parser.add_argument("--worksheet-type", default="weekly-worksheet")
    parser.add_argument("--grades", default=None, help="Comma-separated grade ids; default is every staged grade.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run_root = args.run_root if args.run_root.is_absolute() else REPO / args.run_root
    resolved_policy = policy.resolve(
        {"subject": args.subject, "worksheet_type": args.worksheet_type}, repository_root=REPO
    )
    publishing = resolved_policy["publishing"]
    delivery = publishing["final_delivery"]
    if not delivery["enabled"]:
        raise SystemExit("Final Delivery is disabled in configuration.")
    destinations = delivery["destinations_by_grade"]

    week_of = resolve_week_of(args.week_of, dict(resolved_policy["calendar"]))
    folder_name = delivery["week_folder_pattern"].replace("{{WEEK_OF}}", week_of)

    pairs, source_path = load_pairs(run_root)
    selected = [normalize_grade_id(g) for g in args.grades.split(",")] if args.grades else sorted(pairs)
    missing = [grade_id for grade_id in selected if grade_id not in destinations]
    if missing:
        raise SystemExit(f"No configured Final Delivery parent folder for: {', '.join(missing)}")

    print(f"source={source_path.relative_to(REPO).as_posix()} week_folder={folder_name} mode={delivery['mode']}")
    if args.dry_run:
        for grade_id in selected:
            print(f"  {grade_id} -> {destinations[grade_id]['folder_id']}/{folder_name}")
        print(f"DRY_RUN {len(selected)} pairs")
        return

    drive, docs = build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    results: dict[str, dict] = {}
    for grade_id in selected:
        parent_id = destinations[grade_id]["folder_id"]
        week_folder = adapter.ensure_child_folder(parent_id, folder_name)
        pair = pairs[grade_id]
        delivered = adapter.deliver_pair(
            {"artifact_kind": "student_worksheet", "status": "published", "document": pair["student_worksheet"]},
            {"artifact_kind": "answer_key", "status": "published", "document": pair["answer_key"]},
            week_folder["id"],
            mode=delivery["mode"],
            deliver_answer_key=delivery["deliver_answer_key"],
        )
        results[grade_id] = {"parent_folder_id": parent_id, "week_folder": week_folder, **delivered}
        print(f"{grade_id} -> {week_folder.get('webViewLink', week_folder['id'])}")
        for kind in ("student_worksheet", "answer_key"):
            if kind in delivered:
                print(f"  {kind}={delivered[kind]['document']['webViewLink']}")

    output = run_root / "delivered-artifacts.json"
    output.write_text(
        json.dumps(
            {
                "status": "delivered",
                "audience": delivery["audience"],
                "week_of": week_of,
                "week_folder_name": folder_name,
                "mode": delivery["mode"],
                "source_artifacts": source_path.relative_to(REPO).as_posix(),
                "grades": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"DELIVERY_PASS {len(results)} pairs")


if __name__ == "__main__":
    main()
