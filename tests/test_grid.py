"""P1-02: the H3 grid covering the pilot area.

Every assertion is recomputed from the stored geometry rather than read from the
file's own metadata, so a wrong number in the metadata fails the tests.
"""

import json

import h3
import pytest
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform, unary_union

from pipeline.config import MEASUREMENT_CRS, STORAGE_CRS
from pipeline.grid import MIN_COVERAGE, cell_centre, cell_polygon, clip

TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform
KARACHI_BBOX = (66.8, 24.6, 67.6, 25.2)


@pytest.fixture(scope="module")
def grid(root):
    path = root / "data" / "processed" / "grid.geojson"
    assert path.exists(), "run `uv run python -m pipeline.grid` first"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def boundary(root):
    doc = json.loads((root / "data" / "processed" / "pilot_area.geojson").read_text("utf-8"))
    return shape(doc["features"][0]["geometry"])


@pytest.fixture(scope="module")
def cell_ids(grid):
    return [f["properties"]["h3"] for f in grid["features"]]


def test_every_id_is_a_valid_h3_cell(cell_ids):
    invalid = [c for c in cell_ids if not h3.is_valid_cell(c)]
    assert invalid == []


def test_every_cell_is_at_the_decided_resolution(cell_ids, area):
    expected = area["grid"]["resolution"]
    wrong = [c for c in cell_ids if h3.get_resolution(c) != expected]
    assert wrong == [], f"{len(wrong)} cells are not resolution {expected}"


def test_no_duplicate_cells(cell_ids):
    assert len(cell_ids) == len(set(cell_ids))


def test_cell_count_is_inside_the_documented_range(cell_ids, area):
    assert area["grid"]["expected_cells_min"] <= len(cell_ids) <= area["grid"]["expected_cells_max"]


def test_stored_geometry_matches_the_h3_id(grid):
    """The polygon in the file must be the hexagon its id names, not an arbitrary shape."""
    for feature in grid["features"][:25]:
        stored = shape(feature["geometry"])
        expected = cell_polygon(feature["properties"]["h3"])
        assert stored.equals_exact(expected, 1e-9) or stored.symmetric_difference(
            expected).area < 1e-12, f"geometry does not match id {feature['properties']['h3']}"


def test_cells_cover_at_least_99_percent_of_the_boundary(grid, boundary):
    """P1-02 acceptance criterion, recomputed from geometry."""
    boundary_utm = transform(TO_UTM, boundary)
    covered = unary_union([transform(TO_UTM, shape(f["geometry"])) for f in grid["features"]])
    coverage = covered.intersection(boundary_utm).area / boundary_utm.area
    assert coverage >= MIN_COVERAGE, f"coverage is {coverage * 100:.3f}%"


def test_every_cell_satisfies_the_documented_inclusion_rule(grid, boundary, area):
    """Re-derive the rule independently; no cell may be in the grid without qualifying."""
    threshold = float(area["grid"]["min_area_fraction"])
    boundary_utm = transform(TO_UTM, boundary)
    for feature in grid["features"]:
        cell = feature["properties"]["h3"]
        poly_utm = transform(TO_UTM, cell_polygon(cell))
        fraction = poly_utm.intersection(boundary_utm).area / poly_utm.area
        qualifies = boundary.contains(cell_centre(cell)) or fraction >= threshold
        assert qualifies, f"{cell} is in the grid with only {fraction:.3f} inside"


def test_no_cell_lies_entirely_outside_the_pilot_area(grid, boundary):
    for feature in grid["features"]:
        assert not clip(shape(feature["geometry"]), boundary).is_empty


def test_clipped_area_is_recorded_and_never_exceeds_the_hexagon(grid, boundary):
    for feature in grid["features"]:
        props = feature["properties"]
        clipped = transform(TO_UTM, clip(shape(feature["geometry"]), boundary)).area / 1e6
        assert clipped == pytest.approx(props["clipped_area_km2"], abs=1e-5)
        assert 0 < props["clipped_area_km2"] <= props["area_km2"] + 1e-9


def test_geometry_is_valid_and_in_epsg_4326(grid):
    for feature in grid["features"]:
        geom = shape(feature["geometry"])
        assert geom.is_valid and not geom.is_empty
        lon_min, lat_min, lon_max, lat_max = geom.bounds
        assert KARACHI_BBOX[0] <= lon_min and lon_max <= KARACHI_BBOX[2]
        assert KARACHI_BBOX[1] <= lat_min and lat_max <= KARACHI_BBOX[3]


def test_metadata_is_honest(grid, cell_ids, area):
    meta = grid["metadata"]
    assert meta["cell_count"] == len(cell_ids)
    assert meta["h3_resolution"] == area["grid"]["resolution"]
    assert meta["min_area_fraction"] == area["grid"]["min_area_fraction"]
    assert meta["boundary_coverage"] >= MIN_COVERAGE
    assert "ODbL" in meta["licence"]
    assert meta["cells_by_centre"] + meta["cells_by_area_rule"] == meta["cell_count"]
    assert "clipped" in meta["indicators_use"]


def test_the_grid_is_contiguous(cell_ids):
    """A gap would mean part of Landhi has no cell. Walk the set through H3 neighbours."""
    remaining = set(cell_ids)
    stack = [next(iter(remaining))]
    seen = set()
    while stack:
        cell = stack.pop()
        if cell in seen:
            continue
        seen.add(cell)
        stack.extend(n for n in h3.grid_disk(cell, 1) if n in remaining and n not in seen)
    assert seen == remaining, f"{len(remaining - seen)} cells are disconnected from the grid"
