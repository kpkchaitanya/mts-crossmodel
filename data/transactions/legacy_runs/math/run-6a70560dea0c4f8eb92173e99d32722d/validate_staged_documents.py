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

RUN_ID = "run-6a70560dea0c4f8eb92173e99d32722d"
TOKEN_PATH = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]
DOCUMENTS = {
    "grade_1": ("1eGmwIif0vbcO1BHwuEyqmZS-Ci94ds_rADCOOr6_dyk", "1CZow4aKjfsrOPw8DJwoYjoMHib7vWcR6gSrfsO3GoJw"),
    "grade_4": ("1wJ2-ZBxXRuoXtR-nJSC4-7Mb2tm5ZOWonoy7MMVFh6w", "1sGmtgNCtNkNjrSj5LR0CIF3-elSQubn_YQDm5hAgrz0"),
    "grade_5": ("1jBJe27J-ejJctNUpnBwbNyC07dWDxfaKEHLH757Z_pU", "1phrB00wBoQt4zatqI-BY6-wzBcdhUj8n0oixXuLH3ts"),
    "grade_6": ("1lAVtB0U2un0d76NKmg4hxWVel6OTr8co43uidtGvmcE", "10PYSoBEHklQDOVOX7ncfNseCX9WA6ZsfoOTouVlklGs"),
    "grade_9_10": ("1agTnM3ligzmRFXw5Xs98JRjHOSK7cJ74dTkOTz8EjDs", "1r8rP6CkTfY1c1lsX-HFOM8I2owDGBrtF_RUi6Bvs2g4"),
}


def text_and_blocks(docs, document_id):
    body = docs.documents().get(documentId=document_id).execute().get("body", {}).get("content", [])
    text = "".join(
        element.get("textRun", {}).get("content", "")
        for item in body
        for element in item.get("paragraph", {}).get("elements", [])
    )
    return text, len(body)


def main():
    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    docs = build("docs", "v1", credentials=credentials)
    run_root = REPO / "runs" / "math" / RUN_ID
    manifest = json.loads((run_root / "run-manifest.json").read_text(encoding="utf-8"))
    specs = {
        reference["worksheet_id"]: json.loads((REPO / "runs" / reference["spec_path"]).read_text(encoding="utf-8"))
        for reference in manifest["spec_references"]
    }
    math = subject_module.MathSubjectModule(REPO / "subjects" / "math")
    artifacts = []
    qa_results = {}
    for worksheet_id, (student_id, key_id) in DOCUMENTS.items():
        student_text, student_blocks = text_and_blocks(docs, student_id)
        key_text, key_blocks = text_and_blocks(docs, key_id)
        qa = math.validate_subject_output(
            {"student_worksheet": student_text, "answer_key": key_text}, specs[worksheet_id]
        )
        if qa["student_worksheet"]["status"] != "PASS" or qa["answer_key"]["status"] != "PASS":
            raise RuntimeError(f"Rendered text QA failed for {worksheet_id}: {qa}")
        if "{{" in student_text or "{{" in key_text:
            raise RuntimeError(f"Unresolved template placeholder found in {worksheet_id}.")
        qa_results[worksheet_id] = {
            "status": "PASS",
            "student_content_blocks": student_blocks,
            "answer_key_content_blocks": key_blocks,
            "text_qa": qa,
        }
        artifacts.extend([
            {"artifact_kind": "student_worksheet", "status": "validated", "worksheet_id": worksheet_id, "document": {"id": student_id, "webViewLink": f"https://docs.google.com/document/d/{student_id}/edit"}},
            {"artifact_kind": "answer_key", "status": "validated", "worksheet_id": worksheet_id, "document": {"id": key_id, "webViewLink": f"https://docs.google.com/document/d/{key_id}/edit"}},
        ])
    manifest["artifacts"] = artifacts
    manifest["formatting_qa"] = {"revision": "render-2026-08-31-r1", "results": qa_results}
    manifest["status"] = "validation_complete"
    run_repository.RunRepository(REPO / "runs").save_manifest(manifest)
    print(json.dumps({"run_id": RUN_ID, "status": manifest["status"], "qa": qa_results}, indent=2))


if __name__ == "__main__":
    main()