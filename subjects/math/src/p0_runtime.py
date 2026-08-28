"""MTS Worksheet P0 runtime helpers.

Stdlib-only utilities for curriculum-cache lookup, deterministic math checks,
WorksheetSpec structural checks, targeted rendered-text QA, and run telemetry.
This is intentionally small so ChatGPT/API/orchestrator implementations can
reuse the same semantics without a framework dependency.
"""
from __future__ import annotations

import ast
import json
import math
import operator as op
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

_ALLOWED_BINOPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod}
_ALLOWED_UNARY = {ast.UAdd: op.pos, ast.USub: op.neg}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def week_start_iso(value: str | date) -> str:
    d = date.fromisoformat(value) if isinstance(value, str) else value
    return (d.fromordinal(d.toordinal() - d.weekday())).isoformat()


def progressive_context(backbone: dict[str, Any], grade: str) -> dict[str, Any] | None:
    """Return the long-term MTS concept progression for a grade/course key.

    The progressive backbone is conceptual curriculum, not official CCS pacing.
    """
    grade_key = grade
    if grade.startswith("math_"):
        # NC Math 1/2 normally correspond to the Grade 9/10 progression in this backbone.
        grade_key = {"math_1": "grade_9", "math_2": "grade_10"}.get(grade, grade)
    entry = backbone.get("grades", {}).get(grade_key)
    if not entry:
        return None
    return {
        "grade": entry.get("grade"),
        "units": entry.get("units", {}),
        "source": "mts_progressive_backbone",
        "official_ccs_pacing": False,
    }


