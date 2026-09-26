"""P1-01: the pilot boundary and the code that assembles it.

These tests read the committed GeoJSON, so they need no network and run in CI.
"""

import json

import pytest
from shapely.geometry import shape

from pipeline.boundary import area_km2, relation_to_polygon

KARACHI_BBOX = (66.8, 24.6, 67.6, 25.2)  # lon_min, lat_min, lon_max, lat_max


@pytest.fixture(scope="module")
def feature(root):
    path = root / "data" / "processed" / "pilot_area.geojson"
    assert path.exists(), "run `uv run python -m pipeline.boundary` first"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["type"] == "FeatureCollection"
    assert len(doc["features"]) == 1, "the pilot area is exactly one feature"
    return doc["features"][0]


def test_geometry_is_a_valid_polygon(feature):
    geom = shape(feature["geometry"])
    assert geom.geom_type in {"Polygon", "MultiPolygon"}
    assert geom.is_valid, "boundary self-intersects"
    assert not geom.is_empty


def test_stored_in_epsg_4326(feature):
    """Degrees, not metres: a projected boundary would fall far outside this box."""
    lon_min, lat_min, lon_max, lat_max = shape(feature["geometry"]).bounds
    assert KARACHI_BBOX[0] <= lon_min and lon_max <= KARACHI_BBOX[2]
    assert KARACHI_BBOX[1] <= lat_min and lat_max <= KARACHI_BBOX[3]


def test_area_matches_config_and_recomputes(feature, area):
    """Recompute from the stored geometry rather than trusting the stored number."""
    recomputed = area_km2(shape(feature["geometry"]))
    expected = float(area["pilot"]["area_km2_expected"])
    tolerance = float(area["pilot"]["area_km2_tolerance"])
    assert abs(recomputed - expected) <= tolerance, (
        f"boundary is {recomputed:.3f} km2, config expects {expected} +/- {tolerance}"
    )
    assert abs(recomputed - feature["properties"]["area_km2"]) < 0.001, (
        "the area recorded in the file disagrees with the geometry it describes"
    )


def test_provenance_is_complete(feature, area):
    """PROMPT.md section 2.1: no output without a traceable source."""
    props = feature["properties"]
    for field in ("osm_relation", "source", "source_url", "licence", "accessed",
                  "raw_response_sha256", "generated_by"):
        assert str(props.get(field, "")).strip(), f"missing provenance: {field}"
    assert props["osm_relation"] == area["pilot"]["source"]["osm_relation"]
    assert len(props["raw_response_sha256"]) == 64
    assert props["area_measured_in"] == "EPSG:32642"


def test_licence_is_odbl(feature):
    """D10: OSM-derived output carries ODbL and credits contributors."""
    licence = feature["properties"]["licence"]
    assert "ODbL" in licence
    assert "OpenStreetMap" in licence


def test_matches_the_decided_pilot_area(feature, area):
    """D2 chose Landhi Town. A different relation here means the decision moved."""
    assert feature["properties"]["name_en"] == area["pilot"]["name_en"] == "Landhi Town"


# --- unit tests for the assembly logic -------------------------------------------
# SYNTHETIC fixtures: hand-made squares, not real data. They never reach the site.

def _way(coords, role="outer"):
    return {"type": "way", "role": role,
            "geometry": [{"lon": x, "lat": y} for x, y in coords]}


SYNTHETIC_SQUARE = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
SYNTHETIC_HOLE = [(0.4, 0.4), (0.4, 0.6), (0.6, 0.6), (0.6, 0.4), (0.4, 0.4)]


def test_assembles_a_simple_ring():
    payload = {"elements": [{"members": [_way(SYNTHETIC_SQUARE)]}]}
    assert relation_to_polygon(payload).area == pytest.approx(1.0)


def test_blank_role_counts_as_outer():
    """OSM leaves the role empty on single-ring boundaries."""
    payload = {"elements": [{"members": [_way(SYNTHETIC_SQUARE, role="")]}]}
    assert relation_to_polygon(payload).area == pytest.approx(1.0)


def test_inner_rings_are_subtracted():
    """Landhi has no holes, so only a synthetic case exercises this branch."""
    payload = {"elements": [{"members": [_way(SYNTHETIC_SQUARE),
                                         _way(SYNTHETIC_HOLE, role="inner")]}]}
    geom = relation_to_polygon(payload)
    assert geom.area == pytest.approx(1.0 - 0.04)
    assert len(geom.interiors) == 1


def test_empty_relation_raises():
    with pytest.raises(ValueError):
        relation_to_polygon({"elements": []})


def test_unclosed_ways_raise_rather_than_guess():
    payload = {"elements": [{"members": [_way([(0.0, 0.0), (1.0, 1.0)])]}]}
    with pytest.raises(ValueError):
        relation_to_polygon(payload)
