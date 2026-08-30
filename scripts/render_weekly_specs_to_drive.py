"""Render approved Math Specs into copied Google Docs staging artifacts."""
from __future__ import annotations

from pathlib import Path
import json
import argparse


SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = REPO / "runs" / "math" / "run-2026-08-24-grade-6-weekly"
STAGING_FOLDER = "1FUZ5hC4hpKEZwirG-p4bKpDlPiN8IBfL"
TEMPLATE_MANIFEST = REPO / "subjects" / "math" / "config" / "template-manifests" / "weekly-worksheet.json"
OAUTH_TOKEN = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets\oauth-token.json")


def display_answer(answer: object, *, decimal_places: int = 2, noise_threshold: int = 3) -> str:
    """Render an answer for display.

    Rounding only kicks in when it's actually relevant: if a float's raw value already has
    `noise_threshold` decimal digits or fewer, it's shown as-is (a clean, intentional value like
    `0.125` is never truncated). Only floats with MORE raw decimal digits than that (almost always
    floating-point noise from an irrational computation, e.g. `3.9999999999999996`) get rounded to
    `decimal_places` for display; the underlying stored `answer` used for verification is untouched.
    """
    if isinstance(answer, (list, tuple)):
        return ", ".join(display_answer(item, decimal_places=decimal_places, noise_threshold=noise_threshold) for item in answer)
    if isinstance(answer, float):
        raw = repr(answer)
        raw_decimal_digits = len(raw.split(".", 1)[1]) if "." in raw else 0
        if raw_decimal_digits <= noise_threshold:
            return raw
        rounded = round(answer, decimal_places)
        return f"{rounded:.{decimal_places}f}"
    return str(answer)


def grade_display_name(spec: dict) -> str:
    worksheet = spec["worksheet"]
    return str(worksheet.get("grade_display_name") or worksheet.get("grade") or worksheet["grade_or_course"])


def projection(spec: dict, answer_key: bool, *, decimal_places: int = 2) -> str:
    lines = [spec["worksheet"]["title"], grade_display_name(spec), f"Week of {spec['worksheet']['week_start']}", ""]
    for section in spec["sections"]:
        lines.extend([section.get("title", section["id"].title()), ""])
        for question in section["questions"]:
            value = display_answer(question["answer"], decimal_places=decimal_places) if answer_key else question["prompt"]
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


def paragraph_ranges_containing(body: list[dict], placeholders: set[str]) -> dict[str, tuple[int, int]]:
    ranges = {}
    for item in body:
        paragraph = item.get("paragraph")
        if not paragraph:
            continue
        text = "".join(element.get("textRun", {}).get("content", "") for element in paragraph.get("elements", []))
        for placeholder in placeholders:
            if placeholder in text:
                ranges[placeholder] = (item["startIndex"], item["endIndex"])
    return ranges


