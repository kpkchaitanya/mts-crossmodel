"""Print Worksheets utility: spool approved worksheet/answer-key pairs to a local printer.

Thin CLI over `mts.publishing.print_jobs.run_print_batch`. Copy counts come from configuration; this
file holds no policy.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
DEFAULT_SUBJECT = "math,ela"
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
        f"color_mode={record['color_mode']} copies={record['planned_copies']}"
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
    parser.add_argument("--printer-name", "--printer", dest="printer_name", default=None, help="Select a configured printer name.")
    parser.add_argument("--backend", choices=["sumatra", "acrobat"], default=None)
    parser.add_argument("--subject", default=None, help="Comma-separated subjects; default is math,ela.")
    parser.add_argument("--confirm", type=int, default=None, help="Total copies from the dry run; required to apply.")
    parser.add_argument("--report", type=Path, default=None, help="Optional path to write the Print Record.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    group.add_argument("--apply", dest="dry_run", action="store_false", help="Send the jobs to the printer. Run --dry-run first.")
    args = parser.parse_args()

    subjects = [subject.strip() for subject in (args.subject or DEFAULT_SUBJECT).split(",") if subject.strip()]
    if not subjects or len(set(subjects)) != len(subjects):
        parser.error("--subject must contain one or more unique subject ids.")
    effective_configs = [
        resolve_distribution_config(subject, repository_root=REPO) for subject in subjects
    ]
    requests = [
        {
            "week": args.week,
            "grades": args.grades,
            "source": args.source,
            "include": args.include,
            "copies": args.copies,
            "subject": subject,
            "printer_name": args.printer_name,
        }
        for subject in subjects
    ]

    drive, docs = build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)

    def make_printer(effective_config: dict, record: dict):
        settings = print_jobs.printing_settings(effective_config)
        return build_printer(
            settings,
            repository_root=REPO,
            backend=args.backend,
            printer_name=record["printer_name"],
            color_mode=record["color_mode"],
        )

    records = print_jobs.run_print_batch(
        requests,
        effective_configs,
        adapter,
        make_printer if not args.dry_run else None,
        dry_run=args.dry_run,
        confirm=args.confirm,
    )
    print(f"subjects={','.join(subjects)} total_copies={sum(record['planned_copies'] for record in records)}")
    for subject, record in zip(subjects, records):
        print(f"subject={subject}")
        report(record)
    if args.report:
        payload = records[0] if len(records) == 1 else records
        args.report.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"record={args.report}")
    if any(record["status"] == "failed" for record in records):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
