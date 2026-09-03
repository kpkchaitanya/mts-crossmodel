"""Math subject-module behavior backed by target data/master paths."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from mts.subjects.math import p0_runtime as p0
from mts.subjects.math import question_plan


class MathSubjectError(ValueError):
	"""Raised when a Math subject-module request is incomplete or invalid."""


class MathSubjectModule:
	"""Adapt Math curriculum, verification, and QA capabilities to the target layout."""

	subject_id = "math"

	def __init__(self, module_root: str | Path | None = None) -> None:
		self.module_root = Path(module_root) if module_root else Path(__file__).resolve().parents[4] / "data" / "master" / "subjects" / "math"

	def resolve_curriculum(
		self,
		request: Mapping[str, Any],
		knowledge: Mapping[str, Any] | None = None,
		effective_config: Mapping[str, Any] | None = None,
	) -> dict[str, Any]:
		"""Resolve Math curriculum from local master-data assets."""
		grade = request.get("grade_or_course")
		on_date = request.get("on_date")
		if not isinstance(grade, str) or not grade:
			raise MathSubjectError("Math curriculum request must provide grade_or_course.")
		if not isinstance(on_date, str) or not on_date:
			raise MathSubjectError("Math curriculum request must provide on_date.")

		sources = knowledge or self._load_master_data()
		try:
			pacing = p0.load_json(self.module_root / str(sources["weekly_pacing_cache"]))
			backbone = p0.load_json(self.module_root / str(sources["yearly_progression"]))
			standards = p0.load_json(self.module_root / str(sources["standards"]))
		except KeyError as error:
			raise MathSubjectError(f"Math knowledge index is missing {error.args[0]}.") from error

		resolved = p0.resolve_curriculum(pacing, grade, on_date, backbone, standards)
		resolved["grade_or_course"] = grade
		return resolved

	def prepare_blueprint(
		self,
		scope: Mapping[str, Any],
		worksheet_type: Mapping[str, Any],
		effective_config: Mapping[str, Any],
	) -> dict[str, Any]:
		"""Resolve the Worksheet Type count/duration for an approved Math scope."""
		grade = scope.get("grade_or_course")
		if not isinstance(grade, str) or not grade:
			raise MathSubjectError("Math scope must provide grade_or_course.")
		grade_defaults = worksheet_type.get("grade_defaults", {})
		grade_config = grade_defaults.get(grade)
		if not isinstance(grade_config, Mapping):
			raise MathSubjectError(f"Worksheet Type has no Math defaults for {grade}.")
		count_key = "questions_per_week" if worksheet_type.get("worksheet_type_id") == "weekly-worksheet" else "questions_per_worksheet"
		if count_key not in grade_config:
			raise MathSubjectError(f"Worksheet Type has no {count_key} default for {grade}.")
		if worksheet_type.get("worksheet_type_id") == "weekly-worksheet":
			daily_count = grade_config.get("questions_per_day")
			sections = worksheet_type.get("sections", ())
			if not isinstance(daily_count, int) or not isinstance(sections, (list, tuple)) or not sections:
				raise MathSubjectError(f"Weekly Worksheet has invalid daily count or sections for {grade}.")
			if grade_config[count_key] != daily_count * len(sections):
				raise MathSubjectError(f"Weekly questions_per_week must equal questions_per_day times sections for {grade}.")
		return {
			"subject": self.subject_id,
			"grade_or_course": grade,
			"grade_display_name": self._display_name_for_grade(grade),
			"worksheet_type": worksheet_type.get("worksheet_type_id"),
			count_key: grade_config[count_key],
			"duration_minutes": worksheet_type.get("duration_minutes"),
			"curriculum_scope": deepcopy(dict(scope)),
			**({"questions_per_day": grade_config["questions_per_day"]} if worksheet_type.get("worksheet_type_id") == "weekly-worksheet" else {}),
		}

	def build_spec(self, plan: Mapping[str, Any], approved_inputs: Mapping[str, Any]) -> dict[str, Any]:
		"""Accept a generated candidate Spec; question generation remains AI-owned."""
		candidate = approved_inputs.get("spec")
		if not isinstance(candidate, Mapping):
			raise MathSubjectError("Math build_spec requires a generated candidate spec.")
		return deepcopy(dict(candidate))

	def verify_spec(self, spec: Mapping[str, Any], effective_config: Mapping[str, Any] | None = None) -> dict[str, Any]:
		"""Run deterministic Math verification."""
		return p0.verify_spec(deepcopy(dict(spec)))

	def build_week_plan(
		self,
		sections: list[Mapping[str, Any]],
		primary_skills: list[str],
		spiral_skills: list[str] | None,
		slots_per_day: int,
		*,
		difficulty: str = question_plan.DEFAULT_DIFFICULTY,
		diversity: str = question_plan.DEFAULT_DIVERSITY,
		topic_overrides: list[Mapping[str, Any]] | None = None,
		form_diversity: str = question_plan.DEFAULT_FORM_DIVERSITY,
		variation_seed: int | None = None,
		grade_or_course: str | None = None,
	) -> dict[str, list[dict[str, Any]]]:
		"""Build the per-day skill/form/difficulty authoring plan."""
		return question_plan.build_week_plan(
			sections=[dict(section) for section in sections],
			primary_skills=primary_skills,
			spiral_skills=spiral_skills,
			slots_per_day=slots_per_day,
			difficulty=difficulty,
			diversity=diversity,
			topic_overrides=[dict(override) for override in topic_overrides] if topic_overrides else None,
			form_diversity=form_diversity,
			variation_seed=variation_seed,
			grade_or_course=grade_or_course,
			form_compatibility=self._load_form_compatibility() if grade_or_course and variation_seed is not None else None,
		)

	def check_diversity_and_progression(self, spec: Mapping[str, Any], *, diversity: str = question_plan.DEFAULT_DIVERSITY) -> dict[str, Any]:
		"""Validate per-day difficulty progression and skill diversity."""
		return question_plan.validate_progression(deepcopy(dict(spec)), diversity=diversity)

	def check_form_diversity(
		self,
		spec: Mapping[str, Any],
		*,
		grade_or_course: str,
		form_diversity: str = question_plan.DEFAULT_FORM_DIVERSITY,
	) -> dict[str, Any]:
		"""Validate Math form metadata and prompt uniqueness."""
		return question_plan.validate_form_diversity(
			deepcopy(dict(spec)),
			grade_or_course=grade_or_course,
			form_compatibility=self._load_form_compatibility(),
			form_diversity=form_diversity,
		)

	def review_guidance(self, spec: Mapping[str, Any], effective_config: Mapping[str, Any]) -> dict[str, Any]:
		return {
			"requires_reasoning_review": True,
			"checks": ["ambiguity", "sufficient_information", "grade_appropriateness", "question_answer_consistency"],
		}

	def render_requirements(self, spec: Mapping[str, Any], worksheet_type: Mapping[str, Any]) -> dict[str, Any]:
		return {
			"plain_fraction_notation": "3/8",
			"avoid_raw_latex": True,
			"template_manifest": worksheet_type.get("template_selection", {}).get("template_manifest"),
		}

	def validate_subject_output(self, artifacts: Mapping[str, str], spec: Mapping[str, Any]) -> dict[str, Any]:
		student_text = artifacts.get("student_worksheet")
		answer_key_text = artifacts.get("answer_key")
		if not isinstance(student_text, str) or not isinstance(answer_key_text, str):
			raise MathSubjectError("Math output validation requires student_worksheet and answer_key text.")
		return {
			"student_worksheet": p0.targeted_text_qa_v2(student_text, deepcopy(dict(spec))),
			"answer_key": p0.targeted_text_qa_v2(answer_key_text, deepcopy(dict(spec)), answer_key=True),
		}

	def _load_master_data(self) -> dict[str, Any]:
		return p0.load_json(self.module_root / "master_data_index.json")

	def _load_form_compatibility(self) -> dict[str, Any]:
		master_data = self._load_master_data()
		try:
			relative_path = str(master_data["question_form_compatibility"])
		except KeyError as error:
			raise MathSubjectError("Math knowledge index is missing question_form_compatibility.") from error
		return p0.load_json(self.module_root / relative_path)

	def _display_name_for_grade(self, grade_or_course: str) -> str:
		master_data = self._load_master_data()
		catalog = p0.load_json(self.module_root / str(master_data["grade_course_catalog"]))
		for entry in catalog.get("grades_and_courses", []):
			if entry.get("id") == grade_or_course:
				return str(entry["display_name"])
		raise MathSubjectError(f"Math grade/course {grade_or_course!r} is not registered.")


__all__ = ["MathSubjectError", "MathSubjectModule"]
