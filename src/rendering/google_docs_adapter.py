"""Google Docs/Drive adapter with no embedded workflow policy or credentials."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class GoogleDocsAdapterError(ValueError):
    """Raised when a Google Docs/Drive operation cannot safely proceed."""


class GoogleDocsAdapter:
    """Copy, render, inspect, and publish worksheet document pairs through injected clients."""

    placeholder = "{{CONTENT}}"

    def __init__(self, drive: Any, docs: Any) -> None:
        self.drive = drive
        self.docs = docs

    def copy_master(self, template_id: str, destination_id: str, name: str) -> dict[str, Any]:
        """Copy a master document; this adapter never updates a master template."""
        if not template_id or not destination_id or not name:
            raise GoogleDocsAdapterError("template_id, destination_id, and name are required.")
        copied = self.drive.files().copy(
            fileId=template_id,
            body={"name": name, "parents": [destination_id]},
            fields="id,name,webViewLink",
        ).execute()
        if not copied.get("id"):
            raise GoogleDocsAdapterError("Google Drive did not return an ID for the copied template.")
        return copied

    def render_document(self, document_id: str, projection: str) -> None:
        """Replace the configured placeholder, or append to a copied document."""
        if not document_id:
            raise GoogleDocsAdapterError("document_id is required.")
        if not isinstance(projection, str):
            raise GoogleDocsAdapterError("Document projection must be text.")

        document = self.docs.documents().get(documentId=document_id).execute()
        body = document.get("body", {}).get("content", [])
        text = self._body_text(body)
        if self.placeholder in text:
            requests = [{"replaceAllText": {"containsText": {"text": self.placeholder, "matchCase": True}, "replaceText": projection}}]
        else:
            end_index = body[-1].get("endIndex", 1) - 1 if body else 1
            requests = [{"insertText": {"location": {"index": end_index}, "text": "\n" + projection}}]
        self.docs.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    def inspect_document(self, document_id: str) -> dict[str, Any]:
        """Return text/structure evidence for downstream QA."""
        document = self.docs.documents().get(documentId=document_id).execute()
        body = document.get("body", {}).get("content", [])
        return {"document_id": document_id, "text": self._body_text(body), "content_blocks": len(body)}

    def render_pair(
        self,
        spec: Mapping[str, Any],
        templates: Mapping[str, str],
        staging_destination_id: str,
        names: Mapping[str, str],
        projections: Mapping[str, str],
    ) -> dict[str, dict[str, Any]]:
        """Render a verified student/key pair from one Worksheet Spec revision."""
        if not self._is_verified(spec):
            raise GoogleDocsAdapterError("A passing Worksheet Spec is required before rendering.")
        required_keys = {"student_template_id", "answer_key_template_id"}
        if not required_keys.issubset(templates):
            raise GoogleDocsAdapterError("Both student and answer-key template IDs are required.")
        if {"student_worksheet", "answer_key"} - set(names) or {"student_worksheet", "answer_key"} - set(projections):
            raise GoogleDocsAdapterError("Both student and answer-key names and projections are required.")

        student = self.copy_master(templates["student_template_id"], staging_destination_id, names["student_worksheet"])
        answer_key = self.copy_master(templates["answer_key_template_id"], staging_destination_id, names["answer_key"])
        self.render_document(student["id"], projections["student_worksheet"])
        self.render_document(answer_key["id"], projections["answer_key"])
        return {
            "student_worksheet": {"artifact_kind": "student_worksheet", "status": "staged", "document": student},
            "answer_key": {"artifact_kind": "answer_key", "status": "staged", "document": answer_key},
        }

    def publish_pair(
        self,
        student_artifact: Mapping[str, Any],
        answer_key_artifact: Mapping[str, Any],
        destination_id: str,
    ) -> dict[str, Any]:
        """Move both validated artifacts to the same final destination as one publish operation."""
        if not destination_id:
            raise GoogleDocsAdapterError("Publication destination is required.")
        student_id = self._artifact_document_id(student_artifact, "student_worksheet")
        answer_key_id = self._artifact_document_id(answer_key_artifact, "answer_key")
        if student_id == answer_key_id:
            raise GoogleDocsAdapterError("Student Worksheet and Answer Key must be different documents.")

        published = []
        for document_id in (student_id, answer_key_id):
            metadata = self.drive.files().get(fileId=document_id, fields="id,name,parents,webViewLink").execute()
            parents = ",".join(metadata.get("parents", []))
            moved = self.drive.files().update(
                fileId=document_id,
                addParents=destination_id,
                removeParents=parents,
                fields="id,name,parents,webViewLink",
            ).execute()
            if destination_id not in moved.get("parents", []):
                raise GoogleDocsAdapterError("Published document is not in the requested destination.")
            published.append(moved)
        return {"status": "published", "student_worksheet": published[0], "answer_key": published[1]}

    @staticmethod
    def _body_text(body: list[dict[str, Any]]) -> str:
        text = []
        for item in body:
            for element in item.get("paragraph", {}).get("elements", []):
                text_run = element.get("textRun")
                if text_run:
                    text.append(text_run.get("content", ""))
        return "".join(text)

    @staticmethod
    def _is_verified(spec: Mapping[str, Any]) -> bool:
        status = spec.get("verification_status")
        if status is None:
            status = spec.get("verification", {}).get("status")
        return str(status).upper() == "PASS"

    @staticmethod
    def _artifact_document_id(artifact: Mapping[str, Any], expected_kind: str) -> str:
        if artifact.get("artifact_kind") != expected_kind or artifact.get("status") != "validated":
            raise GoogleDocsAdapterError(f"Validated {expected_kind} artifact is required.")
        document_id = artifact.get("document", {}).get("id")
        if not isinstance(document_id, str) or not document_id:
            raise GoogleDocsAdapterError(f"{expected_kind} artifact must provide a document ID.")
        return document_id
