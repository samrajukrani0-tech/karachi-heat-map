"""P1-08: built-up surface and green cover per cell."""

import csv
import json

import numpy as np
import pytest


@pytest.fixture(scope="module")
def rows(root):
    path = root / "data" / "processed" / "landcover_cells.csv"
    assert path.exists(), "run `uv run python -m pipeline.landcover` first"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def landcover_cfg(root):
    import yaml
    return yaml.safe_load((root / "config" / "landcover.yaml").read_text(encoding="utf-8"))


def test_one_row_per_grid_cell(rows, root):
    grid = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    ids = [r["h3"] for r in rows]
    assert len(ids) == len(set(ids))
    assert set(ids) == {f["properties"]["h3"] for f in grid["features"]}


def test_fractions_are_within_zero_and_one(rows):
    for row in rows:
        for column in ("built_fraction", "green_fraction", "lack_green",
                       "osm_building_fraction"):
            assert 0.0 <= float(row[column]) <= 1.0, f"{row['h3']} {column}"


def test_lack_green_is_the_complement_of_green(rows):
    for row in rows:
        assert float(row["lack_green"]) == pytest.approx(
            1.0 - float(row["green_fraction"]), abs=1e-6), row["h3"]


def test_classes_do_not_overlap(rows):
    """A pixel has exactly one WorldCover class, so the two fractions cannot both be high."""
    for row in rows:
        assert float(row["built_fraction"]) + float(row["green_fraction"]) <= 1.0 + 1e-6


def test_every_cell_rests_on_enough_pixels(rows):
    counts = [int(r["landcover_pixels"]) for r in rows]
    assert min(counts) > 0
    assert np.median(counts) > 200, "10 m data should give hundreds of pixels per cell"


def test_values_are_plausible_for_a_dense_town(rows, landcover_cfg):
    built = [float(r["built_fraction"]) for r in rows]
    green = [float(r["green_fraction"]) for r in rows]
    limits = landcover_cfg["plausibility"]
    assert np.median(built) >= limits["built_fraction_min_median"]
    assert np.median(green) <= limits["green_fraction_max_median"]


def test_there_is_real_variation(rows):
    built = np.array([float(r["built_fraction"]) for r in rows])
    assert built.max() - built.min() > 0.5, "built fraction barely varies; check the source"


def test_osm_is_recorded_as_badly_incomplete(rows):
    """D18: OSM covers a small fraction of Landhi's built area. P1-09's caveat rests on
    this number, so if OSM ever improves, this test should fail and the caveat be revisited."""
    osm = np.mean([float(r["osm_building_fraction"]) for r in rows])
    built = np.mean([float(r["built_fraction"]) for r in rows])
    assert osm < built * 0.5, (
        f"OSM now covers {osm / built:.0%} of the built area; revisit the completeness "
        "caveats in D18 and P1-09"
    )


def test_the_built_green_redundancy_is_still_present(rows):
    """Q8 rests on this correlation. If it changes, the question should be reopened."""
    built = np.array([float(r["built_fraction"]) for r in rows])
    green = np.array([float(r["green_fraction"]) for r in rows])
    assert np.corrcoef(built, green)[0, 1] < -0.8, "revisit Q8: built and green diverged"
