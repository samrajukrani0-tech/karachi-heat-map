"""P1-04a: hot-season daytime land surface temperature composite.

Searches Landsat 8/9 Collection 2 Level-2 for April-June scenes over the pilot area,
reads only the window covering Landhi from each cloud-optimised GeoTIFF, masks cloud
and shadow with QA_PIXEL, converts to degrees Celsius with the documented USGS scaling,
and takes a per-pixel median across scenes.

Run:
    uv run python -m pipeline.lst [--refresh]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from typing import Any

import numpy as np
import planetary_computer
import rasterio
from pystac_client import Client
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from shapely.geometry import shape

from pipeline.config import PROCESSED, RAW, STORAGE_CRS, load

COMPOSITE = RAW / "derived" / "lst_hot_season.tif"
SCENES_CSV = PROCESSED / "lst_scenes.csv"
BOUNDARY = PROCESSED / "pilot_area.geojson"

# Reading a COG window over HTTP: do not list the container, do not fetch the whole file.
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_MULTIPLEX", "YES")
os.environ.setdefault("VSI_CACHE", "TRUE")


def load_boundary():
    doc = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    return shape(doc["features"][0]["geometry"])


def search_scenes(cfg: dict[str, Any], bbox: list[float]) -> list:
    season = cfg["season"]
    catalogue = Client.open(cfg["source"]["stac_api"])
    search = catalogue.search(
        collections=[cfg["source"]["collection"]],
        bbox=bbox,
        datetime=f"{season['first_year']}-01-01/{season['last_year']}-12-31",
    )
    wanted_months = set(season["months"])
    platforms = set(cfg["source"]["platforms"])
    limit = cfg["max_scene_cloud_cover"]
    scenes = [
        item for item in search.items()
        if item.datetime.month in wanted_months
        and item.properties.get("platform") in platforms
        and item.properties.get("eo:cloud_cover", 100) <= limit
    ]
    scenes.sort(key=lambda i: i.datetime)
    return scenes


def qa_mask(qa: np.ndarray, bits: dict[int, str]) -> np.ndarray:
    """True where the pixel is unusable (fill, cloud, shadow, cirrus, dilated cloud)."""
    bad = np.zeros(qa.shape, dtype=bool)
    for bit in bits:
        bad |= (qa & (1 << int(bit))) != 0
    return bad


def _read_window(href: str, bounds_4326: tuple[float, float, float, float]):
    """Read only the pixels covering the pilot area, in the scene's own CRS."""
    with rasterio.open(href) as src:
        left, bottom, right, top = transform_bounds(STORAGE_CRS, src.crs, *bounds_4326)
        window = from_bounds(left, bottom, right, top, src.transform).round_offsets()
        window = window.round_lengths()
        data = src.read(1, window=window)
        return data, src.window_transform(window), src.crs


