"""P1-04b: per-cell hot-season LST. Reads the committed CSV, so it runs in CI."""

import csv
import json

import pytest

KNOWN_FLAGS = {"no_pixels", "thin_pixel_coverage", "few_clear_looks", "all_touched_fallback"}


@pytest.fixture(scope="module")
def cells(root):
    path = root / "data" / "processed" / "lst_cells.csv"
    assert path.exists(), "run `uv run python -m pipeline.heat` first"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def grid_ids(root):
    doc = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    return {f["properties"]["h3"] for f in doc["features"]}


def test_one_row_per_grid_cell(cells, grid_ids):
    ids = [r["h3"] for r in cells]
    assert len(ids) == len(set(ids)), "duplicate cells"
    assert set(ids) == grid_ids, "the heat table and the grid disagree about which cells exist"


def test_every_cell_has_a_value(cells):
    missing = [r["h3"] for r in cells if not r["lst_mean_c"]]
    assert missing == [], f"{len(missing)} cells have no temperature"


def test_values_are_inside_the_plausible_range(cells, root):
    import yaml
    cfg = yaml.safe_load((root / "config" / "heat.yaml").read_text(encoding="utf-8"))
    low = cfg["plausible_range_celsius"]["min"]
    high = cfg["plausible_range_celsius"]["max"]
    for row in cells:
        assert low <= float(row["lst_mean_c"]) <= high, row["h3"]
        assert low <= float(row["lst_p90_c"]) <= high, row["h3"]


def test_p90_is_never_below_the_mean(cells):
    """A 90th percentile below the mean would mean the two were computed differently."""
    for row in cells:
        assert float(row["lst_p90_c"]) >= float(row["lst_mean_c"]), row["h3"]


def test_every_cell_rests_on_real_pixels(cells):
    for row in cells:
        assert int(row["pixels"]) > 0, row["h3"]
        assert 0.0 <= float(row["pixel_coverage"]) <= 1.0


def test_flags_are_from_the_known_set(cells):
    for row in cells:
        for flag in filter(None, row["flags"].split("|")):
            assert flag in KNOWN_FLAGS, f"unknown flag {flag!r}"


def test_the_flagging_rule_is_actually_applied(cells, root):
    """A cell below the configured thresholds must carry the flag, not hide it."""
    import yaml
    cfg = yaml.safe_load((root / "config" / "heat.yaml").read_text(encoding="utf-8"))["cells"]
    for row in cells:
        flags = row["flags"]
        if float(row["pixel_coverage"]) < cfg["min_pixel_coverage"]:
            assert "thin_pixel_coverage" in flags, f"{row['h3']} is thin but unflagged"
        if int(row["clear_looks_median"]) < cfg["min_clear_looks"]:
            assert "few_clear_looks" in flags, f"{row['h3']} has few looks but is unflagged"


def test_there_is_real_variation_between_cells(cells):
    """A hazard layer that is flat across the pilot area would carry no information."""
    means = [float(r["lst_mean_c"]) for r in cells]
    assert max(means) - min(means) >= 1.0, "less than 1 degC of spread across Landhi"


def test_percentile_column_matches_the_configured_percentile(cells, root):
    import yaml
    cfg = yaml.safe_load((root / "config" / "heat.yaml").read_text(encoding="utf-8"))
    assert f"lst_p{cfg['cells']['percentile']}_c" in cells[0]
