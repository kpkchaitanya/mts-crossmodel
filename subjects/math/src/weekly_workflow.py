"""Prepare the Gate 1 scope review for a Math Weekly Worksheet batch."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from subject_module import MathSubjectError, MathSubjectModule


class WeeklyWorkflowError(ValueError):
    """Raised when a Math Weekly Worksheet scope review cannot be prepared."""


def prepare_scope_review(
    resolved_policy: Mapping[str, Any],
    *,
    on_date: str,
    subject_module: MathSubjectModule,
    grade_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve all requested Math weekly scopes and build Gate 1 review data."""
    if resolved_policy.get("subject") != "math":
        raise WeeklyWorkflowError("Math Weekly workflow requires a Math policy.")
    if resolved_policy.get("worksheet_type_id") != "weekly-worksheet":
        raise WeeklyWorkflowError("Math Weekly workflow requires the weekly-worksheet type.")

    catalog = subject_module._load_master_data()
    grade_catalog = subject_module.module_root / "knowledge" / str(catalog["grade_course_catalog"])
    grade_entries = subject_module_module_data(grade_catalog).get("grades_and_courses", [])
    requested = set(grade_ids) if grade_ids else None
    plans = []
    for entry in grade_entries:
        grade_id = entry.get("id")
        if not entry.get("enabled") or (requested is not None and grade_id not in requested):
            continue
        if grade_id == "grade_9_10":
            plans.append(_combined_high_school_plan(entry, on_date, resolved_policy, subject_module))
        else:
            scope = subject_module.resolve_curriculum({"grade_or_course": grade_id, "on_date": on_date})
            plan = subject_module.prepare_blueprint(scope, resolved_policy, resolved_policy)
            plans.append({"grade_or_course": grade_id, "curriculum_scopes": [scope], "plan": plan})

    if requested is not None and {plan["grade_or_course"] for plan in plans} != requested:
        raise WeeklyWorkflowError("One or more requested Math grades/courses are not enabled.")
    return {
        "gate": "scope_review",
        "status": "pending",
        "subject": "math",
        "worksheet_type": "weekly-worksheet",
        "on_date": on_date,
        "worksheet_plans": plans,
    }


def _combined_high_school_plan(
    entry: Mapping[str, Any],
    on_date: str,
    resolved_policy: Mapping[str, Any],
    subject_module: MathSubjectModule,
) -> dict[str, Any]:
    curriculum_scopes = [
        subject_module.resolve_curriculum({"grade_or_course": scope_id, "on_date": on_date})
        for scope_id in entry.get("curriculum_scopes", [])
    ]
    if len(curriculum_scopes) != 2:
        raise WeeklyWorkflowError("Combined Grades 9/10 must resolve Math 1 and Math 2 independently.")
    combined_scope = {"grade_or_course": entry["id"], "week_start": curriculum_scopes[0]["week_start"]}
    plan = subject_module.prepare_blueprint(combined_scope, resolved_policy, resolved_policy)
    grade_split = plan.get("curriculum_scope", {}).get("grade_split")
    if grade_split is not None:
        raise WeeklyWorkflowError("Combined scope must not supply its own grade split.")
    plan["grade_split"] = dict(resolved_policy["grade_defaults"][entry["id"]]["grade_split"])
    return {"grade_or_course": entry["id"], "curriculum_scopes": curriculum_scopes, "plan": plan}


def subject_module_module_data(path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))
