"""Publish rendered weekly worksheet artifacts from staging to the approved folder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")

sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs.google_docs_adapter import GoogleDocsAdapter  # noqa: E402
from mts.setup_project.configure import resolve_effective_config  # noqa: E402


def build_clients():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds), build("docs", "v1", credentials=creds)


def load_rendered_artifacts(run_root: Path) -> list[dict]:
    path = run_root / "rendered-artifacts.json"
    if not path.is_file():
        raise FileNotFoundError(f"No rendered-artifacts.json under {run_root}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("rendered-artifacts.json must contain rendered artifacts.")
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--subject", default="math")
    parser.add_argument("--worksheet-type", default="weekly-worksheet")
    args = parser.parse_args()

    run_root = args.run_root if args.run_root.is_absolute() else REPO / args.run_root
    effective_config = resolve_effective_config(
        {"subject": args.subject, "worksheet_type": args.worksheet_type}, repository_root=REPO
    )
    destination_id = effective_config["publishing"]["staging"]["approved_folder_id"]
    drive, docs = build_clients()
    adapter = GoogleDocsAdapter(drive, docs)

    published_pairs = {}
    published_artifacts = []
    for rendered in load_rendered_artifacts(run_root):
        grade = rendered["worksheet_id"]
        publication = adapter.publish_pair(
            {"artifact_kind": "student_worksheet", "status": "validated", "document": rendered["worksheet"]},
            {"artifact_kind": "answer_key", "status": "validated", "document": rendered["answer_key"]},
            destination_id,
        )
        published_pairs[grade] = {
            "student_worksheet": publication["student_worksheet"],
            "answer_key": publication["answer_key"],
        }
        published_artifacts.append({"worksheet_id": grade, **publication})
        print(grade)
        print(f"  worksheet={publication['student_worksheet']['webViewLink']}")
        print(f"  answer_key={publication['answer_key']['webViewLink']}")

    output = run_root / "published-artifacts.json"
    output.write_text(
        json.dumps(
            {
                "status": "published",
                "destination_id": destination_id,
                "pairs": published_pairs,
                "artifacts": published_artifacts,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"PUBLISH_PASS {len(published_pairs)} pairs")


if __name__ == "__main__":
    main()