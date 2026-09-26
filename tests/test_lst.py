"""P1-04a: the hot-season LST composite.

Unit tests use SYNTHETIC arrays and always run. Tests that open the composite GeoTIFF
are marked `raw`: the file is gitignored and rebuildable, so CI skips them.
"""

import csv

import numpy as np
import pytest

from pipeline.lst import COMPOSITE, SCENES_CSV, qa_mask


@pytest.fixture(scope="module")
def heat(root):
    import yaml
    return yaml.safe_load((root / "config" / "heat.yaml").read_text(encoding="utf-8"))


# --- the QA bit mask (SYNTHETIC arrays) --------------------------------------------

def test_clear_pixels_are_kept(heat):
    qa = np.array([[0b0000_0000_0000_0000]], dtype="uint16")
    assert not qa_mask(qa, heat["qa_mask_bits"]).any()


@pytest.mark.parametrize("bit,name", [(0, "fill"), (1, "dilated_cloud"), (2, "cirrus"),
                                      (3, "cloud"), (4, "cloud_shadow")])
def test_each_masked_bit_is_rejected(heat, bit, name):
    assert heat["qa_mask_bits"][bit] == name, "config and Landsat's bit order disagree"
    qa = np.array([[1 << bit]], dtype="uint16")
    assert qa_mask(qa, heat["qa_mask_bits"]).all(), f"bit {bit} ({name}) was not masked"


def test_unlisted_bits_do_not_mask(heat):
    """Bits 6+ carry confidence levels, not defects; masking them would discard good data."""
    qa = np.array([[1 << 6 | 1 << 7 | 1 << 9]], dtype="uint16")
    assert not qa_mask(qa, heat["qa_mask_bits"]).any()


def test_mask_shape_is_preserved(heat):
    qa = np.zeros((4, 7), dtype="uint16")
    qa[2, 3] = 1 << 3
    mask = qa_mask(qa, heat["qa_mask_bits"])
    assert mask.shape == (4, 7)
    assert mask.sum() == 1 and mask[2, 3]


# --- the documented USGS scaling ---------------------------------------------------

def test_scaling_constants_match_usgs(heat):
    assert heat["scale"]["gain"] == 0.00341802
    assert heat["scale"]["offset"] == 149.0
    assert heat["scale"]["kelvin_to_celsius"] == -273.15


def test_scaling_converts_a_known_dn(heat):
    gain, offset = heat["scale"]["gain"], heat["scale"]["offset"]
    kelvin = 44000 * gain + offset
    assert kelvin == pytest.approx(299.393, abs=0.001)
    assert kelvin + heat["scale"]["kelvin_to_celsius"] == pytest.approx(26.243, abs=0.001)


# --- the recorded scene list (committed, so this runs in CI) ------------------------

@pytest.fixture(scope="module")
def scenes(root):
    path = root / SCENES_CSV.name if False else SCENES_CSV
    assert path.exists(), "run `uv run python -m pipeline.lst` first"
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_scene_list_has_the_required_columns(scenes):
    for field in ("scene_id", "datetime", "platform", "scene_cloud_cover",
                  "usable_pixel_fraction", "used"):
        assert field in scenes[0], f"missing column {field}"


def test_every_scene_is_in_the_configured_season(scenes, heat):
    months = set(heat["season"]["months"])
    first, last = heat["season"]["first_year"], heat["season"]["last_year"]
    for row in scenes:
        year, month = int(row["datetime"][:4]), int(row["datetime"][5:7])
        assert month in months, f"{row['scene_id']} is from month {month}"
        assert first <= year <= last, f"{row['scene_id']} is from {year}"


def test_every_scene_respects_the_cloud_limit(scenes, heat):
    for row in scenes:
        assert float(row["scene_cloud_cover"]) <= heat["max_scene_cloud_cover"]


def test_scenes_come_from_the_configured_platforms(scenes, heat):
    allowed = set(heat["source"]["platforms"])
    assert {row["platform"] for row in scenes} <= allowed


def test_usable_fraction_is_a_fraction(scenes):
    for row in scenes:
        assert 0.0 <= float(row["usable_pixel_fraction"]) <= 1.0


def test_enough_scenes_to_make_a_median_meaningful(scenes, heat):
    used = [r for r in scenes if r["used"] == "True"]
    assert len(used) >= heat["composite"]["min_valid_scenes_per_pixel"], (
        "fewer usable scenes than the minimum clear looks the composite requires"
    )


# --- the composite raster (gitignored; local only) ----------------------------------

@pytest.mark.raw
def test_composite_exists_and_is_two_banded():
    import rasterio
    assert COMPOSITE.exists(), "run `uv run python -m pipeline.lst` first"
    with rasterio.open(COMPOSITE) as src:
        assert src.count == 2
        assert src.dtypes[0] == "float32"
        assert src.descriptions[0].startswith("hot-season median LST")


@pytest.mark.raw
def test_composite_values_are_inside_the_plausible_range(heat):
    import rasterio
    with rasterio.open(COMPOSITE) as src:
        band = src.read(1)
    finite = band[np.isfinite(band)]
    assert finite.size > 0
    assert finite.min() >= heat["plausible_range_celsius"]["min"]
    assert finite.max() <= heat["plausible_range_celsius"]["max"]


@pytest.mark.raw
def test_every_pixel_has_enough_clear_looks(heat):
    import rasterio
    with rasterio.open(COMPOSITE) as src:
        lst, looks = src.read(1), src.read(2)
    kept = np.isfinite(lst)
    assert (looks[kept] >= heat["composite"]["min_valid_scenes_per_pixel"]).all()


@pytest.mark.raw
def test_composite_is_projected_in_metres():
    """Zonal statistics later assume a metre-based CRS, not degrees."""
    import rasterio
    with rasterio.open(COMPOSITE) as src:
        assert src.crs.linear_units == "metre"
        assert abs(src.transform.a - 30.0) < 0.001, "expected 30 m pixels"