def render_document(docs, document_id: str, content: str, spec: dict, answer_key: bool, *, decimal_places: int = 2) -> None:
    existing, body = document_text(docs, document_id)
    if "{{MON_Q1}}" in existing or "{{MON_A1}}" in existing:
        prefixes = {"monday": "MON", "tuesday": "TUE", "wednesday": "WED", "thursday": "THU", "friday": "FRI"}
        values = {
            "{{GRADE_OR_COURSE}}": f"{spec['worksheet']['title']}\n{grade_display_name(spec)}",
            "{{WEEK_OF}}": spec["worksheet"]["week_start"],
            "{{SCHOOL_LEVEL}}": "Middle School",
        }
        for section in spec["sections"]:
            prefix = prefixes[section["id"]]
            questions = {number: question for number, question in enumerate(section["questions"], start=1)}
            for number in range(1, 11):
                question = questions.get(number)
                placeholder = f"{{{{{prefix}_{'A' if answer_key else 'Q'}{number}}}}}"
                if question:
                    value = display_answer(question["answer"], decimal_places=decimal_places) if answer_key else question["prompt"]
                    rendered_value = f"{question['number']}. {value}"
                    if answer_key:
                        values[f"{number}. Answer: {placeholder}"] = f"{question['number']}. Answer: {value}"
                    else:
                        values[f"{number}. {placeholder}"] = rendered_value
                    values[placeholder] = rendered_value
                else:
                    values[placeholder] = ""
        empty_placeholders = {placeholder for placeholder, value in values.items() if not value and placeholder in existing}
        ranges = paragraph_ranges_containing(body, empty_placeholders)
        requests = [
            {"deleteContentRange": {"range": {"startIndex": start, "endIndex": end}}}
            for start, end in sorted(ranges.values(), reverse=True)
        ]
        requests.extend(
            {"replaceAllText": {"containsText": {"text": placeholder, "matchCase": True}, "replaceText": value}}
            for placeholder, value in values.items()
            if value and placeholder in existing
        )
    elif "{{CONTENT}}" in existing:
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
        "grade_1": "MTS-Math-1stGrade-WeeklyWorksheet",
        "grade_4": "MTS-Math-4thGrade-WeeklyWorksheet",
        "grade_5": "MTS-Math-5thGrade-WeeklyWorksheet",
        "grade_6": "MTS-Math-6thGrade-WeeklyWorksheet",
        "grade_9_10": "MTS-Math-9th_10thGrade-WeeklyWorksheet",
    }
    return f"{names[worksheet_id]}-{date}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--worksheet-id", default=None)
    parser.add_argument("--date", default="2026-08-24")
    args = parser.parse_args()
    run_root = args.run_root if args.run_root.is_absolute() else REPO / args.run_root
    specs_root = run_root / "specs"
    output = run_root / "rendered-artifacts.json"
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    from sys import path as module_path
    module_path.insert(0, str(REPO / "src" / "runtime"))
    import policy

    resolved_policy = policy.resolve({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)
    manifest_path = REPO / resolved_policy["template_selection"]["template_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    worksheet_template = manifest["worksheet_template"]["id"]
    answer_key_template = manifest["answer_key_template"]["id"]
    date = args.date
    results = []
    if args.worksheet_id:
        flat_path = specs_root / f"{args.worksheet_id}.json"
        revision_paths = sorted((specs_root / args.worksheet_id).glob("*.json"))
        spec_paths = [flat_path] if flat_path.is_file() else revision_paths[-1:]
    else:
        spec_paths = sorted(specs_root.glob("*.json"))
    if args.worksheet_id == "grades-9-10":
        grade_defaults = resolved_policy["grade_defaults"]["grade_9_10"]
        expected_count = grade_defaults["questions_per_day"] * len(resolved_policy["sections"])
        spec = json.loads(spec_paths[-1].read_text(encoding="utf-8")) if spec_paths else {}
        if spec.get("worksheet", {}).get("question_count") != expected_count:
            raise ValueError("Combined Grades 9/10 Weekly render requires 5 questions per day and 25 questions per week.")
    for spec_path in spec_paths:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        worksheet_id = args.worksheet_id or spec_path.stem
        base_name = name_for(worksheet_id, date)
        worksheet = copy_document(drive, worksheet_template, base_name)
        key = copy_document(drive, answer_key_template, base_name + "_KEY")
        render_document(docs, worksheet["id"], projection(spec, False), spec, False)
        render_document(docs, key["id"], projection(spec, True), spec, True)
        results.append({
            "worksheet_id": worksheet_id,
            "worksheet": worksheet,
            "answer_key": key,
            "status": "rendered",
            "template_ids": {"worksheet": worksheet_template, "answer_key": answer_key_template},
        })
        print(worksheet_id)
        print(f"  worksheet=https://docs.google.com/document/d/{worksheet['id']}/edit")
        print(f"  answer_key=https://docs.google.com/document/d/{key['id']}/edit")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"status": "rendered_to_staging", "staging_folder": STAGING_FOLDER, "artifacts": results}, indent=2) + "\n", encoding="utf-8")
    print(f"RENDER_PASS {len(results)} pairs")


if __name__ == "__main__":
    main()