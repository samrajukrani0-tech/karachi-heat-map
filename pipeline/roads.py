"""P5-02: a simplified outline of Landhi's main roads, for the offline map.

Offline, the basemap tiles are unavailable -- and they are Esri's, so the project does
not cache or redistribute them (data/SOURCES.md). The offline view instead draws the
main roads from OpenStreetMap, simplified hard enough that the file stays small. It is
orientation, not navigation: enough to recognise Korangi Road and the National Highway
around the hexagons.

One Overpass query, cached in data/raw/osm/ like every other (§2.8).

Run:
    uv run python -m pipeline.roads
"""

from __future__ import annotations

import json

from pyproj import Transformer
from shapely.geometry import LineString, mapping
from shapely.ops import transform as shp_transform

from pipeline import overpass
from pipeline.config import MEASUREMENT_CRS, PROCESSED, ROOT, STORAGE_CRS
from pipeline.grid import load_boundary

CLASSES = ("motorway", "trunk", "primary", "secondary", "tertiary")
BUFFER_KM = 1.0
TOLERANCE_M = 15.0          # Douglas-Peucker tolerance; a road moves at most this far
PRECISION = 5               # ~1 m
SITE_OUT = ROOT / "site" / "data" / "roads.geojson"
BUDGET_KB = 150

_TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform
_TO_LONLAT = Transformer.from_crs(MEASUREMENT_CRS, STORAGE_CRS, always_xy=True).transform


def fetch_roads() -> list[dict]:
    west, south, east, north = load_boundary().bounds
    d = BUFFER_KM / 111.0
    body = (f'[out:json][timeout:180];'
            f'way["highway"~"^({"|".join(CLASSES)})$"]'
            f'({south - d},{west - d},{north + d},{east + d});'
            f'out geom tags;')
    payload, _ = overpass.query(body, f"main_roads_buffer{int(BUFFER_KM)}km")
    return [e for e in payload.get("elements", []) if e.get("type") == "way"]


def simplify(ways: list[dict]) -> list[dict]:
    features = []
    for way in ways:
        coords = [(p["lon"], p["lat"]) for p in way.get("geometry", [])]
        if len(coords) < 2:
            continue
        line = shp_transform(_TO_UTM, LineString(coords)).simplify(TOLERANCE_M)
        line = shp_transform(_TO_LONLAT, line)
        geometry = mapping(line)
        geometry["coordinates"] = [[round(x, PRECISION), round(y, PRECISION)]
                                   for x, y in geometry["coordinates"]]
        tags = way.get("tags", {})
        features.append({"type": "Feature", "geometry": geometry,
                         "properties": {"class": tags.get("highway"),
                                        "name": tags.get("name:en") or tags.get("name")}})
    return features


def main() -> int:
    ways = fetch_roads()
    features = simplify(ways)
    doc = {"type": "FeatureCollection",
           "metadata": {"source": "OpenStreetMap via Overpass, highway classes "
                                  + ", ".join(CLASSES),
                        "simplified_m": TOLERANCE_M, "buffer_km": BUFFER_KM,
                        "licence": "ODbL 1.0 - (c) OpenStreetMap contributors",
                        "purpose": "offline orientation only, not navigation"},
           "features": features}
    text = json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n"
    for path in (PROCESSED / "roads.geojson", SITE_OUT):
        path.write_text(text, encoding="utf-8")
    kb = len(text.encode()) / 1024
    print(f"Roads: {len(ways)} ways -> {len(features)} lines, {kb:.0f} kB "
          f"(budget {BUDGET_KB} kB)")
    if kb > BUDGET_KB:
        raise SystemExit(f"FAIL: roads.geojson is {kb:.0f} kB, over {BUDGET_KB} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
