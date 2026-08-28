"""Render approved Math Specs into copied Google Docs staging artifacts."""
from __future__ import annotations

from pathlib import Path
import json
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
SPECS = REPO / "runs" / "math" / "run-2026-08-24-weekly" / "specs"
OUTPUT = REPO / "runs" / "math" / "run-2026-08-24-weekly" / "rendered-artifacts.json"
STAGING_FOLDER = "1FUZ5hC4hpKEZwirG-p4bKpDlPiN8IBfL"
WORKSHEET_TEMPLATE = "1ng3-EQmHRQfUftIEoQnyh7N43hzi1ViUjf44LTgPqo0"
ANSWER_KEY_TEMPLATE = "1uBKm2dzzeqy3gwYRxDAG34HGFnTRXAqJJb1sLJViNIo"
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")


def display_answer(answer: object) -> str:
    if isinstance(answer, list):
        return ", ".join(str(item) for item in answer)
    return str(answer)


def projection(spec: dict, answer_key: bool) -> str:
    lines = [spec["worksheet"]["grade"], f"Week of {spec['worksheet']['week_start']}", ""]
    for section in spec["sections"]:
        lines.extend([section["title"], ""])
        for question in section["questions"]:
            value = display_answer(question["answer"]) if answer_key else question["prompt"]
            lines.append(f"{question['number']}. {value}")
        lines.append("")
    if answer_key:
        lines.insert(0, "ANSWER KEY")
    return "\n".join(lines).strip() + "\n"


def copy_document(drive, template_id: str, name: str) -> dict:
    return drive.files().copy(
        fileId=template_id,
        body={"name": name, "parents": [STAGING_FOLDER]},
        fields="id,name,webViewLink,parents",
    ).execute()


def document_text(docs, document_id: str) -> tuple[str, list[dict]]:
    body = docs.documents().get(documentId=document_id).execute().get("body", {}).get("content", [])
    chunks = []
    for item in body:
        for element in item.get("paragraph", {}).get("elements", []):
            text_run = element.get("textRun")
            if text_run:
                chunks.append(text_run.get("content", ""))
    return "".join(chunks), body


def render_document(docs, document_id: str, content: str) -> None:
    existing, body = document_text(docs, document_id)
    if "{{CONTENT}}" in existing:
        request = {"replaceAllText": {"containsText": {"text": "{{CONTENT}}", "matchCase": True}, "replaceText": content}}
        requests = [request]
    else:
        tables = [item for item in body if "table" in item]
        requests = [
            {"deleteContentRange": {"range": {"startIndex": item["startIndex"], "endIndex": item["endIndex"]}}}
            for item in reversed(tables)
        ]
        insert_index = tables[0]["startIndex"] if tables else (body[-1].get("endIndex", 1) - 1 if body else 1)
        requests.append({"insertText": {"location": {"index": insert_index}, "text": content}})
    docs.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()


def name_for(worksheet_id: str, date: str) -> str:
    names = {
        "grade-1": "MTS-Math-1stGrade-WeeklyWorksheet",
        "grade-4": "MTS-Math-4thGrade-WeeklyWorksheet",
        "grade-5": "MTS-Math-5thGrade-WeeklyWorksheet",
        "grade-6": "MTS-Math-6thGrade-WeeklyWorksheet",
        "grades-9-10": "MTS-Math-9th_10thGrade-WeeklyWorksheet",
    }
    return f"{names[worksheet_id]}-{date}"


def main() -> None:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    date = "2026-08-24"
    results = []
    for spec_path in sorted(SPECS.glob("*.json")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        worksheet_id = spec_path.stem
        base_name = name_for(worksheet_id, date)
        worksheet = copy_document(drive, WORKSHEET_TEMPLATE, base_name)
        key = copy_document(drive, ANSWER_KEY_TEMPLATE, base_name + "_KEY")
        render_document(docs, worksheet["id"], projection(spec, False))
        render_document(docs, key["id"], projection(spec, True))
        results.append({
            "worksheet_id": worksheet_id,
            "worksheet": worksheet,
            "answer_key": key,
            "status": "rendered",
            "template_ids": {"worksheet": WORKSHEET_TEMPLATE, "answer_key": ANSWER_KEY_TEMPLATE},
        })
        print(worksheet_id)
        print(f"  worksheet=https://docs.google.com/document/d/{worksheet['id']}/edit")
        print(f"  answer_key=https://docs.google.com/document/d/{key['id']}/edit")
    OUTPUT.write_text(json.dumps({"status": "rendered_to_staging", "staging_folder": STAGING_FOLDER, "artifacts": results}, indent=2) + "\n", encoding="utf-8")
    print(f"RENDER_PASS {len(results)} pairs")


if __name__ == "__main__":
    main()