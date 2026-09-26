"""P1-07: per-cell age shares, the zero-population rule, and the D17 finding."""

import csv
import json

import numpy as np
import pytest


@pytest.fixture(scope="module")
def rows(root):
    path = root / "data" / "processed" / "age_cells.csv"
    assert path.exists(), "run `uv run python -m pipeline.demographics` first"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def population_cfg(root):
    import yaml
    return yaml.safe_load((root / "config" / "population.yaml").read_text(encoding="utf-8"))


def test_one_row_per_grid_cell(rows, root):
    grid = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    ids = [r["h3"] for r in rows]
    assert len(ids) == len(set(ids))
    assert set(ids) == {f["properties"]["h3"] for f in grid["features"]}


def test_shares_are_within_zero_and_one(rows):
    for row in rows:
        for column in ("share_over60", "share_under5"):
            if row[column]:
                assert 0.0 <= float(row[column]) <= 1.0, f"{row['h3']} {column}"


def test_shares_are_plausible(rows, population_cfg):
    limits = population_cfg["plausibility"]
    for row in rows:
        if row["share_over60"]:
            assert float(row["share_over60"]) <= limits["share_over60_max"]
            assert float(row["share_under5"]) <= limits["share_under5_max"]


# --- the zero-population rule (an explicit acceptance criterion) --------------------

def test_zero_population_cells_have_undefined_shares_not_zero(rows, population_cfg):
    """A share is a ratio: with no residents it is undefined, not 0, and never imputed."""
    flag = population_cfg["zero_population"]["flag"]
    empty = [r for r in rows if float(r["population"]) <= 0]
    assert empty, "expected some cells with no modelled residents"
    for row in empty:
        assert row["share_over60"] == "", f"{row['h3']} has a share despite no residents"
        assert row["share_under5"] == ""
        assert flag in row["flags"]


def test_populated_cells_always_have_shares(rows):
    for row in rows:
        if float(row["population"]) > 0:
            assert row["share_over60"] and row["share_under5"], row["h3"]
            assert row["flags"] == ""


def test_shares_are_consistent_with_the_counts(rows):
    for row in rows:
        if row["share_over60"]:
            expected = float(row["people_over60"]) / float(row["population"])
            assert float(row["share_over60"]) == pytest.approx(expected, rel=0.01), row["h3"]


# --- D17: the finding is asserted, so it cannot quietly become untrue ---------------

def test_the_two_shares_are_still_perfectly_anticorrelated(rows):
    """D17 rests on this. If a future data release fixes it, this test fails and the
    decision gets revisited instead of silently outliving its evidence."""
    defined = [r for r in rows if r["share_over60"]]
    a = np.array([float(r["share_over60"]) for r in defined])
    b = np.array([float(r["share_under5"]) for r in defined])
    assert np.corrcoef(a, b)[0, 1] < -0.99, (
        "the age shares are no longer perfectly anti-correlated; revisit D17 and Q7"
    )


def test_the_combined_dependency_ratio_is_near_constant(rows):
    defined = [r for r in rows if r["share_over60"]]
    combined = np.array([float(r["share_over60"]) + float(r["share_under5"]) for r in defined])
    assert combined.std() / combined.mean() < 0.02, "revisit D17: the sum now varies"


def test_the_counts_do_vary_even_though_the_shares_do_not(rows):
    """D17's saving grace: D8's need definition uses counts, and those carry signal."""
    counts = np.array([float(r["people_over60"]) for r in rows])
    assert counts.std() / counts.mean() > 0.5, "age counts should vary with population"
