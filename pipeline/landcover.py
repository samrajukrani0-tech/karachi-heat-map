"""P1-08: built-up surface and green cover per cell, from ESA WorldCover 10 m.

Also measures OpenStreetMap's building coverage over the same area. That is a
cross-check, never the indicator: it quantifies how incomplete OSM is in Landhi, a
number P1-09 needs when it reports gaps in OSM health-facility coverage.

Run:
    uv run python -m pipeline.landcover
"""

from __future__ import annotations

import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import planetary_computer  # noqa: E402
import rasterio  # noqa: E402
from pyproj import Transformer  # noqa: E402
from pystac_client import Client  # noqa: E402
from rasterio.mask import mask as rio_mask  # noqa: E402
from rasterio.warp import transform_geom  # noqa: E402
from shapely.geometry import Polygon, mapping, shape  # noqa: E402
from shapely.ops import transform as shp_transform  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

from pipeline import overpass  # noqa: E402
from pipeline.config import ARTIFACTS, MEASUREMENT_CRS, PROCESSED, STORAGE_CRS, load  # noqa: E402
from pipeline.grid import clip  # noqa: E402

OUTPUT = PROCESSED / "landcover_cells.csv"
PREVIEW = ARTIFACTS / "landcover_cells_map.png"
_TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform


def worldcover_item(bbox: list[float], cfg: dict):
    catalogue = Client.open(cfg["source"]["stac_api"])
    items = list(catalogue.search(collections=[cfg["source"]["collection"]], bbox=bbox).items())
    if not items:
        raise SystemExit("no ESA WorldCover tile covers the pilot area")
    preferred = [i for i in items if cfg["source"]["prefer_version"] in i.id]
    item = (preferred or items)[0]
    print(f"  WorldCover tile: {item.id}")
    return planetary_computer.sign(item)


def class_fractions(src, geometry, green: set[int], built: set[int]) -> dict[str, float]:
    projected = shape(transform_geom(STORAGE_CRS, src.crs, mapping(geometry)))
    data, _ = rio_mask(src, [mapping(projected)], crop=True, filled=True, nodata=0, indexes=[1])
    values = data[0]
    values = values[values != 0]
    if values.size == 0:
        return {"green_fraction": 0.0, "built_fraction": 0.0, "pixels": 0}
    return {
        "green_fraction": float(np.isin(values, list(green)).mean()),
        "built_fraction": float(np.isin(values, list(built)).mean()),
        "pixels": int(values.size),
    }


def osm_building_union(bbox_4326) -> Polygon | None:
    """Building polygons from OSM, as one geometry, for the completeness cross-check."""
    south, west, north, east = bbox_4326[1], bbox_4326[0], bbox_4326[3], bbox_4326[2]
    query = (f'[out:json][timeout:300];(way["building"]({south},{west},{north},{east});'
             f'relation["building"]({south},{west},{north},{east}););out geom;')
    payload, _ = overpass.query(query, "landhi_buildings")
    polygons = []
    for element in payload.get("elements", []):
        if element.get("type") == "way" and "geometry" in element:
            points = [(p["lon"], p["lat"]) for p in element["geometry"]]
            if len(points) >= 4:
                polygons.append(Polygon(points).buffer(0))
        elif element.get("type") == "relation":
            for member in element.get("members", []):
                if member.get("role") == "outer" and "geometry" in member:
                    points = [(p["lon"], p["lat"]) for p in member["geometry"]]
                    if len(points) >= 4:
                        polygons.append(Polygon(points).buffer(0))
    polygons = [p for p in polygons if p.is_valid and not p.is_empty]
    print(f"  OSM building polygons in the pilot bbox: {len(polygons)}")
    return unary_union(polygons) if polygons else None


