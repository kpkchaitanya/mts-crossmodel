"""CLI for duplicating one worksheet pair between subject configurations."""
from pathlib import Path
import argparse
import sys

REPO = Path(__file__).resolve().parents[1]
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")
sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs import google_docs_adapter  # noqa: E402
from mts.publishing import duplicate  # noqa: E402
from mts.setup_project.configure import resolve_distribution_config  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-subject", required=True)
    parser.add_argument("--from-worksheet-type", default=None)
    parser.add_argument("--from-grade", required=True)
    parser.add_argument("--to-subject", required=True)
    parser.add_argument("--to-worksheet-type", default=None)
    parser.add_argument("--to-grade", required=True)
    parser.add_argument("--week", default="current")
    parser.add_argument("--source-folder", default=None, help="Configured preset, Drive folder ID, or folder URL.")
    parser.add_argument("--target-folder", default=None, help="Configured preset, Drive folder ID, or folder URL.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    group.add_argument("--apply", dest="dry_run", action="store_false")
    return parser


def resolve_folders(args, source_config, target_config) -> tuple[str, str]:
    source_folder = duplicate.resolve_folder(args.source_folder, source_config)
    target_folder = (
        duplicate.resolve_folder(args.target_folder, target_config)
        if args.target_folder
        else source_folder
    )
    return source_folder, target_folder


def resolve_request(args, source_config, target_config) -> dict:
    request = vars(args).copy()
    request["from_worksheet_type"] = args.from_worksheet_type or duplicate.duplicate_settings(
        source_config
    ).get("default_worksheet_type", "weekly")
    request["to_worksheet_type"] = args.to_worksheet_type or duplicate.duplicate_settings(
        target_config
    ).get("default_worksheet_type", "weekly")
    return request


def main() -> None:
    args = build_parser().parse_args()
    source_config = resolve_distribution_config(args.from_subject, repository_root=REPO)
    target_config = resolve_distribution_config(args.to_subject, repository_root=REPO)
    source_folder, target_folder = resolve_folders(args, source_config, target_config)
    request = resolve_request(args, source_config, target_config)
    drive, docs = _build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    record = duplicate.run_duplicate(
        request, source_config, target_config, adapter,
        source_folder_id=source_folder, target_folder_id=target_folder, dry_run=args.dry_run,
    )
    print(f"status={record['status']} dry_run={record['dry_run']} week={record['week']}")
    print(f"source={record['source_pair']['student_worksheet']['name']}")
    print(f"source_key={record['source_pair']['answer_key']['name']}")
    print(f"source_folder={record['source_folder']} target_folder={record['target_folder']}")
    print(f"target={record['target_names']['student_worksheet']}")
    print(f"target_key={record['target_names']['answer_key']}")


def _build_clients():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN), ["https://www.googleapis.com/auth/drive"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds), build("docs", "v1", credentials=creds)


if __name__ == "__main__":
    main()
