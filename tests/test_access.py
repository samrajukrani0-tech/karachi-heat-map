"""P1-09a: distance to the nearest health facility."""

import csv
import json

import numpy as np
import pytest


@pytest.fixture(scope="module")
def rows(root):
    path = root / "data" / "processed" / "access_cells.csv"
    assert path.exists(), "run `uv run python -m pipeline.access` first"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def facilities(root):
    with (root / "data" / "processed" / "health_facilities.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def access_cfg(root):
    import yaml
    return yaml.safe_load((root / "config" / "access.yaml").read_text(encoding="utf-8"))


def test_one_row_per_grid_cell(rows, root):
    grid = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    ids = [r["h3"] for r in rows]
    assert len(ids) == len(set(ids))
    assert set(ids) == {f["properties"]["h3"] for f in grid["features"]}


def test_distances_are_positive_and_plausible(rows, access_cfg):
    limits = access_cfg["plausibility"]
    values = [float(r["dist_health_m"]) for r in rows]
    assert min(values) > 0
    assert np.median(values) <= limits["max_median_m"]
    assert max(values) <= limits["max_any_m"]


def test_circuity_factor_is_applied_exactly(rows, access_cfg):
    """The reported distance must be the straight line times the documented factor -- not
    a different number that happens to look reasonable."""
    factor = access_cfg["distance"]["circuity_factor"]
    for row in rows:
        expected = float(row["dist_health_straight_m"]) * factor
        assert float(row["dist_health_m"]) == pytest.approx(expected, abs=0.2), row["h3"]


def test_circuity_factor_never_shortens_a_distance(access_cfg):
    assert access_cfg["distance"]["circuity_factor"] >= 1.0, (
        "a circuity factor below 1 would claim roads are shorter than straight lines"
    )


def test_facilities_outside_the_pilot_area_are_used(rows):
    """A clinic just over the boundary still serves the cells beside it. Ignoring those
    would inflate the distance for every edge cell."""
    outside = [r for r in rows if r["nearest_is_outside_pilot"] == "True"]
    assert outside, "no cell's nearest facility is outside Landhi; check the search buffer"


def test_every_cell_names_the_facility_it_was_measured_to(rows, facilities):
    known = {f["osm"] for f in facilities}
    for row in rows:
        assert row["nearest_facility_osm"] in known, row["h3"]


def test_facility_list_is_usable(facilities, access_cfg):
    assert len(facilities) > 20, "too few facilities for the indicator to mean anything"
    allowed = set(access_cfg["health_facilities"]["tags"])
    assert {f["amenity"] for f in facilities} <= allowed
    for facility in facilities:
        assert 24.6 <= float(facility["lat"]) <= 25.2
        assert 66.8 <= float(facility["lon"]) <= 67.6


def test_there_is_variation_to_rank(rows):
    values = [float(r["dist_health_m"]) for r in rows]
    assert max(values) - min(values) > 500, "distances barely vary; the indicator is flat"
