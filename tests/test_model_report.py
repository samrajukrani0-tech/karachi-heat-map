"""P2-06: the model report.

These tests re-read the committed outputs and assert the report still matches them, so a
report that goes stale fails loudly instead of quietly misreporting.
"""

import json

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def report(root):
    path = root / "docs" / "model-report.md"
    assert path.exists(), "docs/model-report.md is missing"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def outputs(root):
    p = root / "data" / "processed"
    return {
        "scores": pd.read_csv(p / "scores.csv"),
        "confidence": pd.read_csv(p / "confidence.csv"),
        "sensitivity": json.loads((p / "sensitivity_meta.json").read_text(encoding="utf-8")),
        "validation": json.loads((p / "validation.json").read_text(encoding="utf-8")),
    }


def test_it_has_the_required_sections(report):
    for heading in ("What this model says, in plain words", "Limitations",
                    "Maths appendix", "Figures", "Independent checks"):
        assert heading in report, f"missing section: {heading}"


def test_the_headline_numbers_match_the_data(report, outputs):
    scores, conf = outputs["scores"], outputs["confidence"]
    top_n = int(np.ceil(0.2 * len(scores)))
    stable = conf[conf["rank"] <= top_n]
    assert f"**{top_n} cells** fall in the top 20%" in report
    assert f"only {int((stable['p_top20'] >= 0.8).sum())} stay there" in report
    assert f"**{int((stable['p_top20'] < 0.5).sum())} of the {top_n} are on the wrong side" \
        in report


def test_the_stability_split_matches(report, outputs):
    meta = outputs["sensitivity"]
    assert f"**{meta['confidently_in']} confidently in**" in report
    assert f"**{meta['uncertain']} uncertain**" in report
    assert f"**{meta['confidently_out']} confidently out**" in report


def test_the_vulnerability_floor_claim_matches(report, outputs):
    """The report says the floor never fires; that must still be true."""
    minimum = outputs["scores"]["vulnerability"].min()
    assert "never fires" in report
    assert f"{minimum:.4f}" in report


def test_every_major_limitation_is_present(report):
    """Section 2.1 and the decisions: a reader must not have to dig for the bad news."""
    for claim in [
        "undercounts by roughly a factor of 2.3",      # D16
        "681,293",                                      # the census figure
        "not rescaled to match the census",             # section 2.1
        "the one this model cannot see",                # D20, load-shedding
        "not air temperature",                          # LST caveat
        "0.83 °C",                                      # the vegetation finding
        "exactly **−1.0000**",                          # D17, the age shares
        "6.01%",                                        # D18, OSM coverage
        "overstates** isolation",                       # direction of the OSM bias
        "areas, not individuals",
        "`dist_centre` has no data at all",             # the missing indicator
    ]:
        assert claim in report, f"the report omits: {claim}"


def test_the_face_validity_verdict_is_not_overclaimed(report, outputs):
    """The single incident must never be presented as confirmation."""
    assert "illustrative context only" in report
    assert "neither support nor refutation" in report
    ranks = outputs["validation"]["face_validity"]["ranks"]
    assert str(ranks) in report


def test_the_equal_weights_baseline_is_not_reported_as_a_result(report):
    assert "not available yet" in report
    assert "correlates a vector with itself" in report


def test_the_provisional_status_is_stated_at_the_top(report):
    head = report[:1200]
    assert "provisional" in head.lower()
    assert "P2-02b" in head and "P1-09b" in head


def test_the_maths_appendix_has_the_formulae(report):
    for formula in ("q_{95}", "H^{w_H}", "\\lambda_{\\max}", "\\sqrt{H \\cdot V}", "\\kappa"):
        assert formula in report, f"missing formula: {formula}"


def test_the_checker_verdicts_are_included(report):
    """An explicit acceptance criterion for P2-06."""
    assert "Independent checks" in report
    for feature in ("P2-01", "P2-02", "P2-03", "P2-04", "P2-05"):
        assert feature in report, f"no checker verdict recorded for {feature}"
    assert "found a real bug" in report


def test_the_ai_disclosure_is_present(report):
    """D12."""
    assert "Built with Claude Code as a coding assistant" in report
    assert "Samraj Lal Ukrani" in report


def test_it_never_calls_an_area_dangerous_or_unsafe(report):
    """Section 2.5 forbids calling an AREA dangerous, bad or unsafe. It does not forbid
    the word 'dangerous' about heat -- PROMPT.md section 1 itself says "circumstances that
    make heat more dangerous". This checks the rule, not the vocabulary."""
    lowered = report.lower()
    for banned in ("unsafe", "bad area", "bad neighbourhood", "slum", "dangerous area",
                   "dangerous neighbourhood", "dangerous cell", "dangerous place"):
        assert banned not in lowered, f"the report uses banned language: {banned!r}"
    # "dangerous" may only ever qualify heat or conditions, never a place.
    for sentence in report.split("."):
        if "dangerous" in sentence.lower():
            assert "heat" in sentence.lower(), (
                f"'dangerous' used without reference to heat: {sentence.strip()[:90]}"
            )


def test_the_interval_widths_match(report, outputs):
    """Added when a sensitivity fix moved the priority interval from 0.193 to 0.190 and
    nothing noticed that the report still said 0.193."""
    meta = outputs["sensitivity"]
    assert f"**{meta['median_rank_interval']:.0f} places**" in report
    assert f"**{meta['median_priority_interval']:.3f}** on a 0" in report
