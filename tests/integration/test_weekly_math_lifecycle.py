"""Staging-only integration test for all Math Weekly Worksheet plans."""
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs import google_docs_adapter
from mts.setup_project.configure import resolve_effective_config
from mts.subjects.math import subject_module, weekly_workflow
from mts.workflow_management import gates
from mts.workflow_management.run_loader import RunLoader
from mts.workflow_management.run_writer import RunWriter


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeFiles:
    def __init__(self):
        self.documents = {}
        self.copy_calls = []
        self.update_calls = []

    def copy(self, *, fileId, body, fields):
        document_id = f"copy-{len(self.copy_calls) + 1}"
        document = {"id": document_id, "name": body["name"], "parents": body["parents"], "webViewLink": f"https://docs/{document_id}"}
        self.documents[document_id] = document
        self.copy_calls.append({"template_id": fileId, **document})
        return Request(document)

    def get(self, *, fileId, fields):
        return Request(dict(self.documents[fileId]))

    def update(self, **kwargs):
        self.update_calls.append(kwargs)
        raise AssertionError("Staging-only Weekly lifecycle must not publish documents.")


class FakeDrive:
    def __init__(self):
        self.file_service = FakeFiles()

    def files(self):
        return self.file_service


class FakeDocuments:
    def __init__(self):
        self.content = {}

    def get(self, *, documentId):
        text = self.content.get(documentId, "{{CONTENT}}")
        body = [{"endIndex": len(text) + 1, "paragraph": {"elements": [{"textRun": {"content": text}}]}}]
        return Request({"body": {"content": body}})

    def batchUpdate(self, *, documentId, body):
        request = body["requests"][0]
        self.content[documentId] = request["replaceAllText"]["replaceText"]
        return Request({})


class FakeDocs:
    def __init__(self):
        self.document_service = FakeDocuments()

    def documents(self):
        return self.document_service


def candidate_spec(grade_or_course, question_count):
    section_ids = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    questions_per_section = question_count // len(section_ids)
    if questions_per_section * len(section_ids) != question_count:
        raise AssertionError("Weekly fixture count must divide evenly across five sections.")
    sections = []
    for section_index, section_id in enumerate(section_ids):
        start = section_index * questions_per_section + 1
        questions = []
        for number in range(start, start + questions_per_section):
            questions.append(
                {
                    "number": number,
                    "prompt": f"Fixture question {number}: find {number} + 1.",
                    "answer": number + 1,
                    "skill": "fixture_arithmetic",
                    "difficulty": "easy",
                    "verification": {"method": "arithmetic_expression", "inputs": {"expression": f"{number}+1"}},
                }
            )
        sections.append({"id": section_id, "questions": questions})
    return {
        "worksheet": {
            "grade": grade_or_course,
            "title": "MTS - WEEKLY WORKSHEET",
            "question_count": question_count,
        },
        "sections": sections,
        "verification": {"status": "PENDING"},
    }


def projection(spec, *, answer_key=False):
    lines = [spec["worksheet"]["title"], spec["worksheet"]["grade"]]
    if answer_key:
        lines.append("ANSWER KEY")
    for section in spec["sections"]:
        for question in section["questions"]:
            lines.append(f"{question['number']}. {question['answer'] if answer_key else question['prompt']}")
    return "\n".join(lines)


def approve(writer, manifest, gate, revision):
    updated = gates.record_approval(manifest, gate=gate, artifact_revision=revision, status="approved", reviewer="teacher")
    writer.write_manifest(updated)
    return updated


def test_all_weekly_math_plans_reach_publish_approval_readiness():
    request = {"subject": "math", "worksheet_type": "weekly-worksheet"}
    effective_config = resolve_effective_config(request, repository_root=REPO)
    math = subject_module.MathSubjectModule()
    workflow = weekly_workflow.prepare_scope_review(effective_config, on_date="2026-08-24", subject_module=math)
    drive = FakeDrive()
    docs = FakeDocs()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)

    with tempfile.TemporaryDirectory() as temporary_directory:
        writer = RunWriter(Path(temporary_directory) / "data")
        loader = RunLoader(Path(temporary_directory) / "data")
        writer.write_effective_config("run-weekly-math-e2e", effective_config)
        manifest = {"run_id": "run-weekly-math-e2e", "subject": "math", "worksheet_type": "weekly-worksheet", "status": "initialized", "approvals": []}
        writer.write_manifest(manifest)
        manifest = approve(writer, manifest, "scope_review", "weekly-scope-r1")
        assert gates.require_approval(manifest, gate="scope_review", artifact_revision="weekly-scope-r1") == "worksheet_prepared"

        validated_artifacts = []
        for plan_entry in workflow["worksheet_plans"]:
            grade = plan_entry["grade_or_course"]
            count = plan_entry["plan"]["questions_per_week"]
            if grade == "grade_9_10":
                assert plan_entry["plan"]["questions_per_day"] == 5
                assert count == 25
                assert sum(plan_entry["plan"]["grade_split"].values()) == count
            spec = math.build_spec(plan_entry["plan"], {"spec": candidate_spec(grade, count)})
            assert [section["id"] for section in spec["sections"]] == ["monday", "tuesday", "wednesday", "thursday", "friday"]
            manifest = approve(writer, manifest, "question_review", f"{grade}-questions-r1")
            assert gates.require_approval(manifest, gate="question_review", artifact_revision=f"{grade}-questions-r1") == "verification_in_progress"

            verification = math.verify_spec(spec)
            assert verification["status"] == "PASS"
            assert verification["questions"] == count
            spec["verification"]["status"] = "PASS"
            manifest = approve(writer, manifest, "verification_review", f"{grade}-verification-r1")
            assert gates.require_approval(manifest, gate="verification_review", artifact_revision=f"{grade}-verification-r1") == "render_ready"

            rendered = adapter.render_pair(
                spec,
                {"student_template_id": "student-master", "answer_key_template_id": "key-master"},
                "staging-folder",
                {"student_worksheet": f"{grade} Weekly", "answer_key": f"{grade} Weekly_KEY"},
                {"student_worksheet": projection(spec), "answer_key": projection(spec, answer_key=True)},
            )
            student_id = rendered["student_worksheet"]["document"]["id"]
            key_id = rendered["answer_key"]["document"]["id"]
            qa = math.validate_subject_output(
                {"student_worksheet": docs.document_service.content[student_id], "answer_key": docs.document_service.content[key_id]},
                spec,
            )
            assert qa["student_worksheet"]["status"] == "PASS"
            assert qa["answer_key"]["status"] == "PASS"
            for artifact in rendered.values():
                artifact["status"] = "validated"
                validated_artifacts.append(artifact)
            manifest = approve(writer, manifest, "formatting_review", f"{grade}-render-r1")
            assert gates.require_approval(manifest, gate="formatting_review", artifact_revision=f"{grade}-render-r1") == "publish_approval_pending"

        manifest["artifacts"] = validated_artifacts
        manifest["status"] = "publish_approval_pending"
        writer.write_manifest(manifest)
        persisted = loader.load_manifest("run-weekly-math-e2e")
        assert len(persisted["artifacts"]) == 10
        assert len(drive.file_service.copy_calls) == 10
        assert drive.file_service.update_calls == []


def main():
    test_all_weekly_math_plans_reach_publish_approval_readiness()
    print("PASS test_all_weekly_math_plans_reach_publish_approval_readiness")
    print("ALL_PASS 1/1")


if __name__ == "__main__":
    main()
