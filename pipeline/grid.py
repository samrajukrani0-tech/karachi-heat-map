"""P1-02: cover the pilot boundary with H3 cells at the resolution chosen in D3.

Inclusion rule (config/area.yaml, grid.inclusion_rule): a cell is included when its
centre lies inside the boundary, OR when at least 50% of the cell's area falls inside
it. Both areas are measured in EPSG:32642, never in degrees.

Run:
    uv run python -m pipeline.grid
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

import h3
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import MultiPolygon, Point, Polygon, mapping, shape  # noqa: E402
from shapely.ops import transform, unary_union  # noqa: E402

from pipeline.config import ARTIFACTS, MEASUREMENT_CRS, PROCESSED, STORAGE_CRS, load  # noqa: E402

BOUNDARY = PROCESSED / "pilot_area.geojson"
OUTPUT = PROCESSED / "grid.geojson"
PREVIEW = ARTIFACTS / "grid_preview.png"
MIN_COVERAGE = 0.99         # P1-02 acceptance criterion; never lower this
_TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform


def load_boundary() -> Polygon | MultiPolygon:
    if not BOUNDARY.exists():
        raise SystemExit("data/processed/pilot_area.geojson is missing; run P1-01 first")
    doc = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    return shape(doc["features"][0]["geometry"])


def cell_polygon(cell: str) -> Polygon:
    """H3 gives (lat, lng); shapely wants (lng, lat)."""
    return Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(cell)])


def cell_centre(cell: str) -> Point:
    lat, lng = h3.cell_to_latlng(cell)
    return Point(lng, lat)


def clip(cell_poly: Polygon, boundary: Polygon | MultiPolygon):
    """The part of a cell that lies inside the pilot area.

    Every indicator is computed over this, not the whole hexagon, so an edge cell can
    never report values measured in a neighbouring town (config/area.yaml, D15).
    """
    return cell_poly.intersection(boundary)


def select_cells(boundary: Polygon | MultiPolygon, resolution: int,
                 min_area_fraction: float) -> list[dict[str, Any]]:
    """Apply the documented inclusion rule to every candidate cell."""
    # Buffer by roughly one cell diameter so edge cells whose centre sits outside the
    # boundary are still considered; the rule below decides which of them get in.
    candidates = h3.geo_to_cells(boundary.buffer(0.004), resolution)

    boundary_utm = transform(_TO_UTM, boundary)
    selected: list[dict[str, Any]] = []
    for cell in candidates:
        poly = cell_polygon(cell)
        poly_utm = transform(_TO_UTM, poly)
        cell_area = poly_utm.area
        if cell_area == 0:
            continue
        inside_fraction = poly_utm.intersection(boundary_utm).area / cell_area
        centre_inside = boundary.contains(cell_centre(cell))
        if centre_inside or inside_fraction >= min_area_fraction:
            selected.append({
                "h3": cell,
                "polygon": poly,
                "area_km2": cell_area / 1e6,
                "clipped_area_km2": poly_utm.intersection(boundary_utm).area / 1e6,
                "inside_fraction": inside_fraction,
                "centre_inside": centre_inside,
            })
    selected.sort(key=lambda c: c["h3"])
    return selected


def build() -> dict[str, Any]:
    area_cfg = load("area")
    resolution = int(area_cfg["grid"]["resolution"])
    min_area_fraction = float(area_cfg["grid"]["min_area_fraction"])
    boundary = load_boundary()
    boundary_utm = transform(_TO_UTM, boundary)

    cells = select_cells(boundary, resolution, min_area_fraction)
    if not cells:
        raise SystemExit("no cells selected; check the boundary and resolution")

    covered = unary_union([transform(_TO_UTM, c["polygon"]) for c in cells])
    coverage = covered.intersection(boundary_utm).area / boundary_utm.area
    areas = [c["area_km2"] for c in cells]
    by_rule = sum(1 for c in cells if not c["centre_inside"])

    print(f"Resolution: {resolution} (H3)")
    print(f"Cells: {len(cells)}  ({len(cells) - by_rule} by centre, "
          f"{by_rule} by the >={min_area_fraction:.0%} area rule)")
    print(f"Coverage of the boundary: {coverage * 100:.3f}% (minimum {MIN_COVERAGE * 100:.0f}%)")
    print(f"Cell area km2: min {min(areas):.5f}, mean {sum(areas) / len(areas):.5f}, "
          f"max {max(areas):.5f}")
    clipped = sum(c["clipped_area_km2"] for c in cells)
    print(f"Grid area: {sum(areas):.3f} km2 (hexagons) / {clipped:.3f} km2 (clipped) "
          f"against a boundary of {boundary_utm.area / 1e6:.3f} km2")
    print(f"Overhang outside the pilot area: {sum(areas) - clipped:.3f} km2, "
          f"excluded from every indicator by clipping")

    if coverage < MIN_COVERAGE:
        raise SystemExit(
            f"FAIL: cells cover {coverage * 100:.3f}% of the boundary, below the "
            f"{MIN_COVERAGE * 100:.0f}% acceptance criterion for P1-02."
        )
    low, high = area_cfg["grid"]["expected_cells_min"], area_cfg["grid"]["expected_cells_max"]
    if not low <= len(cells) <= high:
        raise SystemExit(
            f"FAIL: {len(cells)} cells is outside the documented sanity range "
            f"{low}-{high} in config/area.yaml. Investigate before overwriting the grid."
        )

    doc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "metadata": {
            "feature": "P1-02",
            "h3_resolution": resolution,
            "cell_count": len(cells),
            "cells_by_centre": len(cells) - by_rule,
            "cells_by_area_rule": by_rule,
            "inclusion_rule": " ".join(area_cfg["grid"]["inclusion_rule"].split()),
            "min_area_fraction": min_area_fraction,
            "indicators_use": "the clipped geometry (cell intersect boundary), not the hexagon",
            "clipped_area_km2": round(sum(c["clipped_area_km2"] for c in cells), 4),
            "hexagon_area_km2": round(sum(areas), 4),
            "boundary_coverage": round(coverage, 6),
            "areas_measured_in": MEASUREMENT_CRS,
            "boundary_source": "data/processed/pilot_area.geojson (P1-01)",
            "licence": "ODbL 1.0 - derived from OpenStreetMap, (c) OpenStreetMap contributors",
            "generated": dt.date.today().isoformat(),
            "generated_by": "uv run python -m pipeline.grid (feature P1-02)",
            "decision": "D3 and D15 (see DECISIONS.md)",
        },
        "features": [
            {
                "type": "Feature",
                "geometry": mapping(c["polygon"]),
                "properties": {
                    "h3": c["h3"],
                    "area_km2": round(c["area_km2"], 6),
                    "clipped_area_km2": round(c["clipped_area_km2"], 6),
                    "inside_fraction": round(c["inside_fraction"], 6),
                    "centre_inside": c["centre_inside"],
                },
            }
            for c in cells
        ],
    }
    OUTPUT.write_text(json.dumps(doc) + "\n", encoding="utf-8")
    print(f"Wrote data/processed/{OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} kB)")

    _preview(boundary, cells, coverage)
    return doc["metadata"]


def _preview(boundary, cells, coverage: float) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.5, 7.5), dpi=110)
    for c in cells:
        x, y = c["polygon"].exterior.xy
        colour = "#cfe3ea" if c["centre_inside"] else "#f2d9c4"
        ax.fill(x, y, facecolor=colour, edgecolor="#8fa9b2", linewidth=0.35, zorder=2)
    parts = boundary.geoms if isinstance(boundary, MultiPolygon) else [boundary]
    for part in parts:
        bx, by = part.exterior.xy
        ax.plot(bx, by, color="#a6341b", linewidth=1.8, zorder=3)
    ax.set_aspect("equal")
    ax.set_xlabel("longitude (EPSG:4326)")
    ax.set_ylabel("latitude (EPSG:4326)")
    ax.set_title(f"Landhi Town: {len(cells)} H3 resolution-9 cells\n"
                 f"boundary coverage {coverage * 100:.2f}%  "
                 f"(blue = centre inside, tan = area rule)")
    ax.grid(True, linewidth=0.3, alpha=0.4)
    fig.tight_layout()
    fig.savefig(PREVIEW)
    plt.close(fig)
    print(f"Wrote {PREVIEW.name} ({PREVIEW.stat().st_size / 1024:.0f} kB) to artifacts/")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
