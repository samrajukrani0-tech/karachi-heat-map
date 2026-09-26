"""Zonal statistics over the analysis grid.

Shared by every raster indicator (P1-04b, P1-06, P1-08). Two rules are enforced here
once, rather than being re-implemented and re-forgotten in each feature:

1. Statistics are computed over the **clipped** cell (cell interesect pilot boundary),
   never the whole hexagon, so no cell can report a neighbouring town's values (D15).
2. A cell resting on too few pixels is reported as such rather than silently averaged.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.warp import transform_geom
from shapely.geometry import mapping, shape

from pipeline.config import STORAGE_CRS


def cell_pixels(src: rasterio.DatasetReader, geometry, band: int = 1,
                all_touched: bool = False) -> np.ndarray:
    """Finite pixel values of `band` inside `geometry` (given in EPSG:4326)."""
    projected = shape(transform_geom(STORAGE_CRS, src.crs, mapping(geometry)))
    try:
        data, _ = rio_mask(src, [mapping(projected)], crop=True, filled=True,
                           nodata=float("nan"), indexes=[band], all_touched=all_touched)
    except ValueError:
        return np.array([], dtype="float32")
    values = data[0].astype("float32")
    return values[np.isfinite(values)]


def summarise(src: rasterio.DatasetReader, geometry, *, percentile: int,
              value_band: int = 1, count_band: int | None = None,
              pixel_area_m2: float | None = None) -> dict[str, Any]:
    """Mean, percentile and coverage for one cell.

    Falls back to `all_touched=True` for a cell too small to contain a pixel centre,
    and says so in `touched_fallback` rather than reporting an empty cell as missing.
    """
    values = cell_pixels(src, geometry, band=value_band)
    fallback = False
    if values.size == 0:
        values = cell_pixels(src, geometry, band=value_band, all_touched=True)
        fallback = values.size > 0

    if values.size == 0:
        return {"mean": None, "percentile": None, "pixels": 0, "coverage": 0.0,
                "clear_looks_median": None, "touched_fallback": False}

    if pixel_area_m2 is None:
        pixel_area_m2 = abs(src.transform.a * src.transform.e)
    projected = shape(transform_geom(STORAGE_CRS, src.crs, mapping(geometry)))
    coverage = (values.size * pixel_area_m2) / projected.area if projected.area else 0.0

    looks = None
    if count_band is not None:
        counts = cell_pixels(src, geometry, band=count_band, all_touched=fallback)
        if counts.size:
            looks = float(np.median(counts))

    return {
        "mean": float(values.mean()),
        "percentile": float(np.percentile(values, percentile)),
        "pixels": int(values.size),
        "coverage": float(min(coverage, 1.0)),
        "clear_looks_median": looks,
        "touched_fallback": fallback,
    }


def sum_by_cell(src: rasterio.DatasetReader, cells: list[tuple[str, Any]],
                band: int = 1) -> tuple[dict[str, float], dict[str, int], float]:
    """Sum a count raster per cell, assigning every pixel to exactly one cell.

    Masking each cell separately and summing would double-count any pixel straddling a
    shared edge, so totals would not conserve. Rasterising the cells instead gives each
    pixel one owner, decided by its centre.

    Returns (sums by cell id, pixel counts by cell id, total over all cells).
    """
    from rasterio.features import rasterize
    from rasterio.mask import mask as rio_mask
    from rasterio.warp import transform_geom

    shapes = [shape(transform_geom(STORAGE_CRS, src.crs, mapping(geom)))
              for _, geom in cells]
    union = shapes[0]
    for extra in shapes[1:]:
        union = union.union(extra)
    window_data, window_transform = rio_mask(src, [mapping(union)], crop=True,
                                             filled=True, nodata=np.nan, indexes=[band])
    values = window_data[0].astype("float64")
    values[~np.isfinite(values)] = 0.0

    labels = rasterize(
        ((mapping(geom), index) for index, geom in enumerate(shapes, start=1)),
        out_shape=values.shape, transform=window_transform, fill=0, dtype="int32",
    )
    sums = np.bincount(labels.ravel(), weights=values.ravel(),
                       minlength=len(shapes) + 1)
    counts = np.bincount(labels.ravel(), minlength=len(shapes) + 1)
    by_id = {cell_id: float(sums[index])
             for index, (cell_id, _) in enumerate(cells, start=1)}
    pixels = {cell_id: int(counts[index])
              for index, (cell_id, _) in enumerate(cells, start=1)}
    return by_id, pixels, float(values.sum())
