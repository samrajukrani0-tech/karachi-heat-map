"""P3-01: DESIGN.md's colour claims, measured rather than trusted.

Every contrast ratio and colour-blind claim in the design plan is re-derived here, so a
palette change that breaks accessibility fails the suite.
"""

import re

import numpy as np
import pytest

PAPER = "#FAF8F5"
RAMP = ["#F6E3D0", "#D4B5A4", "#B18678", "#8E584B", "#6C2A1F"]


def _linear(channel: np.ndarray) -> np.ndarray:
    channel = channel / 255
    return np.where(channel <= 0.04045, channel / 12.92, ((channel + 0.055) / 1.055) ** 2.4)


def luminance(colour: str) -> float:
    rgb = np.array([int(colour[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)
    r, g, b = _linear(rgb)
    return float(0.2126 * r + 0.7152 * g + 0.0722 * b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def simulate(colour: str, kind: str) -> str:
    rgb = np.array([int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    matrix = {
        "deuteranopia": [[0.625, 0.375, 0], [0.7, 0.3, 0], [0, 0.3, 0.7]],
        "protanopia": [[0.567, 0.433, 0], [0.558, 0.442, 0], [0, 0.242, 0.758]],
        "tritanopia": [[0.95, 0.05, 0], [0, 0.433, 0.567], [0, 0.475, 0.525]],
    }[kind]
    out = np.clip(np.round((np.array(matrix) @ rgb) * 255), 0, 255).astype(int)
    return "#{:02X}{:02X}{:02X}".format(*out)


@pytest.fixture(scope="module")
def design(root):
    return (root / "DESIGN.md").read_text(encoding="utf-8")


def test_body_text_clears_the_contrast_floor():
    for token in ("#1A1C1E", "#58554E", "#1F5E6B", "#6C2A1F"):
        assert contrast(token, PAPER) >= 4.5, token


def test_key_label_colours_clear_seven_to_one():
    """Sun glare: DESIGN.md requires >= 7:1 for key labels."""
    for token in ("#1A1C1E", "#58554E", "#6C2A1F"):
        assert contrast(token, PAPER) >= 7.0, f"{token} is {contrast(token, PAPER):.2f}:1"


def test_the_ramp_is_monotone_in_lightness():
    lums = [luminance(c) for c in RAMP]
    assert all(lums[i] > lums[i + 1] for i in range(len(lums) - 1)), "survives greyscale"


@pytest.mark.parametrize("kind", ["deuteranopia", "protanopia", "tritanopia"])
def test_the_ramp_order_survives_colour_blindness(kind):
    lums = [luminance(simulate(c, kind)) for c in RAMP]
    assert all(lums[i] > lums[i + 1] for i in range(len(lums) - 1))


def test_adjacent_ramp_steps_are_distinguishable():
    for i in range(len(RAMP) - 1):
        assert contrast(RAMP[i], RAMP[i + 1]) > 1.4


def test_the_design_states_measured_values_not_round_numbers(design):
    """The first draft claimed 7.0:1 for a colour that measured 6.59:1."""
    match = re.search(r"`--muted` \| `(#[0-9A-F]{6})`.*?(\d+\.\d+):1", design)
    assert match, "the muted token must state a measured ratio"
    token, claimed = match.group(1), float(match.group(2))
    assert abs(contrast(token, PAPER) - claimed) < 0.02, (
        f"DESIGN.md claims {claimed}:1 but {token} measures {contrast(token, PAPER):.2f}:1"
    )


def test_no_text_is_promised_on_ramp_colours(design):
    """Ink on the deepest step is 1.62:1, so this constraint must be written down."""
    assert contrast("#1A1C1E", RAMP[-1]) < 3.0
    assert "No text is ever drawn on a ramp colour" in design


def test_the_design_reviews_itself_against_the_avoid_list(design):
    """An explicit P3-01 acceptance criterion: the review and the revisions it forced."""
    assert "avoid-list" in design
    assert design.count("**Revised:**") >= 2, "the review must record what it changed"
    for item in ("terracotta", "acid-bright", "hairline columns", "all-caps",
                 "middle-dot", "highlighted word"):
        assert item in design.lower(), f"the avoid-list item {item!r} is not addressed"


def test_the_three_project_principles_are_present(design):
    assert "Three principles, specific to this project" in design
    assert "uncertainty is part of the answer" in design
    assert "Readable in sun" in design
    assert "verdict on a neighbourhood" in design


def test_wireframes_exist_at_both_widths(design):
    assert "### 375 px" in design and "### 1280 px" in design
    assert design.count("┌") >= 3, "ASCII wireframes are required at both widths"
