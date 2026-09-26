"""P2-03: dimension scores, Priority and Intensity.

The property tests use SYNTHETIC arrays, so they check the arithmetic rather than
whatever the real data happens to look like.
"""

import itertools
import json

import numpy as np
import pandas as pd
import pytest

from pipeline.score import (
    IncompleteDimensionWarning,
    dimension_score,
    top_reasons,
    weighted_geometric_mean,
)


@pytest.fixture(scope="module")
def scores(root):
    path = root / "data" / "processed" / "scores.csv"
    assert path.exists(), "run `uv run python -m pipeline.score` first"
    return pd.read_csv(path)


@pytest.fixture(scope="module")
def used_weights(root):
    return json.loads((root / "data" / "processed" / "scores_weights_used.json")
                      .read_text(encoding="utf-8"))


# --- required property tests --------------------------------------------------------

def test_weights_sum_to_one(used_weights, weights):
    assert sum(weights["dimensions"].values()) == pytest.approx(1.0)
    assert sum(used_weights["dimension_exponents"].values()) == pytest.approx(1.0)
    for dimension, used in used_weights["within_dimension"].items():
        assert sum(used.values()) == pytest.approx(1.0), dimension


def test_raising_a_risk_increasing_indicator_never_lowers_priority():
    """The central monotonicity property: more risk in, never less priority out."""
    rng = np.random.default_rng(20260926)
    exponents = {"hazard": 1 / 3, "exposure": 1 / 3, "vulnerability": 1 / 3}
    for _ in range(200):
        parts = {k: rng.uniform(0.05, 1.0, size=6) for k in exponents}
        before = weighted_geometric_mean(parts, exponents)
        which = rng.choice(list(exponents))
        bumped = {k: (v.copy() if k != which else np.minimum(v + rng.uniform(0, 0.3), 1.0))
                  for k, v in parts.items()}
        after = weighted_geometric_mean(bumped, exponents)
        assert np.all(after >= before - 1e-12)


def test_raising_an_indicator_never_lowers_its_dimension_score():
    values = {"a": np.array([0.2, 0.5]), "b": np.array([0.4, 0.6])}
    weights = {"a": 0.4, "b": 0.6}
    before, _ = dimension_score(values, weights, "v", 2)
    values_up = {"a": np.array([0.9, 0.5]), "b": np.array([0.4, 0.6])}
    after, _ = dimension_score(values_up, weights, "v", 2)
    assert np.all(after >= before)


def test_results_do_not_depend_on_indicator_order():
    """Dictionary order is an implementation detail and must never reach the output."""
    values = {"a": np.array([0.2, 0.9]), "b": np.array([0.4, 0.1]), "c": np.array([0.7, 0.5])}
    weights = {"a": 0.2, "b": 0.3, "c": 0.5}
    baseline, _ = dimension_score(values, weights, "v", 2)
    for order in itertools.permutations("abc"):
        shuffled_values = {k: values[k] for k in order}
        shuffled_weights = {k: weights[k] for k in order}
        result, _ = dimension_score(shuffled_values, shuffled_weights, "v", 2)
        assert np.allclose(result, baseline)


def test_geometric_mean_does_not_depend_on_dimension_order():
    parts = {"hazard": np.array([0.4]), "exposure": np.array([0.7]),
             "vulnerability": np.array([0.9])}
    exponents = {"hazard": 1 / 3, "exposure": 1 / 3, "vulnerability": 1 / 3}
    baseline = weighted_geometric_mean(parts, exponents)
    for order in itertools.permutations(exponents):
        assert np.allclose(
            weighted_geometric_mean({k: parts[k] for k in order},
                                    {k: exponents[k] for k in order}), baseline)


# --- D6b: the asymmetric floor ------------------------------------------------------

def test_hazard_and_vulnerability_are_floored_but_exposure_is_not(scores, model):
    floors = model["aggregation"]["floor"]
    assert floors["exposure"] is None
    assert scores["hazard"].min() >= floors["hazard"] - 1e-9
    assert scores["vulnerability"].min() >= floors["vulnerability"] - 1e-9
    assert scores["exposure"].min() == 0.0, (
        "Exposure must be able to reach exactly 0: it means nobody lives there (D6b)"
    )


def test_an_empty_cell_scores_priority_zero(scores):
    """The whole point of leaving Exposure unfloored."""
    empty = scores[scores["exposure"] == 0.0]
    assert len(empty) > 0
    assert (empty["priority"] == 0.0).all()


def test_a_zero_part_zeroes_the_geometric_mean():
    parts = {"h": np.array([1.0]), "e": np.array([0.0]), "v": np.array([1.0])}
    result = weighted_geometric_mean(parts, {"h": 1 / 3, "e": 1 / 3, "v": 1 / 3})
    assert result[0] == 0.0


def test_geometric_mean_never_exceeds_the_arithmetic_mean():
    """AM-GM: the geometric choice is always the more cautious one (D6)."""
    rng = np.random.default_rng(5)
    for _ in range(100):
        parts = {k: rng.uniform(0.01, 1.0, size=20) for k in ("h", "e", "v")}
        geometric = weighted_geometric_mean(parts, {"h": 1 / 3, "e": 1 / 3, "v": 1 / 3})
        arithmetic = sum(parts.values()) / 3
        assert np.all(geometric <= arithmetic + 1e-12)


def test_exponents_that_do_not_sum_to_one_are_refused():
    with pytest.raises(ValueError, match="sum to"):
        weighted_geometric_mean({"a": np.array([0.5]), "b": np.array([0.5])},
                                {"a": 0.5, "b": 0.9})


# --- the missing indicator is handled out loud --------------------------------------

