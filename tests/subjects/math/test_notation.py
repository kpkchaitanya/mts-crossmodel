"""Tests for the Unicode math-notation helpers."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from mts.subjects.math import notation


def test_superscript_renders_common_exponents():
    assert notation.superscript(2) == "\u00b2"
    assert notation.superscript(3) == "\u00b3"
    assert notation.superscript(-1) == "\u207b\u00b9"


def test_subscript_renders_index_digits():
    assert notation.subscript(1) == "\u2081"
    assert notation.subscript(2) == "\u2082"


def test_radical_uses_dedicated_glyphs_for_square_and_cube_roots():
    assert notation.radical(25) == "\u221a25"
    assert notation.radical(27, index=3) == "\u221b27"
    assert notation.radical(16, index=4) == "\u221c16"


def test_radical_falls_back_for_unsupported_index():
    assert notation.radical(32, index=5) == f"{notation.superscript(5)}\u221a32"


def test_fraction_prefers_common_glyph_and_falls_back():
    assert notation.fraction(1, 2) == "\u00bd"
    assert notation.fraction(3, 4) == "\u00be"
    assert notation.fraction(5, 7) == "5/7"


def test_interval_renders_all_bracket_combinations():
    assert notation.interval(2, 5) == "[2, 5]"
    assert notation.interval(2, 5, left_closed=False) == "(2, 5]"
    assert notation.interval(2, 5, right_closed=False) == "[2, 5)"
    assert notation.interval(2, 5, left_closed=False, right_closed=False) == "(2, 5)"


def test_absolute_value_wraps_expression():
    assert notation.absolute_value(-7) == "|-7|"
    assert notation.absolute_value("x - 3") == "|x - 3|"


def test_operator_and_geometry_constants_are_unicode_not_ascii():
    assert notation.TIMES == "\u00d7" and notation.TIMES != "*"
    assert notation.DIVIDE == "\u00f7" and notation.DIVIDE != "/"
    assert notation.LESS_EQUAL == "\u2264"
    assert notation.GREATER_EQUAL == "\u2265"
    assert notation.DEGREE == "\u00b0"
    assert notation.PI == "\u03c0"


def test_grade_band_notation_covers_active_grades():
    for grade in ["grade_1", "grade_4", "grade_5", "grade_6", "math_1_2"]:
        assert grade in notation.GRADE_BAND_NOTATION


def main():
    tests = [
        test_superscript_renders_common_exponents,
        test_subscript_renders_index_digits,
        test_radical_uses_dedicated_glyphs_for_square_and_cube_roots,
        test_radical_falls_back_for_unsupported_index,
        test_fraction_prefers_common_glyph_and_falls_back,
        test_interval_renders_all_bracket_combinations,
        test_absolute_value_wraps_expression,
        test_operator_and_geometry_constants_are_unicode_not_ascii,
        test_grade_band_notation_covers_active_grades,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ALL_PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()

