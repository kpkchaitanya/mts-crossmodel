"""Unicode-based mathematical notation and text-formatting helpers, Grades 1-12.

Used by question authoring to avoid leaking raw Python/ASCII syntax (e.g. `25**(1/2)`, `x^2`,
`*`, `/`, `>=`) into worksheet prompts. Organized by category so authors can pick the right
symbol for a grade band; see `GRADE_BAND_NOTATION` for a per-grade-band guide and
specs/generate_math_worksheets/03. design/design.md for the broader question-authoring design
this supports.
"""
from __future__ import annotations

_SUPERSCRIPT = str.maketrans("0123456789+-()", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207a\u207b\u207d\u207e")
_SUBSCRIPT = str.maketrans("0123456789+-()", "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089\u208a\u208b\u208d\u208e")

_RADICAL_SYMBOLS = {2: "\u221a", 3: "\u221b", 4: "\u221c"}  # √, ∛, ∜

_COMMON_FRACTIONS = {
    (1, 2): "\u00bd", (1, 3): "\u2153", (2, 3): "\u2154", (1, 4): "\u00bc", (3, 4): "\u00be",
    (1, 5): "\u2155", (2, 5): "\u2156", (3, 5): "\u2157", (4, 5): "\u2158",
    (1, 6): "\u2159", (5, 6): "\u215a", (1, 8): "\u215b", (3, 8): "\u215c", (5, 8): "\u215d", (7, 8): "\u215e",
}

# ---- Basic operators (never display raw "*"/"/"//">="/"<=" to students) ----
TIMES = "\u00d7"
DIVIDE = "\u00f7"
PLUS_MINUS = "\u00b1"
APPROX = "\u2248"
NOT_EQUAL = "\u2260"
LESS_EQUAL = "\u2264"
GREATER_EQUAL = "\u2265"

# ---- Geometry ----
DEGREE = "\u00b0"
ANGLE = "\u2220"
PARALLEL = "\u2225"
PERPENDICULAR = "\u22a5"
TRIANGLE = "\u25b3"
PI = "\u03c0"

# ---- Sets, intervals, and advanced (grades 8-12) ----
INFINITY = "\u221e"
ELEMENT_OF = "\u2208"
UNION = "\u222a"
INTERSECTION = "\u2229"
SUBSET = "\u2286"
THETA = "\u03b8"
DELTA = "\u0394"

# Per-grade-band notation guide: what's appropriate to introduce, and what to avoid, at each band.
# Advisory only -- authoring still uses judgment for grade-appropriateness (not enforced by code).
GRADE_BAND_NOTATION = {
    "grade_1": {"operators": "+ - only", "avoid": ["\u00d7", "\u00f7", "negatives", "exponents", "fractions beyond halves/thirds"]},
    "grade_4": {"operators": f"+ - {TIMES} {DIVIDE}", "fractions": "common unit fractions ok"},
    "grade_5": {"operators": f"+ - {TIMES} {DIVIDE}", "fractions": "a/b plus common glyphs", "decimals": True},
    "grade_6": {"exponents": "squares/cubes only (\u00b2 \u00b3)", "ratios": "a:b", "negatives": True, "geometry": f"{DEGREE} {ANGLE} {PI}"},
    "math_1_2": {"exponents": "general and rational (\u221a \u221b)", "functions": "f(x)", "sets_intervals": True, "absolute_value": True},
}


def superscript(value: int | str) -> str:
    """Render an integer (or a string of digits/+/-/parens) using Unicode superscript characters."""
    return str(value).translate(_SUPERSCRIPT)


def subscript(value: int | str) -> str:
    """Render an integer (or a string of digits/+/-/parens) using Unicode subscript characters."""
    return str(value).translate(_SUBSCRIPT)


def radical(n: int | str, index: int = 2) -> str:
    """Render a radical (square/cube/4th root) using a Unicode radical symbol.

    Falls back to `<superscript index>√n` for indices with no dedicated Unicode glyph (5th root+).
    """
    symbol = _RADICAL_SYMBOLS.get(index)
    if symbol:
        return f"{symbol}{n}"
    return f"{superscript(index)}\u221a{n}"


def fraction(numerator: int, denominator: int) -> str:
    """Render a fraction, preferring a precomposed Unicode glyph for common cases."""
    glyph = _COMMON_FRACTIONS.get((numerator, denominator))
    return glyph if glyph else f"{numerator}/{denominator}"


def interval(a, b, *, left_closed: bool = True, right_closed: bool = True) -> str:
    """Render an interval, e.g. interval(2, 5, left_closed=False) -> '(2, 5]'."""
    left = "[" if left_closed else "("
    right = "]" if right_closed else ")"
    return f"{left}{a}, {b}{right}"


def absolute_value(expr) -> str:
    return f"|{expr}|"
