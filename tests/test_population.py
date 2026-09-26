"""P1-06: people per cell. Reads the committed CSVs, so it runs in CI."""

import csv
import json

import pytest


@pytest.fixture(scope="module")
def cells(root):
    path = root / "data" / "processed" / "population_cells.csv"
    assert path.exists(), "run `uv run python -m pipeline.population` first"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def comparison(root):
    with (root / "data" / "processed" / "population_source_comparison.csv").open(
            encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def population_cfg(root):
    import yaml
    return yaml.safe_load((root / "config" / "population.yaml").read_text(encoding="utf-8"))


def test_one_row_per_grid_cell(cells, root):
    grid = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    ids = [r["h3"] for r in cells]
    assert len(ids) == len(set(ids))
    assert set(ids) == {f["properties"]["h3"] for f in grid["features"]}


def test_population_is_never_negative(cells):
    for row in cells:
        assert float(row["population"]) >= 0, row["h3"]
        assert float(row["population_alt"]) >= 0, row["h3"]


def test_density_is_consistent_with_population(cells, root):
    """density = people / clipped area; a mismatch means one of them is stale."""
    grid = json.loads((root / "data" / "processed" / "grid.geojson").read_text("utf-8"))
    areas = {f["properties"]["h3"]: f["properties"]["clipped_area_km2"]
             for f in grid["features"]}
    for row in cells:
        expected = float(row["population"]) / areas[row["h3"]]
        assert float(row["density_per_km2"]) == pytest.approx(expected, rel=0.01), row["h3"]


def test_totals_are_plausible_for_a_dense_karachi_town(cells):
    total = sum(float(r["population"]) for r in cells)
    assert 100_000 < total < 1_500_000, f"Landhi total {total:,.0f} is not credible"


def test_both_sources_are_recorded_in_the_comparison(comparison, population_cfg):
    assert len(comparison) == 2
    names = {row["source"] for row in comparison}
    assert any("Meta" in n for n in names) and any("WorldPop" in n for n in names)
    for row in comparison:
        assert int(row["census_2023_landhi"]) == \
            population_cfg["independent_check"]["pilot"]["figure"]


def test_the_undercount_is_recorded_not_hidden(comparison):
    """D16: both sources fall far short of the census. If that ever stops being true,
    this test should fail so the finding gets revisited rather than silently outdated."""
    for row in comparison:
        ratio = float(row["ratio_to_census"])
        assert 0.0 < ratio < 1.0, f"{row['source']} now exceeds the census figure"
        assert ratio < 0.8, (
            f"{row['source']} is now {ratio:.2f} of the census figure; D16 and Q6 describe "
            "a roughly 0.44 ratio and should be revisited"
        )


def test_data_was_not_rescaled_to_match_the_census(cells, comparison, population_cfg):
    """PROMPT.md 2.1: never adjust data to hit an independent figure."""
    total = sum(float(r["population"]) for r in cells)
    census = population_cfg["independent_check"]["pilot"]["figure"]
    assert abs(total - census) / census > 0.2, (
        "the pilot total now matches the census suspiciously well; check nothing was scaled"
    )
    chosen = population_cfg["chosen"]
    expected = next(float(r["pilot_total"]) for r in comparison
                    if ("Meta" if chosen == "meta" else "WorldPop") in r["source"])
    assert total == pytest.approx(expected, rel=0.001), \
        "the per-cell table and the comparison table disagree about the chosen source"


def test_chosen_source_is_the_higher_resolution_one(comparison, population_cfg):
    """D16 chose on resolution; if the config flips, the reasoning must be revisited."""
    chosen = population_cfg["chosen"]
    resolutions = {("meta" if "Meta" in r["source"] else "worldpop"): int(r["resolution_m"])
                   for r in comparison}
    assert resolutions[chosen] == min(resolutions.values())


def test_some_cells_have_no_people(cells):
    """Landhi contains industrial estate; a model showing people everywhere would be wrong."""
    empty = [r for r in cells if float(r["population"]) == 0]
    assert empty, "no empty cells at all is implausible for a town with industrial land"
    assert len(empty) < len(cells) * 0.3, "too many empty cells; check the raster alignment"
