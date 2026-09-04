"""Deliver Worksheets utility: copy approved pairs into per-grade `Week_<WEEK_OF>` folders.

Thin CLI over `mts.publishing.deliver.run_deliver`. Pairing comes from a run root when `--run-root`
is given, and from staging document names otherwise.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
DEFAULT_SUBJECT = "math"
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")

sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs import google_docs_adapter  # noqa: E402
from mts.publishing import deliver  # noqa: E402
from mts.setup_project.configure import resolve_effective_config  # noqa: E402


def build_clients():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds), build("docs", "v1", credentials=creds)


def report(record: dict) -> None:
    print(
        f"status={record['status']} dry_run={record['dry_run']} week_of={record['week_of']} "
        f"folder={record['week_folder_name']} mode={record['mode']} source={record['source']}"
    )
    for target in record["targets"]:
        print(f"  {target['label']} ({target['grade_id']}) -> {target['folder_id']}")
        print(f"    status={target['status']}")
        if target.get("error"):
            print(f"    error={target['error']}")
        for role, item in (target.get("pair") or {}).items():
            print(f"    {role}={item['name']}")
        for role in ("student_worksheet", "answer_key"):
            if role in target and isinstance(target[role], dict):
                print(f"    {role}={target[role]['document']['webViewLink']}")
    for issue in record["issues"]:
        print(f"  issue={issue['reason']} {issue.get('grade_id', '')}")
        entries = issue.get("documents")
        if isinstance(entries, list):
            for entry in entries:
                detail = entry.get("name") or f"{entry.get('grade_id')} {entry.get('role')} {entry.get('problem')}"
                print(f"    {detail}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default="current", help="'current', an instructional week number, or an ISO date.")
    parser.add_argument("--grades", default=None, help="Comma-separated grade ids; default is every configured grade.")
    parser.add_argument("--run-root", type=Path, default=None, help="Prefer exact pairs recorded by this run.")
    parser.add_argument("--source-folder", default=None, help="Staging folder ID; defaults to the approved staging folder.")
    parser.add_argument("--mode", choices=["copy", "move"], default=None)
    parser.add_argument("--on-missing", choices=["skip", "fail"], default=None, help="Default skip: deliver what is staged.")
    # Absent by default so it stays an optional guard; config loading falls back to DEFAULT_SUBJECT.
    parser.add_argument("--subject", default=None, help="Guard: refuse if this does not match the loaded configuration's subject.")
    parser.add_argument("--worksheet-type", default="weekly-worksheet")
    parser.add_argument("--report", type=Path, default=None, help="Optional path to write the Delivery Record.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    group.add_argument("--apply", dest="dry_run", action="store_false", help="Perform the delivery. Run --dry-run first.")
    args = parser.parse_args()

    effective_config = resolve_effective_config(
        {"subject": args.subject or DEFAULT_SUBJECT, "worksheet_type": args.worksheet_type}, repository_root=REPO
    )
    run_root = None
    if args.run_root:
        run_root = args.run_root if args.run_root.is_absolute() else REPO / args.run_root
    request = {
        "week": args.week,
        "grades": args.grades,
        "mode": args.mode,
        "on_missing": args.on_missing,
        "source_folder_id": args.source_folder,
        "subject": args.subject,
    }

    drive, docs = build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    record = deliver.run_deliver(request, effective_config, adapter, dry_run=args.dry_run, run_root=run_root)

    report(record)
    if args.report:
        args.report.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"record={args.report}")
    if record["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
