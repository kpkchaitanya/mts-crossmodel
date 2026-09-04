"""Format-and-deliver: reconstruct and re-render orphan staged pairs, then deliver every pair.

Thin CLI over `mts.publishing.format_deliver.run_format_and_deliver`. Rendering, Spec persistence,
and document reading are supplied here; all decisions live in the policy module.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import importlib.util
import json
import sys

SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
DEFAULT_SUBJECT = "math"
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")

sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs import google_docs_adapter  # noqa: E402
from mts.publishing import deliver as delivery_policy  # noqa: E402
from mts.publishing import format_deliver  # noqa: E402
from mts.setup_project.configure import resolve_effective_config  # noqa: E402

_render_spec = importlib.util.spec_from_file_location(
    "render_weekly_specs_to_drive", REPO / "scripts" / "render_weekly_specs_to_drive.py"
)
render_weekly = importlib.util.module_from_spec(_render_spec)
_render_spec.loader.exec_module(render_weekly)


def build_clients():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds), build("docs", "v1", credentials=creds)


def paragraph_lines(elements) -> list[str]:
    lines = []
    for element in elements:
        paragraph = element.get("paragraph")
        if paragraph:
            lines.append("".join(e.get("textRun", {}).get("content", "") for e in paragraph.get("elements", [])))
        if "table" in element:
            for row in element["table"]["tableRows"]:
                for cell in row["tableCells"]:
                    lines.extend(paragraph_lines(cell["content"]))
    return lines


def report(record: dict) -> None:
    print(f"status={record['status']} dry_run={record['dry_run']} week_of={record['week_of']}")
    for grade_id, label in record["classification"].items():
        print(f"  {grade_id}: {label}")
    for action in record["actions"]:
        print(f"  {action['grade_id']} -> {action['action']} [{action['status']}]")
        if action.get("error"):
            print(f"    error={action['error']}")
        if action.get("spec_path"):
            print(f"    spec={action['spec_path']}")
        if action.get("replaced"):
            print(f"    replaced={action['replaced']}")
    for issue in record["issues"]:
        print(f"  issue={issue['reason']} {issue.get('grade_id', '')}")
    delivery = record["delivery"]
    print(f"  delivery status={delivery['status']} folder={delivery['week_folder_name']}")
    for target in delivery["targets"]:
        print(f"    {target['label']} [{target['status']}]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default="current")
    parser.add_argument("--grades", default=None)
    parser.add_argument("--source-folder", default=None)
    # Absent by default so it stays an optional guard; config loading falls back to DEFAULT_SUBJECT.
    parser.add_argument("--subject", default=None, help="Guard: refuse if this does not match the loaded configuration's subject.")
    parser.add_argument("--worksheet-type", default="weekly-worksheet")
    parser.add_argument("--batch-id", default=None, help="Batch folder for reconstructed Specs.")
    parser.add_argument("--report", type=Path, default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    group.add_argument("--apply", dest="dry_run", action="store_false")
    args = parser.parse_args()

    subject = args.subject or DEFAULT_SUBJECT
    effective_config = resolve_effective_config(
        {"subject": subject, "worksheet_type": args.worksheet_type}, repository_root=REPO
    )
    drive, docs = build_clients()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    manifest = json.loads((REPO / effective_config["template_selection"]["template_manifest"]).read_text(encoding="utf-8"))
    naming = effective_config["naming"]["weekly"]
    numbering = effective_config.get("display_numbering", "local")
    staging_folder = effective_config["publishing"]["staging"]["render_folder_id"]

    def read_document_lines(document_id: str) -> list[str]:
        body = docs.documents().get(documentId=document_id).execute().get("body", {}).get("content", [])
        return paragraph_lines(body)

    def persist_spec(grade_id: str, week_of: str, spec: dict) -> str:
        batch_id = args.batch_id or f"reconstructed_{week_of.replace('-', '_')}"
        path = (
            REPO / "data" / "transactions" / "subjects" / subject / "grades" / grade_id
            / "cycles" / week_of / "batches" / batch_id / "worksheets" / "weekly_worksheet" / "specs" / "r1.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path.relative_to(REPO).as_posix()

    def render_pair(spec: dict, grade_id: str, week_of: str) -> dict:
        base_name = render_weekly.name_for(naming, grade_id, week_of)
        worksheet = render_weekly.copy_document(drive, manifest["worksheet_template"]["id"], staging_folder, base_name)
        key = render_weekly.copy_document(
            drive, manifest["answer_key_template"]["id"], staging_folder, base_name + naming["answer_key_suffix"]
        )
        render_weekly.render_document(
            docs, worksheet["id"], render_weekly.projection(spec, False, numbering=numbering), spec, False, numbering=numbering
        )
        render_weekly.render_document(
            docs, key["id"], render_weekly.projection(spec, True, numbering=numbering), spec, True, numbering=numbering
        )
        for document, artifact_kind in ((worksheet, "student_worksheet"), (key, "answer_key")):
            adapter.stamp_document(
                document["id"],
                delivery_policy.provenance_properties(
                    run_id=f"reconstructed-{week_of}",
                    spec_revision="r1",
                    grade_id=grade_id,
                    week_of=week_of,
                    worksheet_type=args.worksheet_type,
                    artifact_kind=artifact_kind,
                ),
            )
        return {"student_worksheet": worksheet, "answer_key": key}

    record = format_deliver.run_format_and_deliver(
        {"week": args.week, "grades": args.grades, "source_folder_id": args.source_folder, "subject": args.subject},
        effective_config,
        adapter,
        read_document_lines=read_document_lines,
        persist_spec=persist_spec,
        render_pair=render_pair,
        dry_run=args.dry_run,
    )

    report(record)
    if args.report:
        args.report.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"record={args.report}")
    if record["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
