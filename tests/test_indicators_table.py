"""P1-11: the joined indicator table."""

import json

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def table(root):
    path = root / "data" / "processed" / "indicators.parquet"
    assert path.exists(), "run `uv run python -m pipeline.indicators` first"
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def grid_ids(root):
    doc = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    return {f["properties"]["h3"] for f in doc["features"]}


def test_one_row_per_grid_cell(table, grid_ids):
    assert len(table) == len(grid_ids)
    assert set(table["h3"]) == grid_ids
    assert table["h3"].is_unique


def test_parquet_and_csv_agree(root, table):
    csv = pd.read_csv(root / "data" / "processed" / "indicators.csv")
    assert len(csv) == len(table)
    assert list(csv.columns) == list(table.columns)
    pd.testing.assert_series_equal(
        csv["lst_mean_c"].astype(float).sort_values().reset_index(drop=True),
        table["lst_mean_c"].astype(float).sort_values().reset_index(drop=True),
        check_names=False)


def test_every_configured_indicator_has_a_column(table, root):
    import yaml
    cfg = yaml.safe_load((root / "config" / "indicators.yaml").read_text(encoding="utf-8"))
    mapping = {"lst_day_mean": "lst_mean_c", "population": "population",
               "lack_green": "lack_green", "dist_health": "dist_health_m",
               "dist_centre": "dist_centre_m"}
    for indicator in cfg["indicators"]:
        column = mapping[indicator["id"]]
        assert column in table.columns, f"{indicator['id']} has no column"


def test_available_indicators_have_no_missing_values(table):
    for column in ("lst_mean_c", "population", "lack_green", "dist_health_m"):
        assert table[column].isna().sum() == 0, f"{column} has gaps"


def test_the_blocked_indicator_is_empty_and_declared(table, root):
    """dist_centre_m must be empty while P1-09b is blocked -- and the gap must be written
    down, not silently left as a column of nulls nobody mentions."""
    assert table["dist_centre_m"].isna().all(), (
        "dist_centre_m has values; if P1-09b is unblocked, update the data dictionary"
    )
    dictionary = (root / "docs" / "data-dictionary.md").read_text(encoding="utf-8")
    assert "dist_centre_m" in dictionary
    assert "P1-09b" in dictionary and "Q2" in dictionary


def test_values_match_their_source_layers(root, table):
    """The join must not reorder or mismatch rows."""
    for filename, column in (("lst_cells.csv", "lst_mean_c"),
                             ("population_cells.csv", "population"),
                             ("landcover_cells.csv", "lack_green"),
                             ("access_cells.csv", "dist_health_m")):
        source = pd.read_csv(root / "data" / "processed" / filename).set_index("h3")
        joined = table.set_index("h3")
        merged = joined[[column]].join(source[[column]], rsuffix="_src")
        assert (merged[column].astype(float)
                - merged[f"{column}_src"].astype(float)).abs().max() < 1e-6, filename


def test_data_dictionary_documents_every_column(root, table):
    dictionary = (root / "docs" / "data-dictionary.md").read_text(encoding="utf-8")
    for column in table.columns:
        assert f"`{column}`" in dictionary, f"{column} is not in the data dictionary"


def test_data_dictionary_states_the_known_biases(root):
    """A reader must not have to dig through DECISIONS.md to learn the numbers are biased."""
    dictionary = (root / "docs" / "data-dictionary.md").read_text(encoding="utf-8")
    for phrase in ("not air temperature", "undercounts", "overstates", "D16", "D17", "D20"):
        assert phrase in dictionary, f"the data dictionary omits {phrase!r}"


def test_processed_data_stays_inside_the_size_budget(root):
    total = sum(p.stat().st_size for p in (root / "data" / "processed").rglob("*")
                if p.is_file())
    assert total < 5 * 1024 * 1024, f"data/processed is {total / 1e6:.1f} MB, over budget"


def test_keys_are_sane(table):
    assert (table["clipped_area_km2"] > 0).all()
    assert ((table["inside_fraction"] > 0) & (table["inside_fraction"] <= 1.0)).all()
