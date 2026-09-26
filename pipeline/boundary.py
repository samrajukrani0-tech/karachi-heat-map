"""P1-01: build the pilot-area boundary from its OpenStreetMap relation.

Landhi Town, OSM relation 16350631, admin_level 7 (decision D2). Geometry is stored
in EPSG:4326; the area is measured in EPSG:32642 (UTM 42N), per PROMPT.md section 6.

Run:
    uv run python -m pipeline.boundary [--refresh]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from typing import Any

import matplotlib

matplotlib.use("Agg")  # no display in CI or a headless run
import matplotlib.pyplot as plt  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping  # noqa: E402
from shapely.ops import linemerge, polygonize, transform, unary_union  # noqa: E402

from pipeline import overpass  # noqa: E402
from pipeline.config import ARTIFACTS, MEASUREMENT_CRS, PROCESSED, STORAGE_CRS, load  # noqa: E402

OUTPUT = PROCESSED / "pilot_area.geojson"
PREVIEW = ARTIFACTS / "pilot_area_preview.png"
_TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform


def area_km2(geometry: Polygon | MultiPolygon) -> float:
    """Area in km^2, measured in UTM 42N rather than in degrees."""
    return transform(_TO_UTM, geometry).area / 1e6


def _ring_lines(members: list[dict[str, Any]], role: str) -> list[LineString]:
    """Member ways with the given role, as lines. OSM leaves the role blank for
    single-ring boundaries, so a blank role counts as outer."""
    accepted = {role} if role == "inner" else {"outer", ""}
    return [
        LineString([(point["lon"], point["lat"]) for point in member["geometry"]])
        for member in members
        if member["type"] == "way"
        and "geometry" in member
        and member.get("role", "") in accepted
        and len(member["geometry"]) >= 2
    ]


def relation_to_polygon(payload: dict[str, Any]) -> Polygon | MultiPolygon:
    """Assemble a relation's member ways into a polygon, subtracting inner rings."""
    elements = payload.get("elements", [])
    if not elements:
        raise ValueError("Overpass returned no elements for the relation")
    members = elements[0].get("members", [])

    outer = list(polygonize(unary_union(linemerge(_ring_lines(members, "outer")))))
    if not outer:
        raise ValueError("member ways did not close into any ring")
    geometry = unary_union(outer)

    inner_lines = _ring_lines(members, "inner")
    if inner_lines:
        holes = unary_union(list(polygonize(unary_union(linemerge(inner_lines)))))
        if not holes.is_empty:
            geometry = geometry.difference(holes)

    if not geometry.is_valid:
        geometry = geometry.buffer(0)
    if geometry.is_empty:
        raise ValueError("assembled boundary is empty")
    return geometry


def build(*, refresh: bool = False) -> dict[str, Any]:
    area_cfg = load("area")["pilot"]
    grid_cfg = load("area")["grid"]
    relation_id = area_cfg["source"]["osm_relation"]

    body = f"[out:json][timeout:300];rel(id:{relation_id});out geom;"
    payload, digest = overpass.query(body, f"relation_{relation_id}", refresh=refresh)
    geometry = relation_to_polygon(payload)
    measured = area_km2(geometry)

    expected = float(area_cfg["area_km2_expected"])
    tolerance = float(area_cfg["area_km2_tolerance"])
    print(f"Pilot area: {area_cfg['name_en']}")
    print(f"OSM relation: {relation_id} (admin_level {area_cfg['source']['admin_level']})")
    print(f"Area: {measured:.3f} km2 (config expects {expected} +/- {tolerance})")
    print(f"Rings: {len(geometry.geoms) if isinstance(geometry, MultiPolygon) else 1}; "
          f"interior holes: {len(geometry.interiors) if isinstance(geometry, Polygon) else 'n/a'}")
    if abs(measured - expected) > tolerance:
        raise SystemExit(
            f"FAIL: measured area {measured:.3f} km2 is outside the documented "
            f"tolerance {expected} +/- {tolerance}. Do not overwrite the boundary; "
            f"investigate whether the OSM relation changed and record it in DECISIONS.md."
        )

    tags = payload["elements"][0].get("tags", {})
    feature = {
        "type": "Feature",
        "geometry": mapping(geometry),
        "properties": {
            "name_en": area_cfg["name_en"],
            "name_osm": tags.get("name"),
            "city": area_cfg["city"],
            "district": area_cfg["district"],
            "country": area_cfg["country"],
            "osm_relation": relation_id,
            "osm_admin_level": area_cfg["source"]["admin_level"],
            "area_km2": round(measured, 4),
            "area_measured_in": MEASUREMENT_CRS,
            "h3_resolution": grid_cfg["resolution"],
            "source": "OpenStreetMap via the Overpass API",
            "source_url": f"https://www.openstreetmap.org/relation/{relation_id}",
            "licence": "ODbL 1.0 - (c) OpenStreetMap contributors",
            "accessed": dt.date.today().isoformat(),
            "raw_response_sha256": digest,
            "raw_response_sha256_note": (
                "fingerprints this particular download, not the geometry: Overpass "
                "embeds a timestamp, so an identical query returns a different hash. "
                "Reproducibility is checked by re-measuring the area, not by this hash."
            ),
            "generated_by": "uv run python -m pipeline.boundary (feature P1-01)",
            "decision": "D2 (see DECISIONS.md)",
        },
    }
    collection = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [feature],
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(collection, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(OUTPUT.parents[2])} "
          f"({OUTPUT.stat().st_size / 1024:.1f} kB, {STORAGE_CRS})")

    _preview(geometry, measured, area_cfg["name_en"])
    return feature["properties"]


def _preview(geometry: Polygon | MultiPolygon, measured: float, name: str) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 7), dpi=110)
    parts = geometry.geoms if isinstance(geometry, MultiPolygon) else [geometry]
    for part in parts:
        x, y = part.exterior.xy
        ax.fill(x, y, facecolor="#cfe3ea", edgecolor="#1f4e5a", linewidth=1.6, zorder=2)
        for hole in part.interiors:
            hx, hy = hole.xy
            ax.fill(hx, hy, facecolor="white", edgecolor="#1f4e5a", linewidth=1.0, zorder=3)
    centroid = geometry.centroid
    ax.plot(centroid.x, centroid.y, marker="+", color="#a6341b", markersize=12, zorder=4)
    ax.set_aspect("equal")
    ax.set_xlabel("longitude (EPSG:4326)")
    ax.set_ylabel("latitude (EPSG:4326)")
    ax.set_title(f"{name} pilot boundary\n{measured:.2f} km$^2$ measured in {MEASUREMENT_CRS}")
    ax.annotate(f"centroid {centroid.y:.5f}, {centroid.x:.5f}",
                xy=(centroid.x, centroid.y), xytext=(6, -14),
                textcoords="offset points", fontsize=8, color="#a6341b")
    ax.grid(True, linewidth=0.3, alpha=0.5)
    fig.tight_layout()
    fig.savefig(PREVIEW)
    plt.close(fig)
    print(f"Wrote {PREVIEW.name} ({PREVIEW.stat().st_size / 1024:.0f} kB) to artifacts/")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the pilot-area boundary (P1-01)")
    parser.add_argument("--refresh", action="store_true",
                        help="re-download from Overpass instead of using the cache")
    args = parser.parse_args()
    build(refresh=args.refresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
