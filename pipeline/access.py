"""P1-09a: distance from each cell to the nearest health facility.

Distances are straight-line in EPSG:32642 multiplied by a documented circuity factor,
measured from the centroid of the clipped cell. Facilities outside the pilot boundary
are included, because a clinic just over the line still serves the cells beside it.

Run:
    uv run python -m pipeline.access
"""

from __future__ import annotations

import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import Point, shape  # noqa: E402
from shapely.ops import transform as shp_transform  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

from pipeline import overpass  # noqa: E402
from pipeline.config import ARTIFACTS, MEASUREMENT_CRS, PROCESSED, STORAGE_CRS, load  # noqa: E402
from pipeline.grid import clip  # noqa: E402

OUTPUT = PROCESSED / "access_cells.csv"
FACILITIES = PROCESSED / "health_facilities.csv"
PREVIEW = ARTIFACTS / "access_cells_map.png"
_TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform


def fetch_facilities(bounds, buffer_km: float, tags: list[str]) -> list[dict]:
    """Health facilities within a buffer of the pilot area, from OpenStreetMap."""
    degrees = buffer_km / 111.0
    south, west = bounds[1] - degrees, bounds[0] - degrees
    north, east = bounds[3] + degrees, bounds[2] + degrees
    pattern = "|".join(tags)
    query = (f'[out:json][timeout:300];'
             f'(nwr["amenity"~"^({pattern})$"]({south},{west},{north},{east}););'
             f'out center tags;')
    payload, _ = overpass.query(query, f"health_facilities_buffer{int(buffer_km)}km")

    facilities = []
    for element in payload.get("elements", []):
        tag_set = element.get("tags", {})
        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        facilities.append({
            "name": tag_set.get("name", "(unnamed)"),
            "amenity": tag_set.get("amenity", ""),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "osm": f"{element['type']}/{element['id']}",
        })
    return facilities


def build() -> dict[str, float]:
    cfg = load("access")
    health = cfg["health_facilities"]
    dist_cfg = cfg["distance"]

    boundary = shape(json.loads(
        (PROCESSED / "pilot_area.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"])
    grid = json.loads((PROCESSED / "grid.geojson").read_text(encoding="utf-8"))

    facilities = fetch_facilities(boundary.bounds, health["search_buffer_km"], health["tags"])
    inside = sum(1 for f in facilities if boundary.contains(Point(f["lon"], f["lat"])))
    print(f"  health facilities found: {len(facilities)} within "
          f"{health['search_buffer_km']} km of the pilot area "
          f"({inside} inside Landhi, {len(facilities) - inside} outside but still serving it)")
    if not facilities:
        raise SystemExit("no health facilities found; the indicator cannot be computed")

    points = [shp_transform(_TO_UTM, Point(f["lon"], f["lat"])) for f in facilities]
    tree = STRtree(points)
    factor = float(dist_cfg["circuity_factor"])

    rows = []
    for feature in grid["features"]:
        clipped = clip(shape(feature["geometry"]), boundary)
        centroid = shp_transform(_TO_UTM, clipped.centroid)
        index = tree.nearest(centroid)
        straight = centroid.distance(points[index])
        rows.append({
            "h3": feature["properties"]["h3"],
            "dist_health_m": round(straight * factor, 1),
            "dist_health_straight_m": round(straight, 1),
            "nearest_facility": facilities[index]["name"],
            "nearest_facility_osm": facilities[index]["osm"],
            "nearest_is_outside_pilot": not boundary.contains(
                Point(facilities[index]["lon"], facilities[index]["lat"])),
        })

    distances = [r["dist_health_m"] for r in rows]
    outside = sum(1 for r in rows if r["nearest_is_outside_pilot"])
    print(f"  distance to care (straight line x {factor}): min {min(distances):,.0f} m, "
          f"median {np.median(distances):,.0f} m, max {max(distances):,.0f} m")
    print(f"  cells whose nearest facility lies outside Landhi: {outside} of {len(rows)} "
          f"-- these would have been scored far from care without the search buffer")

    limits = cfg["plausibility"]
    if np.median(distances) > limits["max_median_m"]:
        raise SystemExit(f"FAIL: median distance {np.median(distances):,.0f} m exceeds the "
                         f"documented maximum {limits['max_median_m']:,} m")
    if max(distances) > limits["max_any_m"]:
        raise SystemExit(f"FAIL: maximum distance {max(distances):,.0f} m exceeds the "
                         f"documented maximum {limits['max_any_m']:,} m")

    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with FACILITIES.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(facilities[0]))
        writer.writeheader()
        writer.writerows(facilities)
    print(f"Wrote data/processed/{OUTPUT.name} and {FACILITIES.name}")

    _map(grid, rows, facilities, boundary)
    return {"facilities": len(facilities), "median_m": float(np.median(distances)),
            "max_m": max(distances), "nearest_outside": outside}


def _map(grid, rows, facilities, boundary) -> None:
    by_cell = {r["h3"]: r for r in rows}
    values = [r["dist_health_m"] for r in rows]
    norm = plt.Normalize(vmin=min(values), vmax=max(values))
    cmap = plt.get_cmap("magma_r")
    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=110)
    for feature in grid["features"]:
        x, y = shape(feature["geometry"]).exterior.xy
        ax.fill(x, y, facecolor=cmap(norm(by_cell[feature["properties"]["h3"]]["dist_health_m"])),
                edgecolor="white", linewidth=0.2, zorder=2)
    minx, miny, maxx, maxy = boundary.bounds
    near = [f for f in facilities
            if minx - 0.02 < f["lon"] < maxx + 0.02 and miny - 0.02 < f["lat"] < maxy + 0.02]
    ax.scatter([f["lon"] for f in near], [f["lat"] for f in near], s=14, c="#1b7837",
               marker="P", zorder=4,
               label=f"OSM health facilities ({len(near)} shown)")
    ax.set_aspect("equal")
    ax.set_xlabel("longitude (EPSG:4326)")
    ax.set_ylabel("latitude (EPSG:4326)")
    ax.set_title("Landhi Town: distance to the nearest health facility\n"
                 "OpenStreetMap, straight line x 1.3 circuity factor")
    ax.legend(loc="lower left", fontsize=8)
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.75)
    bar.set_label("metres to nearest health facility")
    fig.tight_layout()
    fig.savefig(PREVIEW)
    plt.close(fig)
    print(f"Wrote {PREVIEW.name} to artifacts/")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
