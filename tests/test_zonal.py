"""The shared zonal-statistics helper, on SYNTHETIC in-memory rasters.

These tests guard the rule every raster indicator depends on: statistics come from the
clipped cell, so a value measured outside the pilot boundary can never enter a cell.
"""

import numpy as np
import pytest
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box

from pipeline.zonal import cell_pixels, summarise

# SYNTHETIC raster: 10x10 pixels of 1 m, in a metre-based CRS, origin at (0, 10).
# Left half is 10.0, right half is 30.0, so the mean over the whole thing is 20.0.
PIXELS = np.zeros((10, 10), dtype="float32")
PIXELS[:, :5] = 10.0
PIXELS[:, 5:] = 30.0


@pytest.fixture
def raster():
    profile = {"driver": "GTiff", "height": 10, "width": 10, "count": 2,
               "dtype": "float32", "crs": "EPSG:32642",
               "transform": from_origin(0, 10, 1, 1), "nodata": float("nan")}
    with MemoryFile() as mem:
        with mem.open(**profile) as dst:
            dst.write(PIXELS, 1)
            dst.write(np.full((10, 10), 7.0, dtype="float32"), 2)
        with mem.open() as src:
            yield src


def to_4326(geom, src):
    """summarise() takes EPSG:4326 input, so hand it geometry it will transform back."""
    from rasterio.warp import transform_geom
    from shapely.geometry import mapping, shape
    return shape(transform_geom(src.crs, "EPSG:4326", mapping(geom)))


def test_reads_only_pixels_inside_the_polygon(raster):
    left_half = to_4326(box(0, 0, 5, 10), raster)
    values = cell_pixels(raster, left_half)
    assert values.size > 0
    assert set(np.unique(values)) == {10.0}, "a value from outside the polygon leaked in"


def test_mean_and_percentile(raster):
    whole = to_4326(box(0, 0, 10, 10), raster)
    stats = summarise(raster, whole, percentile=90)
    assert stats["mean"] == pytest.approx(20.0, abs=0.5)
    assert stats["percentile"] == pytest.approx(30.0, abs=0.5)
    assert stats["pixels"] == 100


def test_clipping_changes_the_answer(raster):
    """The whole point of D15: clipping must actually exclude outside values."""
    whole = summarise(raster, to_4326(box(0, 0, 10, 10), raster), percentile=90)
    clipped = summarise(raster, to_4326(box(0, 0, 5, 10), raster), percentile=90)
    assert clipped["mean"] == pytest.approx(10.0, abs=0.5)
    assert clipped["mean"] < whole["mean"], "clipping did not exclude the hotter half"


def test_coverage_is_reported(raster):
    stats = summarise(raster, to_4326(box(0, 0, 10, 10), raster), percentile=90)
    assert stats["coverage"] == pytest.approx(1.0, abs=0.05)


def test_a_polygon_smaller_than_a_pixel_falls_back_rather_than_vanishing(raster):
    tiny = to_4326(box(2.1, 2.1, 2.4, 2.4), raster)  # no pixel centre inside
    stats = summarise(raster, tiny, percentile=90)
    assert stats["pixels"] > 0, "a sub-pixel cell must not be reported as empty"
    assert stats["touched_fallback"] is True


def test_a_polygon_outside_the_raster_returns_no_value(raster):
    away = to_4326(box(500, 500, 510, 510), raster)
    stats = summarise(raster, away, percentile=90)
    assert stats["mean"] is None and stats["pixels"] == 0


def test_count_band_is_summarised_separately(raster):
    stats = summarise(raster, to_4326(box(0, 0, 10, 10), raster), percentile=90,
                      value_band=1, count_band=2)
    assert stats["clear_looks_median"] == pytest.approx(7.0)
