"""Archive Folder utility: move a folder's previous set of loose files into its Archive folder.

Thin CLI over `mts.publishing.archive.run_archive`. All decisions live in that module so the
publishing pipeline can later invoke the same behavior without duplicating it.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")

sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs import google_docs_adapter  # noqa: E402
from mts.publishing import archive  # noqa: E402
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
    print(f"status={record['status']} dry_run={record['dry_run']} archive_folder={record['archive_folder_name']}")
    for target in record["targets"]:
        effective = target["effective_folder"]
        print(f"  {target['label']} [{target['folder_type']}] {target['folder_id']} -> {effective.get('name', effective['id'])}")
        print(f"    status={target['status']}")
        if target.get("error"):
            print(f"    error={target['error']}")
        for item in target["moved"]:
            print(f"    moved   {item['name']}")
        for item in target["unmoved"]:
            print(f"    pending {item['name']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, help="Preset name (staging, publish), Drive folder ID, or folder URL.")
    parser.add_argument("--folder-type", choices=["folder", "parent"], default=None)
    parser.add_argument("--folder-date", default=None, help="Parent mode only: 'latest', an ISO date, or a folder name.")
    parser.add_argument("--grades", default=None, help="Comma-separated grade ids; default is every configured grade.")
    parser.add_argument("--subject", default="math")
    parser.add_argument("--worksheet-type", default="weekly-worksheet")
    parser.add_argument("--report", type=Path, default=None, help="Optional path to write the Archive Record.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    group.add_argument("--apply", dest="dry_run", action="store_false", help="Perform the moves. Run --dry-run first.")
    args = parser.parse_args()

    effective_config = resolve_effective_config(
        {"subject": args.subject, "worksheet_type": args.worksheet_type}, repository_root=REPO
    )
    request = {
        "folder": args.folder,
        "folder_type": args.folder_type,
        "folder_date": args.folder_date,
        "grades": args.grades,
    }

    drive, docs = build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    record = archive.run_archive(request, effective_config, adapter, dry_run=args.dry_run)

    report(record)
    if args.report:
        args.report.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"record={args.report}")
    if record["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
