import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO = Path(__file__).resolve().parents[3]
sys.path.extend([str(REPO / "src" / "runtime"), str(REPO / "subjects" / "math" / "src")])

import run_repository
import subject_module

RUN_ID = "run-b3b0b8fa936a4191914c694243ce1baa"
TOKEN_PATH = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")


def document_text(docs, document_id):
    body = docs.documents().get(documentId=document_id).execute().get("body", {}).get("content", [])
    text = "".join(
        element.get("textRun", {}).get("content", "")
        for item in body
        for element in item.get("paragraph", {}).get("elements", [])
    )
    return text, len(body)


def main():
    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), ["https://www.googleapis.com/auth/drive"])
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    docs = build("docs", "v1", credentials=credentials)
    run_root = REPO / "runs" / "math" / RUN_ID
    rendered = json.loads((run_root / "rendered-artifacts.json").read_text(encoding="utf-8"))["artifacts"][0]
    manifest = json.loads((run_root / "run-manifest.json").read_text(encoding="utf-8"))
    spec = json.loads((REPO / "runs" / manifest["spec_references"][0]["spec_path"]).read_text(encoding="utf-8"))
    student_text, student_blocks = document_text(docs, rendered["worksheet"]["id"])
    key_text, key_blocks = document_text(docs, rendered["answer_key"]["id"])
    qa = subject_module.MathSubjectModule(REPO / "subjects" / "math").validate_subject_output(
        {"student_worksheet": student_text, "answer_key": key_text}, spec
    )
    if qa["student_worksheet"]["status"] != "PASS" or qa["answer_key"]["status"] != "PASS":
        raise RuntimeError(qa)
    if "{{" in student_text or "{{" in key_text:
        raise RuntimeError("Unresolved template placeholder.")
    manifest["artifacts"] = [
        {"artifact_kind": "student_worksheet", "status": "validated", "worksheet_id": "grade_5", "document": rendered["worksheet"]},
        {"artifact_kind": "answer_key", "status": "validated", "worksheet_id": "grade_5", "document": rendered["answer_key"]},
    ]
    manifest["formatting_qa"] = {"revision": "form-diversity-r4", "status": "PASS", "student_content_blocks": student_blocks, "answer_key_content_blocks": key_blocks, "text_qa": qa}
    manifest["status"] = "validation_complete"
    run_repository.RunRepository(REPO / "runs").save_manifest(manifest)
    print(json.dumps(manifest["formatting_qa"], indent=2))


if __name__ == "__main__":
    main()