"""Mocked integration tests for the Google Docs/Drive adapter."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from mts.infrastructure.google_docs import google_docs_adapter as adapter_module


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeFiles:
    FOLDER_MIME = "application/vnd.google-apps.folder"

    def __init__(self):
        self.documents = {}
        self.copies = []
        self.updates = []
        self.folders = {}
        self.list_queries = []
        self.trashed = []
        self._sequence = 0

    def _next_created_time(self):
        self._sequence += 1
        return f"2026-01-{self._sequence:02d}T00:00:00.000Z"

    def add_file(self, file_id, name, parent_id, *, mime_type="application/vnd.google-apps.document"):
        self.documents[file_id] = {
            "id": file_id,
            "name": name,
            "parents": [parent_id],
            "mimeType": mime_type,
            "createdTime": self._next_created_time(),
            "webViewLink": f"https://docs/{file_id}",
        }
        return self.documents[file_id]

    def add_folder(self, folder_id, name, parent_id):
        self.folders[folder_id] = {
            "id": folder_id,
            "name": name,
            "parents": [parent_id],
            "mimeType": self.FOLDER_MIME,
            "createdTime": self._next_created_time(),
            "webViewLink": f"https://drive/{folder_id}",
        }
        return self.folders[folder_id]

    def copy(self, *, fileId, body, fields):
        document_id = f"copy-{len(self.copies) + 1}"
        document = {
            "id": document_id,
            "name": body["name"],
            "parents": body["parents"],
            "mimeType": "application/vnd.google-apps.document",
            "createdTime": self._next_created_time(),
            "webViewLink": f"https://docs/{document_id}",
        }
        self.documents[document_id] = document
        self.copies.append({"template_id": fileId, **document})
        return Request(document)

    def get(self, *, fileId, fields):
        return Request(dict(self.documents[fileId]))

    def list(self, *, q, fields, pageSize, orderBy=None, pageToken=None):
        self.list_queries.append(q)
        matches = [item for item in (*self.documents.values(), *self.folders.values()) if self._matches(item, q)]
        if orderBy == "createdTime desc":
            matches.sort(key=lambda item: item["createdTime"], reverse=True)
        return Request({"files": [self._project(item, fields) for item in matches]})

    def _matches(self, item, q):
        if f"'{item['parents'][0]}' in parents" not in q:
            return False
        if f"mimeType != '{self.FOLDER_MIME}'" in q and item["mimeType"] == self.FOLDER_MIME:
            return False
        if f"mimeType = '{self.FOLDER_MIME}'" in q and item["mimeType"] != self.FOLDER_MIME:
            return False
        if "name = '" in q and f"name = '{item['name']}'" not in q:
            return False
        return True

    @staticmethod
    def _project(item, fields):
        keys = ("id", "name", "mimeType", "createdTime", "webViewLink", "appProperties") if "createdTime" in fields else ("id", "name", "webViewLink")
        return {key: item[key] for key in keys if key in item}

    def create(self, *, body, fields):
        folder_id = f"folder-{len(self.folders) + 1}"
        return Request(dict(self.add_folder(folder_id, body["name"], body["parents"][0])))

    def update(self, *, fileId, fields, addParents=None, removeParents=None, body=None):
        document = self.documents[fileId]
        if body and "trashed" in body:
            document["trashed"] = body["trashed"]
            self.trashed.append(fileId)
            return Request(dict(document))
        if body and "appProperties" in body:
            document.setdefault("appProperties", {}).update(body["appProperties"])
            return Request(dict(document))
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


def test_list_child_files_excludes_folders_and_lists_only_direct_children():
    drive = FakeDrive()
    adapter = adapter_module.GoogleDocsAdapter(drive, FakeDocs())
    drive.file_service.add_file("doc-1", "Grade 6", "week-folder")
    drive.file_service.add_file("doc-2", "Grade 6_KEY", "week-folder")
    drive.file_service.add_folder("archive-1", "Archive", "week-folder")
    drive.file_service.add_file("doc-3", "Elsewhere", "other-folder")

    listed = adapter.list_child_files("week-folder")

    assert [item["id"] for item in listed] == ["doc-2", "doc-1"]
    assert all("createdTime" in item for item in listed)
    assert adapter.list_child_files("empty-folder") == []


def test_list_child_folders_returns_newest_first():
    drive = FakeDrive()
    adapter = adapter_module.GoogleDocsAdapter(drive, FakeDocs())
    drive.file_service.add_folder("week-1", "Week_2026-08-24", "grade-6-parent")
    drive.file_service.add_folder("week-2", "Week_2026-08-31", "grade-6-parent")
    drive.file_service.add_file("doc-1", "Loose", "grade-6-parent")

    listed = adapter.list_child_folders("grade-6-parent")

    assert [item["id"] for item in listed] == ["week-2", "week-1"]


def test_move_file_reparents_and_is_a_no_op_when_already_in_destination():
    drive = FakeDrive()
    adapter = adapter_module.GoogleDocsAdapter(drive, FakeDocs())
    drive.file_service.add_file("doc-1", "Grade 6", "week-folder")

    moved = adapter.move_file("doc-1", "archive-1")
    assert moved["parents"] == ["archive-1"]
    assert drive.file_service.updates[-1]["remove_parents"] == "week-folder"

    adapter.move_file("doc-1", "archive-1")
    assert len(drive.file_service.updates) == 1


def test_move_file_requires_both_ids():
    adapter = adapter_module.GoogleDocsAdapter(FakeDrive(), FakeDocs())
    try:
        adapter.move_file("doc-1", "")
    except adapter_module.GoogleDocsAdapterError as error:
        assert "required" in str(error)
    else:
        raise AssertionError("A missing destination must fail closed.")


def test_trash_file_marks_the_file_trashed_and_never_deletes():
    drive = FakeDrive()
    adapter = adapter_module.GoogleDocsAdapter(drive, FakeDocs())
    drive.file_service.add_file("doc-1", "Grade 6", "week-folder")

    trashed = adapter.trash_file("doc-1")

    assert trashed["trashed"] is True
    assert drive.file_service.trashed == ["doc-1"]
    assert not hasattr(drive.file_service, "deleted")


def test_stamp_document_records_provenance_and_listings_return_it():
    drive = FakeDrive()
    adapter = adapter_module.GoogleDocsAdapter(drive, FakeDocs())
    drive.file_service.add_file("doc-1", "Grade 4", "staging")

    adapter.stamp_document("doc-1", {"mts_run_id": "run-1", "mts_grade_id": "grade_4"})

    listed = adapter.list_child_files("staging")
    assert listed[0]["appProperties"]["mts_run_id"] == "run-1"


def test_stamp_document_requires_a_file_and_at_least_one_property():
    adapter = adapter_module.GoogleDocsAdapter(FakeDrive(), FakeDocs())
    try:
        adapter.stamp_document("doc-1", {})
    except adapter_module.GoogleDocsAdapterError as error:
        assert "property" in str(error)
    else:
        raise AssertionError("An empty provenance stamp must fail closed.")


def test_stamp_document_rejects_a_property_over_the_drive_byte_limit():
    adapter = adapter_module.GoogleDocsAdapter(FakeDrive(), FakeDocs())
    try:
        adapter.stamp_document("doc-1", {"mts_spec_path": "x" * 200})
    except adapter_module.GoogleDocsAdapterError as error:
        assert "124-byte limit" in str(error)
    else:
        raise AssertionError("An oversized property must fail before reaching Drive.")


def main():
    tests = [
        test_render_pair_copies_masters_and_replaces_placeholder,
        test_publish_pair_moves_both_validated_artifacts_to_final_destination,
        test_unverified_spec_and_incomplete_pair_fail_closed,
        test_ensure_child_folder_is_idempotent,
        test_deliver_pair_copies_staged_documents_and_preserves_staging,
        test_deliver_pair_can_skip_the_answer_key,
        test_deliver_pair_rejects_unstaged_artifact_and_bad_mode,
        test_list_child_files_excludes_folders_and_lists_only_direct_children,
        test_list_child_folders_returns_newest_first,
        test_move_file_reparents_and_is_a_no_op_when_already_in_destination,
        test_move_file_requires_both_ids,
        test_trash_file_marks_the_file_trashed_and_never_deletes,
        test_stamp_document_records_provenance_and_listings_return_it,
        test_stamp_document_requires_a_file_and_at_least_one_property,
        test_stamp_document_rejects_a_property_over_the_drive_byte_limit,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
