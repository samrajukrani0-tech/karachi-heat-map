"""Named localities inside Landhi, from OpenStreetMap place nodes.

Used by the expert-ranking form (P2-05) and the field briefs (P5-01). Every name is a
real OSM place node inside the pilot boundary -- nothing is invented (§2.1). OSM maps
only a small part of Landhi (D18), so this list is certainly incomplete; field staff
are asked to add places it misses.

A place node is a point, not a boundary. "The area around" a locality is therefore
defined here, openly, as the cells whose centre lies within RADIUS_M of that point, plus
the cell the point falls in. It is not an official neighbourhood boundary.

Run:
    uv run python -m pipeline.localities
"""

from __future__ import annotations

import csv

import h3
from shapely.geometry import Point

from pipeline import overpass
from pipeline.config import PROCESSED, load
from pipeline.grid import load_boundary

OUT = PROCESSED / "localities.csv"
PLACE_CLASSES = ("suburb", "neighbourhood", "quarter", "village", "hamlet")
RADIUS_M = 500
FIELDS = ["name_en", "name_osm", "place", "lat", "lon", "osm_node", "h3_cell"]


def fetch_places() -> list[dict]:
    west, south, east, north = load_boundary().bounds
    body = (f'[out:json][timeout:120];'
            f'node["place"]["name"]({south},{west},{north},{east});out body;')
    payload, _ = overpass.query(body, "landhi_places")
    return [e for e in payload.get("elements", []) if e.get("type") == "node"]


def build() -> list[dict]:
    boundary = load_boundary()
    resolution = int(load("area")["grid"]["resolution"])
    rows = []
    for node in fetch_places():
        tags = node.get("tags", {})
        # "town" is Landhi itself, the whole pilot area, not a locality within it
        if tags.get("place") not in PLACE_CLASSES:
            continue
        if not boundary.contains(Point(node["lon"], node["lat"])):
            continue
        rows.append({"name_en": tags.get("name:en") or tags["name"],
                     "name_osm": tags["name"], "place": tags["place"],
                     "lat": round(node["lat"], 6), "lon": round(node["lon"], 6),
                     "osm_node": node["id"],
                     "h3_cell": h3.latlng_to_cell(node["lat"], node["lon"], resolution)})
    rows.sort(key=lambda r: r["name_en"])
    return rows


def read() -> list[dict]:
    with OUT.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = build()
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Localities: {len(rows)} named OSM place nodes inside Landhi -> "
          f"data/processed/{OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
