import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO = Path(__file__).resolve().parents[3]
sys.path.extend([str(REPO / "src" / "runtime"), str(REPO / "src" / "rendering")])

import gates
import google_docs_adapter
import policy
import run_repository

RUN_ID = "run-b3b0b8fa936a4191914c694243ce1baa"
TOKEN_PATH = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")
NOTES = "Explicit current-user instruction: All Gates Bypassed."


def main():
    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), ["https://www.googleapis.com/auth/drive"])
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    drive = build("drive", "v3", credentials=credentials)
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, build("docs", "v1", credentials=credentials))
    repository = run_repository.RunRepository(REPO / "runs")
    run_root = REPO / "runs" / "math" / RUN_ID
    manifest = json.loads((run_root / "run-manifest.json").read_text(encoding="utf-8"))
    manifest = gates.record_approval(manifest, gate="formatting_review", artifact_revision="grade_5-form-diversity-r3", status="approved", reviewer="auto-bypass", notes=NOTES)
    manifest["status"] = "publish_approval_pending"
    manifest = gates.record_approval(manifest, gate="publish_approval", artifact_revision="grade_5-form-diversity-r3", status="approved", reviewer="auto-bypass", notes=NOTES)
    resolved = policy.resolve({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)
    student = next(item for item in manifest["artifacts"] if item["artifact_kind"] == "student_worksheet")
    answer_key = next(item for item in manifest["artifacts"] if item["artifact_kind"] == "answer_key")
    published = adapter.publish_pair(student, answer_key, resolved["publishing"]["staging"]["approved_folder_id"])
    published_student = {"artifact_kind": "student_worksheet", "status": "published", "worksheet_id": "grade_5", "document": published["student_worksheet"]}
    published_key = {"artifact_kind": "answer_key", "status": "published", "worksheet_id": "grade_5", "document": published["answer_key"]}
    delivery_config = resolved["publishing"]["final_delivery"]
    grade_destination = resolved["publishing"]["final_delivery"]["destinations_by_grade"]["grade_5"]
    folder_name = delivery_config["week_folder_pattern"].replace("{{WEEK_OF}}", "2026-08-24")
    destination = adapter.ensure_child_folder(grade_destination["folder_id"], folder_name)
    delivery = adapter.deliver_pair(published_student, published_key, destination["id"], mode=delivery_config["mode"], deliver_answer_key=delivery_config["deliver_answer_key"])
    manifest["artifacts"] = [published_student, published_key]
    manifest["publication"] = {"status": "published", "destination_folder_id": resolved["publishing"]["staging"]["approved_folder_id"], "pair": published}
    manifest["delivery"] = {"status": "delivered", "week_folder": destination, "record": delivery}
    manifest["status"] = "published"
    repository.save_manifest(manifest)
    (run_root / "published-artifacts.json").write_text(json.dumps({"publication": manifest["publication"], "delivery": manifest["delivery"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": RUN_ID, "status": manifest["status"], "publication": manifest["publication"], "delivery": manifest["delivery"]}, indent=2))


if __name__ == "__main__":
    main()