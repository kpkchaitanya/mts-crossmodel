import re
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO = Path(__file__).resolve().parents[3]
sys.path.extend([str(REPO / "src" / "runtime"), str(REPO / "subjects" / "math" / "src")])

from validate_staged_documents import DOCUMENTS, SCOPES, TOKEN_PATH, text_and_blocks


def main():
    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    docs = build("docs", "v1", credentials=credentials)
    drive = build("drive", "v3", credentials=credentials)
    response = drive.files().list(
        q="name = 'MTS-Math-1stGrade-WeeklyWorksheet-2026-08-31_KEY'",
        orderBy="createdTime desc",
        pageSize=1,
        fields="files(id,name,createdTime)",
    ).execute()
    document = response["files"][0]
    text, blocks = text_and_blocks(docs, document["id"])
    print(f"document={document}")
    missing = [number for number in range(1, 51) if not re.search(rf"(?m)^\s*{number}\.\s*", text)]
    print(f"content_blocks={blocks}")
    print(f"missing_numbers={missing}")
    print(repr(text[:2500]))


if __name__ == "__main__":
    main()