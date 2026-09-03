"""Run-local evidence: confirm Final Delivery week folders are reused, not duplicated."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src" / "rendering"))
import google_docs_adapter

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]
PARENTS = {
    "grade_1": "1na4xEkS4mYB97qwjNZRdQ6q3RG3xk3Q9",
    "grade_4": "1WgYy1NG2buVLXEEhxyrHzloWbkjljD1K",
    "grade_5": "130VEomHbyC2-oyANo49W73dfDSi1VU5p",
    "grade_6": "10tSM2SwAxzGkzuYT47vNCo16K9TtPZre",
    "grade_9_10": "1RSSV84MDP8vHq7UwVm9GYH-36ZvGh1Cc",
}

creds = Credentials.from_authorized_user_file(
    r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json", SCOPES
)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
drive = build("drive", "v3", credentials=creds)
adapter = google_docs_adapter.GoogleDocsAdapter(drive, None)

failures = []
for grade_id, parent_id in PARENTS.items():
    folder = adapter.ensure_child_folder(parent_id, "Week_2026-08-31")
    if folder["created"]:
        failures.append(f"{grade_id}: duplicate week folder created")
    contents = drive.files().list(
        q=f"'{folder['id']}' in parents and trashed = false", fields="files(name)"
    ).execute()["files"]
    names = sorted(item["name"] for item in contents)
    print(f"{grade_id} reused={not folder['created']} {names}")
    if len(names) != 2:
        failures.append(f"{grade_id}: expected 2 delivered documents, found {len(names)}")

if failures:
    raise SystemExit("DELIVERY_VERIFY_FAIL\n" + "\n".join(failures))
print("DELIVERY_VERIFY_PASS")
