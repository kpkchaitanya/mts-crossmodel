"""Print Worksheets utility: spool approved worksheet/answer-key pairs to a local printer.

Thin CLI over `mts.publishing.print_jobs.run_print`. Copy counts come from configuration; this file
holds no policy.
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
from mts.infrastructure.printing import build_printer  # noqa: E402
from mts.publishing import print_jobs  # noqa: E402
from mts.setup_project.configure import resolve_distribution_config  # noqa: E402


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
        f"source={record['source']} printer={record['printer_name']} duplex={record['duplex']} "
        f"copies={record['planned_copies']}"
    )
    for target in record["targets"]:
        print(f"  {target.get('label')} -> {target['effective_folder'].get('id')}")
        print(f"    status={target['status']}")
        if target.get("error"):
            print(f"    error={target['error']}")
        for group in ("printed", "unprinted"):
            label = "planned" if group == "unprinted" and record["dry_run"] else group
            for job in target.get(group, []):
                print(f"    {label}: {job['grade_id']} {job['role']} x{job['copies']} {job.get('name')}")
        for issue in target.get("issues", []):
            print(f"    issue={issue['reason']} {issue.get('grade_id', '')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default="current", help="'current', an instructional week number, or an ISO date.")
    parser.add_argument("--grades", default=None, help="Comma-separated grade ids; default is every configured grade.")
    parser.add_argument("--source", choices=["staging", "publish"], default=None, help="Folder preset to print from.")
    parser.add_argument("--include", choices=["both", "worksheet", "key"], default=None)
    parser.add_argument("--copies", default=None, help="Per-grade overrides, e.g. grade_5=6,grade_6=3:2.")
    parser.add_argument("--printer", default=None, help="Override the configured printer name.")
    parser.add_argument("--backend", choices=["sumatra", "acrobat"], default=None)
    parser.add_argument("--subject", default=None, help="Subject whose configuration and naming to use.")
    parser.add_argument("--confirm", type=int, default=None, help="Total copies from the dry run; required to apply.")
    parser.add_argument("--report", type=Path, default=None, help="Optional path to write the Print Record.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    group.add_argument("--apply", dest="dry_run", action="store_false", help="Send the jobs to the printer. Run --dry-run first.")
    args = parser.parse_args()

    effective_config = resolve_distribution_config(args.subject or DEFAULT_SUBJECT, repository_root=REPO)
    request = {
        "week": args.week,
        "grades": args.grades,
        "source": args.source,
        "include": args.include,
        "copies": args.copies,
        "subject": args.subject,
    }

    drive, docs = build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    printer = None
    if not args.dry_run:
        printer = build_printer(
            print_jobs.printing_settings(effective_config),
            repository_root=REPO,
            backend=args.backend,
            printer_name=args.printer,
        )
    record = print_jobs.run_print(
        request, effective_config, adapter, printer, dry_run=args.dry_run, confirm=args.confirm
    )

    report(record)
    if args.report:
        args.report.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"record={args.report}")
    if record["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
