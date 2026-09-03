"""Staging-only end-to-end integration test for Math Class Worksheet lifecycle."""
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs import google_docs_adapter
from mts.setup_project.configure import resolve_effective_config
from mts.subjects.math import subject_module
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
        raise AssertionError("Staging-only lifecycle must not call publication.")


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


def candidate_spec():
    return {
        "worksheet": {"grade": "Grade 6", "title": "MTS - CLASS WORKSHEET", "question_count": 1},
        "sections": [{"id": "A", "questions": [
            {"number": 1, "prompt": "Find 3 + 4.", "answer": 7, "skill": "arithmetic", "difficulty": "easy",
             "verification": {"method": "arithmetic_expression", "inputs": {"expression": "3+4"}}}
        ]}],
        "verification": {"status": "PENDING"},
    }


def approve(writer, manifest, gate, revision):
    updated = gates.record_approval(manifest, gate=gate, artifact_revision=revision, status="approved", reviewer="teacher")
    writer.write_manifest(updated)
    return updated


def test_math_class_lifecycle_stops_at_publish_readiness():
    request = {"subject": "math", "worksheet_type": "class-worksheet"}
    effective_config = resolve_effective_config(request, repository_root=REPO)
    math = subject_module.MathSubjectModule()
    drive = FakeDrive()
    docs = FakeDocs()
    adapter = google_docs_adapter.GoogleDocsAdapter(drive, docs)

    with tempfile.TemporaryDirectory() as temporary_directory:
        writer = RunWriter(Path(temporary_directory) / "data")
        loader = RunLoader(Path(temporary_directory) / "data")
        writer.write_effective_config("run-math-class-e2e", effective_config)
        manifest = {"run_id": "run-math-class-e2e", "subject": "math", "worksheet_type": "class-worksheet", "status": "initialized", "approvals": []}
        writer.write_manifest(manifest)
        scope = math.resolve_curriculum({"grade_or_course": "grade_6", "on_date": "2026-08-24"})
        manifest = approve(writer, manifest, "scope_review", "scope-grade-6-r1")
        assert gates.require_approval(manifest, gate="scope_review", artifact_revision="scope-grade-6-r1") == "worksheet_prepared"

        plan = math.prepare_blueprint(scope, effective_config, effective_config)
        spec = math.build_spec(plan, {"spec": candidate_spec()})
        manifest = approve(writer, manifest, "question_review", "spec-grade-6-r1")
        assert gates.require_approval(manifest, gate="question_review", artifact_revision="spec-grade-6-r1") == "verification_in_progress"

        verification = math.verify_spec(spec)
        assert verification["status"] == "PASS"
        spec["verification"]["status"] = "PASS"
        manifest = approve(writer, manifest, "verification_review", "verification-grade-6-r1")
        assert gates.require_approval(manifest, gate="verification_review", artifact_revision="verification-grade-6-r1") == "render_ready"

        rendered = adapter.render_pair(
            spec,
            {"student_template_id": "student-master", "answer_key_template_id": "key-master"},
            "staging-folder",
            {"student_worksheet": "Grade 6", "answer_key": "Grade 6_KEY"},
            {"student_worksheet": "MTS - CLASS WORKSHEET\nGrade 6\n1. Find 3 + 4.", "answer_key": "MTS - CLASS WORKSHEET\nGrade 6\nANSWER KEY\n1. 7"},
        )
        qa = math.validate_subject_output(
            {"student_worksheet": docs.document_service.content["copy-1"], "answer_key": docs.document_service.content["copy-2"]},
            spec,
        )
        assert qa["student_worksheet"]["status"] == "PASS"
        assert qa["answer_key"]["status"] == "PASS"
        for artifact in rendered.values():
            artifact["status"] = "validated"
        manifest["artifacts"] = list(rendered.values())
        manifest = approve(writer, manifest, "formatting_review", "render-grade-6-r1")
        assert gates.require_approval(manifest, gate="formatting_review", artifact_revision="render-grade-6-r1") == "publish_approval_pending"

        manifest["status"] = "publish_approval_pending"
        writer.write_manifest(manifest)
        persisted = loader.load_manifest("run-math-class-e2e")
        assert persisted["status"] == "publish_approval_pending"
        assert len(persisted["approvals"]) == 4
        assert len(drive.file_service.copy_calls) == 2
        assert drive.file_service.update_calls == []


def main():
    test_math_class_lifecycle_stops_at_publish_readiness()
    print("PASS test_math_class_lifecycle_stops_at_publish_readiness")
    print("ALL_PASS 1/1")


if __name__ == "__main__":
    main()