def build() -> dict[str, float]:
    cfg = load("landcover")
    boundary = shape(json.loads(
        (PROCESSED / "pilot_area.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"])
    grid = json.loads((PROCESSED / "grid.geojson").read_text(encoding="utf-8"))
    bbox = list(boundary.bounds)

    green = set(cfg["green_classes"])
    built = set(cfg["built_classes"])
    item = worldcover_item(bbox, cfg)

    osm = osm_building_union(bbox) if cfg["osm_crosscheck"]["enabled"] else None
    osm_utm = shp_transform(_TO_UTM, osm) if osm is not None else None

    rows = []
    with rasterio.open(item.assets[cfg["source"]["asset"]].href) as src:
        print(f"  raster crs {src.crs}, pixel {abs(src.transform.a) * 111320:.0f} m")
        for feature in grid["features"]:
            cell = feature["properties"]["h3"]
            clipped = clip(shape(feature["geometry"]), boundary)
            fractions = class_fractions(src, clipped, green, built)
            clipped_utm = shp_transform(_TO_UTM, clipped)
            osm_fraction = 0.0
            if osm_utm is not None and clipped_utm.area:
                osm_fraction = osm_utm.intersection(clipped_utm).area / clipped_utm.area
            rows.append({
                "h3": cell,
                "built_fraction": round(fractions["built_fraction"], 5),
                "green_fraction": round(fractions["green_fraction"], 5),
                "lack_green": round(1.0 - fractions["green_fraction"], 5),
                "osm_building_fraction": round(osm_fraction, 5),
                "landcover_pixels": fractions["pixels"],
            })

    built_values = [r["built_fraction"] for r in rows]
    green_values = [r["green_fraction"] for r in rows]
    osm_values = [r["osm_building_fraction"] for r in rows]
    print(f"\nCells: {len(rows)}; WorldCover pixels per cell median "
          f"{int(np.median([r['landcover_pixels'] for r in rows]))}")
    print(f"built_fraction: min {min(built_values):.3f}, median {np.median(built_values):.3f}, "
          f"max {max(built_values):.3f}")
    print(f"green_fraction: min {min(green_values):.3f}, median {np.median(green_values):.3f}, "
          f"max {max(green_values):.3f}")
    print(f"OSM building fraction: median {np.median(osm_values):.4f}, max {max(osm_values):.4f}")
    ratio = (np.mean(osm_values) / np.mean(built_values)) if np.mean(built_values) else 0.0
    print(f"OSM buildings cover {np.mean(osm_values) * 100:.2f}% of Landhi against "
          f"WorldCover built-up {np.mean(built_values) * 100:.1f}% -> OSM captures roughly "
          f"{ratio * 100:.0f}% as much area (completeness cross-check, not the indicator)")

    limits = cfg["plausibility"]
    if np.median(built_values) < limits["built_fraction_min_median"]:
        raise SystemExit(f"FAIL: median built fraction {np.median(built_values):.3f} is below "
                         f"the documented minimum {limits['built_fraction_min_median']}")
    if np.median(green_values) > limits["green_fraction_max_median"]:
        raise SystemExit(f"FAIL: median green fraction {np.median(green_values):.3f} exceeds "
                         f"the documented maximum {limits['green_fraction_max_median']}")

    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote data/processed/{OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} kB)")
    _map(grid, rows)
    return {"built_median": float(np.median(built_values)),
            "green_median": float(np.median(green_values)),
            "osm_ratio": float(ratio)}


def _map(grid: dict, rows: list[dict]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    by_cell = {r["h3"]: r for r in rows}
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=110)
    for ax, column, cmap, title in (
            (axes[0], "built_fraction", "copper_r", "Built-up surface fraction"),
            (axes[1], "green_fraction", "YlGn", "Green cover fraction")):
        values = [by_cell[f["properties"]["h3"]][column] for f in grid["features"]]
        norm = plt.Normalize(vmin=min(values), vmax=max(values))
        palette = plt.get_cmap(cmap)
        for feature in grid["features"]:
            x, y = shape(feature["geometry"]).exterior.xy
            ax.fill(x, y, facecolor=palette(norm(by_cell[feature["properties"]["h3"]][column])),
                    edgecolor="white", linewidth=0.2)
        ax.set_aspect("equal")
        ax.set_title(title)
        ax.set_xlabel("longitude")
        fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=palette), ax=ax, shrink=0.8)
    axes[0].set_ylabel("latitude")
    fig.suptitle("Landhi Town: ESA WorldCover 10 m (2021)")
    fig.tight_layout()
    fig.savefig(PREVIEW)
    plt.close(fig)
    print(f"Wrote {PREVIEW.name} to artifacts/")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