def build(*, refresh: bool = False) -> dict[str, Any]:
    cfg = load("heat")
    boundary = load_boundary()
    # A small pad so the grid's edge cells are fully covered by the raster.
    pad = 0.005
    minx, miny, maxx, maxy = boundary.bounds
    bounds = (minx - pad, miny - pad, maxx + pad, maxy + pad)

    scenes = search_scenes(cfg, list(bounds))
    print(f"Scenes: {len(scenes)} April-June {cfg['season']['first_year']}-"
          f"{cfg['season']['last_year']}, cloud cover <= {cfg['max_scene_cloud_cover']}%")
    if not scenes:
        raise SystemExit("no scenes matched; check config/heat.yaml and the STAC API")

    gain = cfg["scale"]["gain"]
    offset = cfg["scale"]["offset"]
    to_celsius = cfg["scale"]["kelvin_to_celsius"]
    bits = cfg["qa_mask_bits"]

    layers: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []
    transform = crs = None

    for index, item in enumerate(scenes, start=1):
        signed = planetary_computer.sign(item)
        try:
            lwir, tform, scene_crs = _read_window(
                signed.assets[cfg["source"]["temperature_asset"]].href, bounds)
            qa, _, _ = _read_window(signed.assets[cfg["source"]["qa_asset"]].href, bounds)
        except Exception as exc:  # a single unreadable scene must not lose the rest
            print(f"  [{index:>2}/{len(scenes)}] {item.id}: SKIPPED ({type(exc).__name__}: {exc})")
            rows.append({"scene_id": item.id, "datetime": item.datetime.isoformat(),
                         "platform": item.properties.get("platform", ""),
                         "scene_cloud_cover": item.properties.get("eo:cloud_cover", ""),
                         "usable_pixel_fraction": 0.0, "used": False,
                         "note": f"read failed: {type(exc).__name__}"})
            continue

        if transform is None:
            transform, crs = tform, scene_crs
        bad = qa_mask(qa, bits) | (lwir == 0)
        kelvin = np.where(bad, np.nan, lwir.astype("float32") * gain + offset)
        celsius = kelvin + to_celsius
        usable = float(np.isfinite(celsius).mean())
        layers.append(celsius)
        rows.append({
            "scene_id": item.id,
            "datetime": item.datetime.isoformat(),
            "platform": item.properties.get("platform", ""),
            "scene_cloud_cover": item.properties.get("eo:cloud_cover", ""),
            "usable_pixel_fraction": round(usable, 4),
            "used": True,
            "note": "",
        })
        print(f"  [{index:>2}/{len(scenes)}] {item.id}  "
              f"scene cloud {item.properties.get('eo:cloud_cover', 0):>5.1f}%  "
              f"usable over Landhi {usable * 100:>5.1f}%")

    if not layers:
        raise SystemExit("every scene failed to read; nothing to composite")

    stack = np.stack(layers)
    valid_counts = np.isfinite(stack).sum(axis=0)
    with np.errstate(all="ignore"):
        composite = np.nanmedian(stack, axis=0)
    thin = valid_counts < cfg["composite"]["min_valid_scenes_per_pixel"]
    composite = np.where(thin, np.nan, composite).astype("float32")

    finite = composite[np.isfinite(composite)]
    print(f"\nComposite: {composite.shape[1]} x {composite.shape[0]} pixels at 30 m")
    print(f"  clear looks per pixel: min {int(valid_counts.min())}, "
          f"median {int(np.median(valid_counts))}, max {int(valid_counts.max())}")
    print(f"  pixels dropped for fewer than {cfg['composite']['min_valid_scenes_per_pixel']} "
          f"clear looks: {int(thin.sum())} of {thin.size}")
    print(f"  LST degC: min {finite.min():.2f}, median {np.median(finite):.2f}, "
          f"max {finite.max():.2f}")

    low = cfg["plausible_range_celsius"]["min"]
    high = cfg["plausible_range_celsius"]["max"]
    if finite.min() < low or finite.max() > high:
        raise SystemExit(
            f"FAIL: composite spans {finite.min():.2f} to {finite.max():.2f} degC, outside the "
            f"documented plausible range {low}-{high}. Check the scaling before publishing."
        )

    COMPOSITE.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "height": composite.shape[0], "width": composite.shape[1],
        "count": 2, "dtype": "float32", "crs": crs, "transform": transform,
        "nodata": float("nan"), "compress": "deflate", "tiled": True,
    }
    with rasterio.open(COMPOSITE, "w", **profile) as dst:
        dst.write(composite, 1)
        dst.write(valid_counts.astype("float32"), 2)
        dst.set_band_description(1, "hot-season median LST, degrees Celsius")
        dst.set_band_description(2, "number of clear looks contributing to the median")
        dst.update_tags(
            feature="P1-04a",
            season=f"months {cfg['season']['months']}, "
                   f"{cfg['season']['first_year']}-{cfg['season']['last_year']}",
            scenes_used=str(sum(1 for r in rows if r["used"])),
            scaling=f"kelvin = {gain} * DN + {offset}",
            source="Landsat 8/9 Collection 2 Level-2 via Microsoft Planetary Computer",
            licence="USGS Landsat data: public domain; no restrictions on use",
            generated=dt.date.today().isoformat(),
        )

    import csv
    with SCENES_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {COMPOSITE.relative_to(RAW.parent.parent)} "
          f"({COMPOSITE.stat().st_size / 1024:.0f} kB, gitignored, rebuildable)")
    print(f"Wrote data/processed/{SCENES_CSV.name} ({len(rows)} scenes)")

    return {"scenes": len(rows), "used": sum(1 for r in rows if r["used"]),
            "min": float(finite.min()), "max": float(finite.max()),
            "median": float(np.median(finite))}


def main() -> int:
    parser = argparse.ArgumentParser(description="Hot-season LST composite (P1-04a)")
    parser.add_argument("--refresh", action="store_true")
    parser.parse_args()
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
