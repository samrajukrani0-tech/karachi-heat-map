"""P2-05: the validation pack. Synthetic rankings only -- no real expert data exists."""

import json

import numpy as np
import pytest

from pipeline.validate import expert_agreement


@pytest.fixture(scope="module")
def report(root):
    path = root / "data" / "processed" / "validation.json"
    assert path.exists(), "run `uv run python -m pipeline.validate` first"
    return json.loads(path.read_text(encoding="utf-8"))


# --- (a) agreement with alternative weightings --------------------------------------

def test_equal_weights_baseline_is_reported(report):
    key = "equal weights (the configured baseline)"
    assert key in report["equal_weights_and_alternatives"]
    assert "spearman" in report["equal_weights_and_alternatives"][key]


def test_the_baseline_is_currently_uninformative_and_says_so(report):
    """The configured weights ARE equal weights while P2-02b is blocked, so rho = 1 by
    construction. Anything else would mean the comparison was not what it claims."""
    if report["weights_provisional"]:
        rho = report["equal_weights_and_alternatives"][
            "equal weights (the configured baseline)"]["spearman"]
        assert rho == pytest.approx(1.0, abs=1e-6)


def test_alternative_weightings_do_move_the_ranking(report):
    """If every weighting gave the same ranking, the weights would carry no meaning."""
    for label, stats in report["equal_weights_and_alternatives"].items():
        if "equal weights" in label:
            continue
        assert stats["spearman"] < 1.0, f"{label} is indistinguishable from the baseline"
        assert stats["spearman"] > 0.5, f"{label} disagrees implausibly"


# --- (b) face validity, and the guard against overclaiming it ------------------------

def test_face_validity_carries_no_evidentiary_weight(report):
    """Strengthened after the checker: D14 called it weak; a single incident with no
    denominator is not weak evidence, it is no evidence."""
    face = report["face_validity"]
    assert "illustrative" in face["verdict_strength"]
    assert len(face["why_weak"]) >= 3


def test_every_candidate_reading_of_the_location_is_reported(report):
    """D14 and section 2.1: the incident is a phrase, not a coordinate. Reporting one
    reading would imply a precision the source does not have."""
    candidates = report["face_validity"]["candidates"]
    assert len(candidates) >= 3
    assert len({c["cell"] for c in candidates}) > 1, "the readings must differ"
    assert all("of_cells" in c for c in candidates if c.get("inside_pilot"))


def test_the_face_validity_result_is_not_presented_as_support(report):
    """The measured ranks sit mid-table. This test exists so that if someone later
    rewrites the summary to claim the model was confirmed, it fails."""
    ranks = report["face_validity"]["ranks"]
    n = report["face_validity"]["candidates"][0]["of_distinguishable_positions"]
    assert ranks, "no candidate fell inside the pilot area"
    # A genuine confirmation would put the incident near the top. It does not.
    assert min(ranks) > n * 0.2, (
        "the incident now ranks in the top 20%; the write-up says the check is "
        "uninformative, so revisit D14 and the model report before changing this test"
    )


def test_the_source_is_cited_and_not_invented(report):
    source = report["face_validity"]["source"]
    assert "Express Tribune" in source and "Q1" in source


# --- (c) the expert-ranking analysis, on SYNTHETIC data ------------------------------

SYNTHETIC_MODEL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def test_perfect_agreement():
    result = expert_agreement(SYNTHETIC_MODEL, SYNTHETIC_MODEL)
    assert result["spearman"] == pytest.approx(1.0)
    assert result["kendall"] == pytest.approx(1.0)
    assert result["spearman_ci95"][0] == pytest.approx(1.0)


def test_perfect_disagreement():
    result = expert_agreement(SYNTHETIC_MODEL, SYNTHETIC_MODEL[::-1])
    assert result["spearman"] == pytest.approx(-1.0)


def test_partial_agreement_has_a_confidence_interval_that_brackets_it():
    expert = [1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 12]  # SYNTHETIC: neighbours swapped
    result = expert_agreement(SYNTHETIC_MODEL, expert)
    low, high = result["spearman_ci95"]
    assert low <= result["spearman"] <= high
    assert 0.8 < result["spearman"] < 1.0


