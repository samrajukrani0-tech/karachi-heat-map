"""P2-04: the seeded sensitivity analysis."""

import json

import numpy as np
import pandas as pd
import pytest

CONFIDENCE_LABELS = {"high", "medium", "low"}


@pytest.fixture(scope="module")
def confidence(root):
    path = root / "data" / "processed" / "confidence.csv"
    assert path.exists(), "run `uv run python -m pipeline.sensitivity` first"
    return pd.read_csv(path)


@pytest.fixture(scope="module")
def sensitivity_cfg(model):
    return model["sensitivity"]


def test_the_run_is_large_enough(sensitivity_cfg, root):
    assert sensitivity_cfg["n"] >= 1000, "section 7 requires N >= 1000"
    meta = json.loads((root / "data" / "processed" / "sensitivity_meta.json")
                      .read_text(encoding="utf-8"))
    assert meta["draws"] >= 1000


def test_the_seed_is_fixed_and_recorded(sensitivity_cfg, root):
    assert isinstance(sensitivity_cfg["seed"], int)
    meta = json.loads((root / "data" / "processed" / "sensitivity_meta.json")
                      .read_text(encoding="utf-8"))
    assert meta["seed"] == sensitivity_cfg["seed"]


def test_rerunning_reproduces_the_committed_output_exactly(root):
    """The reproducibility test required by P2-04: a fixed seed must give a fixed answer,
    or none of the intervals below mean anything."""
    import warnings

    from pipeline.sensitivity import build
    before = (root / "data" / "processed" / "confidence.csv").read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        build()
    after = (root / "data" / "processed" / "confidence.csv").read_text(encoding="utf-8")
    assert before == after, "the same seed produced a different answer"


def test_one_row_per_grid_cell(confidence, root):
    grid = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    assert set(confidence["h3"]) == {f["properties"]["h3"] for f in grid["features"]}
    assert confidence["h3"].is_unique


def test_the_interval_brackets_the_median(confidence):
    assert (confidence["rank_low_5pct"] <= confidence["median_rank"]).all()
    assert (confidence["median_rank"] <= confidence["rank_high_95pct"]).all()
    assert (confidence["rank_interval_width"] >= 0).all()


def test_probabilities_are_probabilities(confidence):
    assert confidence["p_top20"].between(0.0, 1.0).all()


def test_certainty_is_never_below_a_half(confidence):
    """certainty = max(p, 1-p), so a coin flip is 0.5 and anything decisive is higher."""
    assert (confidence["certainty"] >= 0.5 - 1e-9).all()
    assert np.allclose(confidence["certainty"],
                       np.maximum(confidence["p_top20"], 1 - confidence["p_top20"]), atol=1e-4)


def test_confidence_labels_are_valid(confidence):
    assert set(confidence["confidence"]) <= CONFIDENCE_LABELS
    assert set(confidence["confidence_literal"]) <= CONFIDENCE_LABELS


def test_confidence_thresholds_match_the_config(confidence, sensitivity_cfg):
    classes = sensitivity_cfg["confidence_classes"]
    for _, row in confidence.iterrows():
        expected = ("high" if row["certainty"] >= classes["high"]
                    else "medium" if row["certainty"] >= classes["medium"] else "low")
        assert row["confidence"] == expected, row["h3"]


def test_the_literal_reading_is_kept_and_shows_why_it_is_wrong(confidence):
    """Q13: reading section 7's thresholds straight off P(top 20%) labels most of the map
    'low confidence' precisely because we are confident those cells are NOT in the top
    20%. Both columns are kept so the difference is visible rather than argued."""
    literal_low = (confidence["confidence_literal"] == "low").mean()
    certainty_low = (confidence["confidence"] == "low").mean()
    assert literal_low > 0.5, "the literal reading should label most of the map low"
    assert certainty_low < literal_low


def test_extremes_are_more_settled_than_the_middle(confidence):
    """The expected shape: the top and bottom of a ranking are stable, the middle is not.
    If this failed, the Monte Carlo would not be behaving like a ranking at all."""
    ordered = confidence.sort_values("rank")
    n = len(ordered)
    top = ordered.head(15)["rank_interval_width"].median()
    middle = ordered.iloc[n // 2 - 20: n // 2 + 20]["rank_interval_width"].median()
    assert top < middle, "the top of the ranking should be more stable than the middle"


def test_the_headline_top_20_percent_is_not_all_stable(confidence):
    """The honest finding this analysis exists to surface: a good part of the top-20%
    list does not survive reasonable variation in the weights and method."""
    top_n = int(np.ceil(0.20 * len(confidence)))
    headline_top = confidence[confidence["rank"] <= top_n]
    stable = (headline_top["p_top20"] >= 0.8).sum()
    assert stable < len(headline_top), (
        "if every top cell were stable the sensitivity analysis would be finding nothing"
    )


def test_empty_cells_sit_at_the_bottom_and_stay_there(confidence, root):
    scores = pd.read_csv(root / "data" / "processed" / "scores.csv")
    empty = set(scores[scores["exposure"] == 0.0]["h3"])
    rows = confidence[confidence["h3"].isin(empty)]
    assert (rows["p_top20"] == 0.0).all(), "a cell with nobody in it reached the top 20%"


def test_empty_cells_score_exactly_zero_in_every_draw(confidence, root):
    """D6b/D23 in the sensitivity analysis itself, not only in the headline score.

    The weaker test above passed while half the draws gave empty cells exposure 0.0379
    under percentile rank: they never reached the top 20%, but they did outrank real
    residents and widened everyone's intervals. Zero people must mean Priority 0 in every
    draw, so the whole 5-95% priority interval is zero and the rank never rises above
    the tied bottom rank."""
    scores = pd.read_csv(root / "data" / "processed" / "scores.csv")
    empty = set(scores[scores["exposure"] == 0.0]["h3"])
    bottom = int(scores["rank"].max())
    rows = confidence[confidence["h3"].isin(empty)]
    assert len(rows) == 21
    assert (rows["priority_high_95pct"] == 0.0).all()
    assert (rows["rank_low_5pct"] >= bottom).all()


def test_precompute_applies_the_structural_zero_under_both_methods(root):
    import warnings

    from pipeline.config import load
    from pipeline.sensitivity import precompute
    frame = pd.read_parquet(root / "data" / "processed" / "indicators.parquet")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        values = precompute(frame, load("indicators")["indicators"], load("model"))
    empty = (frame["population"] == 0).to_numpy()
    for method, v in values.items():
        assert (v["population"][empty] == 0.0).all(), method


def test_output_row_order_is_deterministic_across_machines(root):
    """Ties in rank must be ordered by a stable rule, not by quicksort's whim: CI's
    Linux runner ordered the 21 tied empty cells differently from macOS."""
    out = pd.read_csv(root / "data" / "processed" / "confidence.csv")
    key = list(zip(out["rank"], out["h3"], strict=True))
    assert key == sorted(key)
