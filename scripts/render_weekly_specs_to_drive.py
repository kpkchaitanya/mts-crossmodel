"""Render approved Math Specs into copied Google Docs staging artifacts."""
from __future__ import annotations

from pathlib import Path
import json
import argparse


SCOPES = ["https://www.googleapis.com/auth/drive"]
REPO = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = REPO / "data" / "transactions" / "runs" / "run-2026-09-07-weekly-bypass-sample"
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


def display_question_prompt(question: dict) -> str:
    """Return a student prompt without its canonical Question N storage prefix."""
    number = question["number"]
    return str(question["prompt"]).removeprefix(f"Question {number}: ")


def answer_key_line(question: dict, *, decimal_places: int = 2, number: int | None = None) -> str:
    """Return one concise numbered answer-key entry."""
    shown = question["number"] if number is None else number
    return f"{shown}. {display_answer(question['answer'], decimal_places=decimal_places)}"


def display_number(question: dict, local_number: int, numbering: str) -> int:
    """Students see local per-day numbers; the Spec keeps global numbers for verification."""
    return local_number if numbering == "local" else question["number"]


def projection(spec: dict, answer_key: bool, *, decimal_places: int = 2, numbering: str = "local") -> str:
    lines = [spec["worksheet"]["title"], grade_display_name(spec), f"Week of {spec['worksheet']['week_start']}", ""]
    for section in spec["sections"]:
        lines.extend([section.get("title", section["id"].title()), ""])
        for local_number, question in enumerate(section["questions"], start=1):
            shown = display_number(question, local_number, numbering)
            value = (
                answer_key_line(question, decimal_places=decimal_places, number=shown)
                if answer_key
                else f"{shown}. {display_question_prompt(question)}"
            )
            lines.append(value)
        lines.append("")
    if answer_key:
        lines.insert(0, "ANSWER KEY")
    return "\n".join(lines).strip() + "\n"


def copy_document(drive, template_id: str, staging_folder: str, name: str) -> dict:
    return drive.files().copy(
        fileId=template_id,
        body={"name": name, "parents": [staging_folder]},
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


def render_document(docs, document_id: str, content: str, spec: dict, answer_key: bool, *, decimal_places: int = 2, numbering: str = "local") -> None:
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
                    shown = display_number(question, number, numbering)
                    value = display_answer(question["answer"], decimal_places=decimal_places) if answer_key else display_question_prompt(question)
                    rendered_value = f"{shown}. {value}"
                    if answer_key:
                        values[f"{number}. Answer: {placeholder}"] = answer_key_line(question, decimal_places=decimal_places, number=shown)
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


def name_for(naming: dict, worksheet_id: str, date: str) -> str:
    prefix = naming["prefix_by_grade"][worksheet_id]
    return naming["document_name_pattern"].replace("{{PREFIX}}", prefix).replace("{{WEEK_OF}}", date)


def spec_paths_for_run(run_root: Path, worksheet_id: str | None = None) -> list[tuple[str, Path]]:
    """Return worksheet IDs and Spec paths, preferring target entity references."""
    references_path = run_root / "entity_references.json"
    if references_path.is_file():
        references = json.loads(references_path.read_text(encoding="utf-8")).get("references", [])
        selected = []
        normalized = worksheet_id.replace("-", "_") if worksheet_id else None
        for reference in references:
            grade = str(reference["grade_or_course"])
            if normalized and grade != normalized:
                continue
            selected.append((grade, REPO / reference["spec"]))
        return selected

    specs_root = run_root / "specs"
    if worksheet_id:
        flat_path = specs_root / f"{worksheet_id}.json"
        revision_paths = sorted((specs_root / worksheet_id).glob("*.json"))
        paths = [flat_path] if flat_path.is_file() else revision_paths[-1:]
    else:
        paths = sorted(specs_root.glob("*.json"))
    return [(worksheet_id or path.stem, path) for path in paths]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--worksheet-id", default=None)
    parser.add_argument("--date", default="2026-08-24")
    args = parser.parse_args()
    run_root = args.run_root if args.run_root.is_absolute() else REPO / args.run_root
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
    module_path.insert(0, str(REPO / "src"))
    from mts.setup_project.configure import resolve_effective_config

    effective_config = resolve_effective_config({"subject": "math", "worksheet_type": "weekly-worksheet"}, repository_root=REPO)
    manifest_path = REPO / effective_config["template_selection"]["template_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    worksheet_template = manifest["worksheet_template"]["id"]
    answer_key_template = manifest["answer_key_template"]["id"]
    staging_folder = effective_config["publishing"]["staging"]["render_folder_id"]
    naming = effective_config["naming"]["weekly"]
    numbering = effective_config.get("display_numbering", "local")
    date = args.date
    results = []
    spec_paths = spec_paths_for_run(run_root, args.worksheet_id)
    if args.worksheet_id in {"grades-9-10", "grade_9_10"}:
        grade_defaults = effective_config["grade_defaults"]["grade_9_10"]
        expected_count = grade_defaults["questions_per_day"] * len(effective_config["sections"])
        spec = json.loads(spec_paths[-1][1].read_text(encoding="utf-8")) if spec_paths else {}
        if spec.get("worksheet", {}).get("question_count") != expected_count:
            raise ValueError("Combined Grades 9/10 Weekly render requires 5 questions per day and 25 questions per week.")
    for worksheet_id, spec_path in spec_paths:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        base_name = name_for(naming, worksheet_id, date)
        worksheet = copy_document(drive, worksheet_template, staging_folder, base_name)
        key = copy_document(drive, answer_key_template, staging_folder, base_name + naming["answer_key_suffix"])
        render_document(docs, worksheet["id"], projection(spec, False, numbering=numbering), spec, False, numbering=numbering)
        render_document(docs, key["id"], projection(spec, True, numbering=numbering), spec, True, numbering=numbering)
        if effective_config["publishing"].get("provenance", {}).get("enabled"):
            from mts.publishing import deliver as delivery_policy
            from mts.infrastructure.google_docs import google_docs_adapter

            stamper = google_docs_adapter.GoogleDocsAdapter(drive, docs)
            for document, artifact_kind in ((worksheet, "student_worksheet"), (key, "answer_key")):
                stamper.stamp_document(
                    document["id"],
                    delivery_policy.provenance_properties(
                        run_id=run_root.name,
                        spec_revision=spec_path.stem,
                        grade_id=worksheet_id,
                        week_of=date,
                        worksheet_type="weekly-worksheet",
                        artifact_kind=artifact_kind,
                    ),
                )
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
    output.write_text(json.dumps({"status": "rendered_to_staging", "staging_folder": staging_folder, "artifacts": results}, indent=2) + "\n", encoding="utf-8")
    print(f"RENDER_PASS {len(results)} pairs")


if __name__ == "__main__":
    main()