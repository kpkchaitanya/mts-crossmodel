"""Mocked integration tests for the Google Docs/Drive adapter."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "rendering"))
import google_docs_adapter as adapter_module


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeFiles:
    def __init__(self):
        self.documents = {}
        self.copies = []
        self.updates = []
        self.folders = {}
        self.list_queries = []

    def copy(self, *, fileId, body, fields):
        document_id = f"copy-{len(self.copies) + 1}"
        document = {"id": document_id, "name": body["name"], "parents": body["parents"], "webViewLink": f"https://docs/{document_id}"}
        self.documents[document_id] = document
        self.copies.append({"template_id": fileId, **document})
        return Request(document)

    def get(self, *, fileId, fields):
        return Request(dict(self.documents[fileId]))

    def list(self, *, q, fields, pageSize):
        self.list_queries.append(q)
        matches = [
            folder for folder in self.folders.values()
            if f"name = '{folder['name']}'" in q and f"'{folder['parents'][0]}' in parents" in q
        ]
        return Request({"files": [{"id": f["id"], "name": f["name"], "webViewLink": f["webViewLink"]} for f in matches]})

    def create(self, *, body, fields):
        folder_id = f"folder-{len(self.folders) + 1}"
        folder = {"id": folder_id, "name": body["name"], "parents": body["parents"], "webViewLink": f"https://drive/{folder_id}"}
        self.folders[folder_id] = folder
        return Request(dict(folder))

    def update(self, *, fileId, addParents, removeParents, fields):
        document = self.documents[fileId]
        document["parents"] = [addParents]
        self.updates.append({"file_id": fileId, "add_parents": addParents, "remove_parents": removeParents})
        return Request(dict(document))


class FakeDrive:
    def __init__(self):
        self.file_service = FakeFiles()

    def files(self):
        return self.file_service


class FakeDocuments:
    def __init__(self):
        self.content = {}
        self.batch_requests = []

    def get(self, *, documentId):
        text = self.content.get(documentId, "{{CONTENT}}")
        body = [{"endIndex": len(text) + 1, "paragraph": {"elements": [{"textRun": {"content": text}}]}}]
        return Request({"body": {"content": body}})

    def batchUpdate(self, *, documentId, body):
        self.batch_requests.append({"document_id": documentId, "requests": body["requests"]})
        request = body["requests"][0]
        if "replaceAllText" in request:
            self.content[documentId] = request["replaceAllText"]["replaceText"]
        else:
            self.content[documentId] = self.content.get(documentId, "") + request["insertText"]["text"]
        return Request({})


class FakeDocs:
    def __init__(self):
        self.document_service = FakeDocuments()

    def documents(self):
        return self.document_service


def verified_spec():
    return {"verification": {"status": "PASS"}}


def test_render_pair_copies_masters_and_replaces_placeholder():
    drive = FakeDrive()
    docs = FakeDocs()
    adapter = adapter_module.GoogleDocsAdapter(drive, docs)
    rendered = adapter.render_pair(
        verified_spec(),
        {"student_template_id": "student-master", "answer_key_template_id": "key-master"},
        "staging-folder",
        {"student_worksheet": "Grade 6", "answer_key": "Grade 6_KEY"},
        {"student_worksheet": "1. Solve.", "answer_key": "ANSWER KEY\n1. 7"},
    )
    assert [copy["template_id"] for copy in drive.file_service.copies] == ["student-master", "key-master"]
    assert all(copy["parents"] == ["staging-folder"] for copy in drive.file_service.copies)
    assert docs.document_service.content[rendered["student_worksheet"]["document"]["id"]] == "1. Solve."
    assert docs.document_service.content[rendered["answer_key"]["document"]["id"]] == "ANSWER KEY\n1. 7"


def test_publish_pair_moves_both_validated_artifacts_to_final_destination():
    drive = FakeDrive()
    docs = FakeDocs()
    adapter = adapter_module.GoogleDocsAdapter(drive, docs)
    rendered = adapter.render_pair(
        verified_spec(),
        {"student_template_id": "student-master", "answer_key_template_id": "key-master"},
        "staging-folder",
        {"student_worksheet": "Grade 6", "answer_key": "Grade 6_KEY"},
        {"student_worksheet": "1. Solve.", "answer_key": "ANSWER KEY\n1. 7"},
    )
    for artifact in rendered.values():
        artifact["status"] = "validated"
    publication = adapter.publish_pair(rendered["student_worksheet"], rendered["answer_key"], "final-folder")
    assert publication["status"] == "published"
    assert len(drive.file_service.updates) == 2
    assert all(update["add_parents"] == "final-folder" for update in drive.file_service.updates)


def test_unverified_spec_and_incomplete_pair_fail_closed():
    adapter = adapter_module.GoogleDocsAdapter(FakeDrive(), FakeDocs())
    try:
        adapter.render_pair(
            {"verification": {"status": "PENDING"}},
            {"student_template_id": "student-master", "answer_key_template_id": "key-master"},
            "staging-folder",
            {"student_worksheet": "Grade 6", "answer_key": "Grade 6_KEY"},
            {"student_worksheet": "1. Solve.", "answer_key": "ANSWER KEY\n1. 7"},
        )
    except adapter_module.GoogleDocsAdapterError as error:
        assert "passing" in str(error)
    else:
        raise AssertionError("Unverified Spec must not render.")


def staged_pair(adapter):
    rendered = adapter.render_pair(
        verified_spec(),
        {"student_template_id": "student-master", "answer_key_template_id": "key-master"},
        "staging-folder",
        {"student_worksheet": "Grade 6", "answer_key": "Grade 6_KEY"},
        {"student_worksheet": "1. Solve.", "answer_key": "ANSWER KEY\n1. 7"},
    )
    return rendered["student_worksheet"], rendered["answer_key"]


def test_ensure_child_folder_is_idempotent():
    drive = FakeDrive()
    adapter = adapter_module.GoogleDocsAdapter(drive, FakeDocs())
    created = adapter.ensure_child_folder("grade-6-parent", "Week_2026-08-31")
    reused = adapter.ensure_child_folder("grade-6-parent", "Week_2026-08-31")
    assert created["created"] is True
    assert reused["created"] is False
    assert reused["id"] == created["id"]
    assert len(drive.file_service.folders) == 1


def test_deliver_pair_copies_staged_documents_and_preserves_staging():
    drive = FakeDrive()
    adapter = adapter_module.GoogleDocsAdapter(drive, FakeDocs())
    student, answer_key = staged_pair(adapter)
    week_folder = adapter.ensure_child_folder("grade-6-parent", "Week_2026-08-31")

    delivered = adapter.deliver_pair(student, answer_key, week_folder["id"], mode="copy")

    assert delivered["status"] == "delivered"
    assert delivered["student_worksheet"]["document"]["parents"] == [week_folder["id"]]
    assert delivered["answer_key"]["document"]["parents"] == [week_folder["id"]]
    assert drive.file_service.documents[student["document"]["id"]]["parents"] == ["staging-folder"]
    assert drive.file_service.updates == []


def test_deliver_pair_can_skip_the_answer_key():
    adapter = adapter_module.GoogleDocsAdapter(FakeDrive(), FakeDocs())
    student, answer_key = staged_pair(adapter)
    delivered = adapter.deliver_pair(student, answer_key, "week-folder", deliver_answer_key=False)
    assert "answer_key" not in delivered


def test_deliver_pair_rejects_unstaged_artifact_and_bad_mode():
    adapter = adapter_module.GoogleDocsAdapter(FakeDrive(), FakeDocs())
    student, answer_key = staged_pair(adapter)
    try:
        adapter.deliver_pair({**student, "status": "pending"}, answer_key, "week-folder")
    except adapter_module.GoogleDocsAdapterError as error:
        assert "staged" in str(error)
    else:
        raise AssertionError("Unstaged artifact must not be delivered.")
    try:
        adapter.deliver_pair(student, answer_key, "week-folder", mode="link")
    except adapter_module.GoogleDocsAdapterError as error:
        assert "mode" in str(error)
    else:
        raise AssertionError("Unknown delivery mode must fail closed.")

    try:
        adapter.publish_pair({"artifact_kind": "student_worksheet", "status": "staged"}, {}, "final-folder")
    except adapter_module.GoogleDocsAdapterError as error:
        assert "Validated" in str(error)
    else:
        raise AssertionError("Incomplete artifact pair must not publish.")


def main():
    tests = [
        test_render_pair_copies_masters_and_replaces_placeholder,
        test_publish_pair_moves_both_validated_artifacts_to_final_destination,
        test_unverified_spec_and_incomplete_pair_fail_closed,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
