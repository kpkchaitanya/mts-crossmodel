"""Tests for the configurable answer-key decimal rounding in render_weekly_specs_to_drive."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import render_weekly_specs_to_drive as render  # noqa: E402


def test_display_answer_rounds_only_when_more_than_noise_threshold_decimals():
    # Floating-point noise (many raw decimal digits) gets rounded for display.
    assert render.display_answer(3.9999999999999996) == "4.00"


def test_display_answer_leaves_clean_short_decimals_unrounded():
    # Already-clean values with <= 3 decimal digits are shown as-is, not force-padded/truncated.
    assert render.display_answer(3.0) == "3.0"
    assert render.display_answer(0.125) == "0.125"
    assert render.display_answer(9.0) == "9.0"


def test_display_answer_decimal_places_is_configurable():
    assert render.display_answer(3.14159265, decimal_places=4) == "3.1416"
    assert render.display_answer(3.9999999999999996, decimal_places=0) == "4"


def test_display_answer_noise_threshold_is_configurable():
    assert render.display_answer(3.14159, noise_threshold=1) == "3.14"
    assert render.display_answer(3.14, noise_threshold=1) == "3.14"


def test_display_answer_leaves_ints_and_lists_readable():
    assert render.display_answer(7) == "7"
    assert render.display_answer([2, 11]) == "2, 11"
    assert render.display_answer([2, 3.9999999999999996]) == "2, 4.00"
