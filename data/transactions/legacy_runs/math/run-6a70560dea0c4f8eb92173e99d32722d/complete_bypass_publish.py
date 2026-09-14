import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO = Path(__file__).resolve().parents[3]
sys.path.extend([
    str(REPO / "src" / "runtime"),
    str(REPO / "src" / "rendering"),
    str(REPO / "subjects" / "math" / "src"),
    str(REPO / "scripts"),
])

import gates
import google_docs_adapter
import render_weekly_specs_to_drive as renderer
import run_repository
import subject_module

RUN_ID = "run-6a70560dea0c4f8eb92173e99d32722d"
RUNS = REPO / "runs"
TOKEN_PATH = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")
STAGING_FOLDER = "1FUZ5hC4hpKEZwirG-p4bKpDlPiN8IBfL"
FINAL_FOLDER = "1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS"
SCOPES = ["https://www.googleapis.com/auth/drive"]
GATE_IDS = ["scope_review", "question_review", "verification_review", "formatting_review", "publish_approval"]


def approval(manifest, gate, revision):
    return gates.record_approval(
        manifest,
        gate=gate,
        artifact_revision=revision,
        status="approved",
        reviewer="auto-bypass",
        notes="Explicit current-user instruction: go ahead with all the gates and publish.",
    )


def document_text(docs, document_id):
    body = docs.documents().get(documentId=document_id).execute().get("body", {}).get("content", [])
    return "".join(
        element.get("textRun", {}).get("content", "")
        for item in body
        for element in item.get("paragraph", {}).get("elements", [])
    ), len(body)


def main():
    repository = run_repository.RunRepository(RUNS)
    manifest_path = RUNS / "math" / RUN_ID / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["gates"] = {"mode": "bypass_all", "bypassed": GATE_IDS, "requested_by": "current_user"}
    manifest["publish"] = {"requested": "yes", "resolved": True}

    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    drive = build("drive", "v3", credentials=credentials)
    docs = build("docs", "v1", credentials=credentials)
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)
    math = subject_module.MathSubjectModule(REPO / "subjects" / "math")

    specs = {}
    for reference in manifest["spec_references"]:
        if reference["revision"] != "questions-r3":
            raise RuntimeError(f"Active revision must be questions-r3, found {reference['revision']}.")
        spec = json.loads((RUNS / reference["spec_path"]).read_text(encoding="utf-8"))
        result = math.verify_spec(spec)
        if result["status"] != "PASS":
            raise RuntimeError(f"Formal verification failed for {reference['worksheet_id']}: {result}")
        specs[reference["worksheet_id"]] = spec
        manifest = approval(manifest, "question_review", f"{reference['worksheet_id']}-questions-r3")
        manifest = approval(manifest, "verification_review", f"{reference['worksheet_id']}-verification-r3")

    manifest = approval(manifest, "scope_review", "scope-2026-08-31-r1")
    manifest["verification"] = {
        "revision": "verification-2026-08-31-r3",
        "results": {worksheet_id: math.verify_spec(spec) for worksheet_id, spec in specs.items()},
    }
    manifest["status"] = "render_ready"
    repository.save_manifest(manifest)

    template_manifest = json.loads((REPO / "subjects" / "math" / "config" / "template-manifests" / "weekly-worksheet.json").read_text(encoding="utf-8"))
    artifacts = []
    qa_results = {}
    for worksheet_id, spec in specs.items():
        base_name = renderer.name_for(worksheet_id, "2026-08-31")
        student = renderer.copy_document(drive, template_manifest["worksheet_template"]["id"], base_name)
        answer_key = renderer.copy_document(drive, template_manifest["answer_key_template"]["id"], base_name + "_KEY")
        renderer.render_document(docs, student["id"], renderer.projection(spec, False), spec, False)
        renderer.render_document(docs, answer_key["id"], renderer.projection(spec, True), spec, True)
        student_text, student_blocks = document_text(docs, student["id"])
        key_text, key_blocks = document_text(docs, answer_key["id"])
        qa = math.validate_subject_output({"student_worksheet": student_text, "answer_key": key_text}, spec)
        if qa["student_worksheet"]["status"] != "PASS" or qa["answer_key"]["status"] != "PASS":
            raise RuntimeError(f"Rendered QA failed for {worksheet_id}: {qa}")
        if "{{" in student_text or "{{" in key_text:
            raise RuntimeError(f"Unresolved placeholder found in {worksheet_id}.")
        qa_results[worksheet_id] = {"status": "PASS", "student_content_blocks": student_blocks, "answer_key_content_blocks": key_blocks, "text_qa": qa}
        artifacts.extend([
            {"artifact_kind": "student_worksheet", "status": "validated", "worksheet_id": worksheet_id, "document": student},
            {"artifact_kind": "answer_key", "status": "validated", "worksheet_id": worksheet_id, "document": answer_key},
        ])
        manifest = approval(manifest, "formatting_review", f"{worksheet_id}-render-r3")

    manifest["artifacts"] = artifacts
    manifest["formatting_qa"] = {"revision": "render-2026-08-31-r3", "results": qa_results}
    manifest["status"] = "publish_approval_pending"
    manifest = approval(manifest, "publish_approval", "batch-2026-08-31-r3")

    published_artifacts = []
    publication = {}
    for worksheet_id in specs:
        student_artifact = next(item for item in artifacts if item["worksheet_id"] == worksheet_id and item["artifact_kind"] == "student_worksheet")
        key_artifact = next(item for item in artifacts if item["worksheet_id"] == worksheet_id and item["artifact_kind"] == "answer_key")
        published = adapter.publish_pair(student_artifact, key_artifact, FINAL_FOLDER)
        publication[worksheet_id] = published
        published_artifacts.extend([
            {"artifact_kind": "student_worksheet", "status": "published", "worksheet_id": worksheet_id, "document": published["student_worksheet"]},
            {"artifact_kind": "answer_key", "status": "published", "worksheet_id": worksheet_id, "document": published["answer_key"]},
        ])

    manifest["artifacts"] = published_artifacts
    manifest["publication"] = {"status": "published", "destination_folder_id": FINAL_FOLDER, "pairs": publication}
    manifest["status"] = "published"
    repository.save_manifest(manifest)
    output_path = RUNS / "math" / RUN_ID / "published-artifacts.json"
    output_path.write_text(json.dumps(manifest["publication"], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": RUN_ID, "status": manifest["status"], "qa": qa_results, "publication": publication}, indent=2))


if __name__ == "__main__":
    main()