def test_a_small_sample_gives_a_wide_interval():
    """Twelve localities cannot pin down a correlation, and the interval must show it."""
    rng = np.random.default_rng(1)
    expert = list(rng.permutation(SYNTHETIC_MODEL))
    result = expert_agreement(SYNTHETIC_MODEL, expert)
    low, high = result["spearman_ci95"]
    assert high - low > 0.5, "a 12-locality bootstrap interval should be wide"


def test_it_is_reproducible():
    a = expert_agreement(SYNTHETIC_MODEL, SYNTHETIC_MODEL[::-1])
    b = expert_agreement(SYNTHETIC_MODEL, SYNTHETIC_MODEL[::-1])
    assert a == b


def test_mismatched_or_tiny_inputs_are_refused():
    with pytest.raises(ValueError, match="same localities"):
        expert_agreement([1, 2, 3], [1, 2])
    with pytest.raises(ValueError, match="at least three"):
        expert_agreement([1, 2], [2, 1])


def test_no_real_expert_rankings_are_claimed(report):
    """Section 2.1: nothing may present synthetic rankings as field data."""
    assert report["expert_ranking"]["real_rankings_collected"] is False


def test_the_form_exists_and_asks_before_showing_the_map(root):
    form = (root / "docs" / "expert-ranking-form.md").read_text(encoding="utf-8")
    assert "before** looking at the map" in form
    assert "no right answers" in form.lower()
    assert "collects no personal data" in form


# --- points raised by the independent checker ---------------------------------------

def test_ranks_are_reported_against_distinguishable_positions(report):
    """21 unpopulated cells tie at the bottom, so ranks run 1..245, not 1..265. Quoting
    'of 265' would imply more resolution than the model has."""
    for candidate in report["face_validity"]["candidates"]:
        if candidate.get("inside_pilot"):
            assert candidate["of_distinguishable_positions"] < candidate["of_cells"]
            assert candidate["rank"] <= candidate["of_distinguishable_positions"]


def test_the_face_validity_verdict_carries_no_evidentiary_weight(report):
    """The checker went further than D14: a single incident has no denominator, so it
    cannot support or refute anything. The wording must say so."""
    face = report["face_validity"]
    assert "illustrative" in face["verdict_strength"]
    assert any("denominator" in reason for reason in face["why_weak"])
    assert any("neither support nor refutation" in reason for reason in face["why_weak"])


def test_the_equal_weights_baseline_declares_itself_a_tautology(report):
    """Reporting 'Spearman vs equal weights: 1.0' reads as agreement between two methods.
    It is a vector correlated with itself while the weights remain provisional."""
    if report["weights_provisional"]:
        status = report["equal_weights_baseline_status"]
        assert "not applicable yet" in status
        assert "1.0 by construction" in status
        assert "P2-04" in status, "it must point at what answers the question meanwhile"


def test_a_permutation_test_is_reported_not_just_an_interval():
    """'Better than chance' is a test, not an interval."""
    result = expert_agreement([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                              [1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 12])
    assert result["permutation_p_one_sided"] < 0.01
    assert result["spearman"] == pytest.approx(0.9650, abs=1e-4)
    assert result["kendall"] == pytest.approx(0.8485, abs=1e-4)


def test_a_chance_ranking_does_not_pass_the_permutation_test():
    rng = np.random.default_rng(4)
    model = list(range(1, 13))
    expert = list(rng.permutation(model))
    result = expert_agreement(model, expert)
    assert result["permutation_p_one_sided"] > 0.05


def test_fisher_interval_is_reported_and_does_not_pin_at_one():
    """Near rho = 1 the percentile bootstrap hits the ceiling; Fisher-z does not."""
    result = expert_agreement([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                              [1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 12])
    assert result["spearman_ci95"][1] == pytest.approx(1.0)
    assert result["spearman_ci95_fisher"][1] < 1.0


def test_the_power_limitation_is_stated(report):
    """12 localities can only detect very strong agreement, and the form says so."""
    expert = report["expert_ranking"]
    assert expert["n_localities"] >= 10
    assert "0.50" in expert["power_note"] and "25" in expert["power_note"]


def test_localities_are_real_places_not_invented(report, root):
    """Section 2.1: every locality on the form is an OSM place node inside Landhi."""
    assert "OpenStreetMap" in report["expert_ranking"]["localities_source"]
    form = (root / "docs" / "expert-ranking-form.md").read_text(encoding="utf-8")
    for name in report["expert_ranking"]["localities"]:
        assert name in form
    assert "certainly incomplete" in form, "the form must admit the list is partial"