def resolve_curriculum(
    pacing: dict[str, Any],
    grade: str,
    on_date: str | date,
    backbone: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve cached weekly scope and optionally attach long-term progression context."""
    ws = week_start_iso(on_date)
    if ws in pacing.get("weeks", {}) and grade in pacing["weeks"][ws]:
        out = dict(pacing["weeks"][ws][grade])
        out.update({"week_start": ws, "source": "weekly_cache", "cache_hit": True})
    else:
        month = ws[:7]
        fallback = pacing.get("month_fallback", {}).get(month, {}).get(grade)
        if fallback:
            out = {
                "week_start": ws,
                "current": fallback,
                "topics": [],
                "spiral": [],
                "confidence": "inferred",
                "source": "month_cache",
                "cache_hit": True,
                "requires_weekly_resolution": True,
            }
        else:
            out = {"week_start": ws, "cache_hit": False, "requires_web_resolution": True}
    if backbone is not None:
        ctx = progressive_context(backbone, grade)
        if ctx is not None:
            out["progressive_context"] = ctx
    return out


def safe_number_expression(expr: str) -> float:
    """Evaluate numeric-only arithmetic expressions without eval()."""
    node = ast.parse(expr, mode="eval").body
    def walk(n: ast.AST) -> float:
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_BINOPS:
            return _ALLOWED_BINOPS[type(n.op)](walk(n.left), walk(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(n.op)](walk(n.operand))
        raise ValueError(f"Unsupported expression: {expr}")
    return walk(node)


def compute(method: str, inputs: dict[str, Any]) -> Any:
    """Deterministic validator methods used by common MTS worksheet questions."""
    if method == "arithmetic_expression":
        return safe_number_expression(str(inputs["expression"]))
    if method == "triangle_area":
        return inputs["base"] * inputs["height"] / 2
    if method == "parallelogram_area":
        return inputs["base"] * inputs["height"]
    if method == "trapezoid_area":
        return (inputs["base1"] + inputs["base2"]) * inputs["height"] / 2
    if method == "rectangle_area":
        return inputs["length"] * inputs["width"]
    if method == "rect_prism_surface_area":
        l, w, h = inputs["length"], inputs["width"], inputs["height"]
        return 2 * (l*w + l*h + w*h)
    if method == "cube_surface_area":
        return 6 * inputs["edge"] ** 2
    if method == "midpoint":
        return ((inputs["x1"] + inputs["x2"]) / 2, (inputs["y1"] + inputs["y2"]) / 2)
    if method == "distance":
        return math.hypot(inputs["x2"] - inputs["x1"], inputs["y2"] - inputs["y1"])
    if method == "gcf":
        return math.gcd(int(inputs["a"]), int(inputs["b"]))
    if method == "lcm":
        return math.lcm(int(inputs["a"]), int(inputs["b"]))
    if method == "linear_eval":
        return inputs["m"] * inputs["x"] + inputs.get("b", 0)
    if method == "quadratic_eval":
        x = inputs["x"]
        return inputs.get("a", 1)*x*x + inputs.get("b", 0)*x + inputs.get("c", 0)
    raise KeyError(f"Unknown verification method: {method}")


def equivalent(actual: Any, expected: Any, tol: float = 1e-9) -> bool:
    if isinstance(actual, tuple) and isinstance(expected, (tuple, list)):
        return len(actual) == len(expected) and all(equivalent(a, b, tol) for a, b in zip(actual, expected))
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(float(actual), float(expected), rel_tol=tol, abs_tol=tol)
    return actual == expected


def verify_question(question: dict[str, Any]) -> dict[str, Any]:
    v = question.get("verification")
    if not v:
        return {"number": question.get("number"), "status": "REASONING_REQUIRED"}
    if v.get("method") == "reasoning_review":
        return {
            "number": question.get("number"),
            "status": "REASONING_REQUIRED",
            "criterion": v.get("criterion"),
        }
    try:
        actual = compute(v["method"], v.get("inputs", {}))
        ok = equivalent(actual, question.get("answer"))
        return {"number": question.get("number"), "status": "PASS" if ok else "FAIL", "computed": actual, "expected": question.get("answer")}
    except Exception as exc:
        return {"number": question.get("number"), "status": "ERROR", "error": str(exc)}


def flatten_questions(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [q for s in spec.get("sections", []) for q in s.get("questions", [])]


def verify_spec(spec: dict[str, Any]) -> dict[str, Any]:
    qs = flatten_questions(spec)
    expected_count = spec.get("worksheet", {}).get("question_count")
    numbering = [q.get("number") for q in qs]
    structure_errors = []
    if len(qs) != expected_count:
        structure_errors.append(f"question_count expected {expected_count}, found {len(qs)}")
    if numbering != list(range(1, len(qs)+1)):
        structure_errors.append("question numbering is not contiguous from 1")
    results = [verify_question(q) for q in qs]
    deterministic_failures = [r for r in results if r["status"] in {"FAIL", "ERROR"}]
    reasoning_required = [r for r in results if r["status"] == "REASONING_REQUIRED"]
    status = "PASS" if not structure_errors and not deterministic_failures else "FAIL"
    return {
        "status": status,
        "questions": len(qs),
        "deterministic_checked": len(qs)-len(reasoning_required),
        "reasoning_required": len(reasoning_required),
        "failures": deterministic_failures,
        "structure_errors": structure_errors,
        "results": results,
    }


def targeted_text_qa(rendered_text: str, spec: dict[str, Any], *, answer_key: bool = False) -> dict[str, Any]:
    """Cheap post-render checks; visual/layout QA remains separate where required."""
    qs = flatten_questions(spec)
    checks: dict[str, bool] = {}
    checks["title_present"] = bool(spec.get("worksheet", {}).get("grade"))
    checks["all_question_numbers_present"] = all(f"{q['number']}." in rendered_text for q in qs)
    checks["no_unresolved_placeholders"] = not any(x in rendered_text for x in ["{{", "}}", "<PLACEHOLDER>"])
    checks["no_pending_approval_label"] = "PENDING-APPROVAL" not in rendered_text
    if answer_key:
        checks["answer_key_label"] = "ANSWER KEY" in rendered_text.upper()
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


@dataclass
class Telemetry:
    started: float = field(default_factory=time.perf_counter)
    wall_started_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())
    stages: dict[str, float] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    tool_calls: int = 0
    _stage_started: dict[str, float] = field(default_factory=dict)

    def start_stage(self, name: str) -> None:
        self._stage_started[name] = time.perf_counter()

    def end_stage(self, name: str) -> None:
        start = self._stage_started.pop(name)
        self.stages[name] = round(time.perf_counter() - start, 4)

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.wall_started_at,
            "completed_at": datetime.now().astimezone().isoformat(),
            "elapsed_seconds": round(time.perf_counter() - self.started, 4),
            "stage_seconds": self.stages,
            "tool_calls": self.tool_calls,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "token_usage": None,
        }


def template_cache_valid(manifest: dict[str, Any], worksheet_revision: str, answer_key_revision: str) -> dict[str, Any]:
    """Check whether cached template structure can be safely reused."""
    expected_ws = str(manifest.get("worksheet_template", {}).get("revision_id", ""))
    expected_key = str(manifest.get("answer_key_template", {}).get("revision_id", ""))
    checks = {
        "worksheet_revision_matches": str(worksheet_revision) == expected_ws,
        "answer_key_revision_matches": str(answer_key_revision) == expected_key,
    }
    return {
        "status": "HIT" if all(checks.values()) else "MISS",
        "cache_valid": all(checks.values()),
        "checks": checks,
        "expected": {"worksheet": expected_ws, "answer_key": expected_key},
        "actual": {"worksheet": str(worksheet_revision), "answer_key": str(answer_key_revision)},
    }


def targeted_text_qa_v2(rendered_text: str, spec: dict[str, Any], *, answer_key: bool = False) -> dict[str, Any]:
    """Targeted post-render content QA using only rendered text and WorksheetSpec.

    This intentionally does not replace visual/layout review where the MTS config
    requires it; it removes redundant full-structure rereads for content checks.
    """
    import re

    qs = flatten_questions(spec)
    ws = spec.get("worksheet", {})
    grade = str(ws.get("grade", "")).strip()
    title = str(ws.get("title", "")).strip()

    def numbered_line_present(n: int) -> bool:
        return bool(re.search(rf"(?m)^\s*{n}\.\s*", rendered_text))

    checks: dict[str, bool] = {
        "rendered_text_nonempty": bool(rendered_text.strip()),
        "grade_present": bool(grade) and grade.lower() in rendered_text.lower(),
        "all_question_numbers_present": all(numbered_line_present(int(q["number"])) for q in qs),
        "no_unresolved_placeholders": not any(x in rendered_text for x in ["{{", "}}", "<PLACEHOLDER>"]),
        "no_pending_approval_label": "PENDING-APPROVAL" not in rendered_text,
    }
    if title:
        checks["title_present"] = title.lower() in rendered_text.lower()
    if answer_key:
        checks["answer_key_label"] = "ANSWER KEY" in rendered_text.upper()

    expected_count = int(ws.get("question_count", len(qs)))
    checks["no_extra_numbered_slots"] = not any(
        numbered_line_present(n) for n in range(expected_count + 1, 33)
    )

    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "failed_checks": [k for k, ok in checks.items() if not ok],
    }