def test_a_missing_indicator_renormalises_the_rest_and_warns():
    values = {"lack_green": np.array([0.4, 0.8])}
    weights = {"lack_green": 1 / 3, "dist_health": 1 / 3, "dist_centre": 1 / 3}
    with pytest.warns(IncompleteDimensionWarning, match="dist_health"):
        score, used = dimension_score(values, weights, "vulnerability", 2)
    assert used == {"lack_green": 1.0}
    assert np.allclose(score, [0.4, 0.8]), "a lone indicator carries its dimension entirely"


def test_the_output_declares_that_the_model_is_incomplete(scores, used_weights):
    """dist_centre is blocked on Q2, and nothing may present the scores as final."""
    assert scores["model_incomplete"].all()
    assert scores["weights_provisional"].all()
    assert used_weights["missing_indicators"] == ["dist_centre"]
    assert "dist_centre" not in used_weights["within_dimension"]["vulnerability"]
    assert sum(used_weights["within_dimension"]["vulnerability"].values()) == pytest.approx(1.0)


# --- the real output ----------------------------------------------------------------

def test_one_row_per_grid_cell(scores, root):
    grid = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    assert set(scores["h3"]) == {f["properties"]["h3"] for f in grid["features"]}
    assert scores["h3"].is_unique


def test_every_score_is_within_zero_and_one(scores):
    for column in ("hazard", "exposure", "vulnerability", "priority", "intensity"):
        assert scores[column].min() >= 0.0, column
        assert scores[column].max() <= 1.0, column


def test_ranks_follow_priority(scores):
    ordered = scores.sort_values("rank")
    assert ordered["priority"].is_monotonic_decreasing
    assert ordered["rank"].iloc[0] == 1


def test_intensity_excludes_exposure_entirely(scores):
    """Intensity = sqrt(H*V) wherever it is defined. Section 7 calls this the
    "per-person view"; strictly it is exposure-BLIND rather than per-person, since no
    population term appears in it. See QUESTIONS.md Q11 on the wording."""
    populated = scores[scores["exposure"] > 0]
    expected = np.sqrt(populated["hazard"] * populated["vulnerability"])
    assert np.allclose(populated["intensity"], expected, atol=1e-5)


def test_intensity_and_priority_disagree_somewhere(scores):
    """If they ranked identically, Intensity would add nothing to the equity discussion."""
    from scipy.stats import spearmanr
    populated = scores[scores["exposure"] > 0]
    rho = spearmanr(populated["priority"], populated["intensity"]).statistic
    assert rho < 0.99, "Intensity is indistinguishable from Priority; check the formula"


def test_every_cell_has_plain_language_reasons(scores):
    populated = scores[scores["priority"] > 0]
    assert (populated["top_reasons"].str.len() > 0).all()
    for text in populated["top_reasons"].head(20):
        assert len(text.split(";")) <= 3
        assert not any(token in text for token in ("_", "lst_", "dist_"))


def test_reasons_are_above_the_median_only():
    values = {"a": np.array([0.9, 0.1, 0.5]), "b": np.array([0.2, 0.8, 0.5])}
    indicators = [{"id": "a", "reason_en": "reason A"}, {"id": "b", "reason_en": "reason B"}]
    assert top_reasons(values, indicators, 0) == ["reason A"]
    assert top_reasons(values, indicators, 1) == ["reason B"]


def test_a_cell_below_the_median_everywhere_still_says_something():
    """Found by testing the real output: 6 populated cells sit below the pilot median on
    every indicator, so nothing "pushes them above average" and the reasons list came back
    empty. That is a correct answer badly presented -- a blank panel looks broken."""
    from pipeline.score import NO_REASON_ABOVE_MEDIAN
    values = {"a": np.array([0.1, 0.9]), "b": np.array([0.1, 0.9])}
    indicators = [{"id": "a", "reason_en": "reason A"}, {"id": "b", "reason_en": "reason B"}]
    assert top_reasons(values, indicators, 0) == [NO_REASON_ABOVE_MEDIAN]


def test_no_populated_cell_is_left_without_an_explanation(scores):
    populated = scores[scores["priority"] > 0]
    assert populated["top_reasons"].notna().all()
    assert (populated["top_reasons"].astype(str).str.len() > 0).all()


# --- points raised by the third independent checker ---------------------------------

def test_intensity_is_undefined_where_nobody_lives(scores):
    """Intensity excludes Exposure, so "how bad is it for a person here" has no answer
    when there is no person here. Unmasked, an empty cell scored 0.74 and ranked 24th of
    265 on a measure described as a per-person view."""
    empty = scores[scores["exposure"] == 0.0]
    assert len(empty) > 0
    assert empty["intensity"].isna().all()
    populated = scores[scores["exposure"] > 0]
    assert populated["intensity"].notna().all()


def test_the_vulnerability_floor_is_currently_dead_code(scores, model):
    """Recorded rather than removed: the floor is specified by D6b and must stay in case
    the indicator set changes, but right now V never comes near it. If this ever starts
    failing, the floor has begun to bite and D6b's reasoning should be revisited."""
    assert scores["vulnerability"].min() > model["aggregation"]["floor"]["vulnerability"]


def test_the_three_dimensions_are_near_independent(root):
    """Measured: the dimensions carry complementary information rather than repeating
    each other. Good for an index -- but it also means no dimension dominates, so the
    ranking is sensitive to the weights, which the model report must say."""
    from scipy.stats import spearmanr
    frame = pd.read_parquet(root / "data" / "processed" / "indicators.parquet")
    assert abs(spearmanr(frame["lst_mean_c"], frame["population"]).statistic) < 0.2
    assert abs(spearmanr(frame["lst_mean_c"], frame["lack_green"]).statistic) < 0.2
