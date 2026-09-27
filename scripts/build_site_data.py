"""Write the site's data files into site/data/.

Kept small on purpose: the whole first load must stay under 1.5 MB on a 3G phone, so
geometry is rounded to 5 decimal places (about 1 m at this latitude) and only the fields
the site actually renders are included.

Run:
    uv run python scripts/build_site_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# Run as a script, so the repo root is not on the path; the pipeline package lives there.
sys.path.insert(0, str(ROOT))
from pipeline.scenarios import load_cells  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "site" / "data"
PRECISION = 5


def round_coords(geometry: dict) -> dict:
    return {"type": geometry["type"],
            "coordinates": [[[round(x, PRECISION), round(y, PRECISION)] for x, y in ring]
                            for ring in geometry["coordinates"]]}


def main() -> int:
    grid = json.loads((PROCESSED / "grid.geojson").read_text(encoding="utf-8"))
    scores = pd.read_csv(PROCESSED / "scores.csv").set_index("h3")
    confidence = pd.read_csv(PROCESSED / "confidence.csv").set_index("h3")
    indicators = pd.read_parquet(PROCESSED / "indicators.parquet").set_index("h3")
    weights_used = json.loads((PROCESSED / "scores_weights_used.json").read_text("utf-8"))

    # The clipped-cell centroid, the same point the allocation solvers measure from, so
    # the planner's browser-side quick estimate uses identical geometry (P4-03).
    cells = load_cells()
    centroid = {h: (round(float(x), PRECISION), round(float(y), PRECISION))
                for h, (x, y) in zip(cells.h3, cells.lonlat, strict=True)}

    features = []
    for feature in grid["features"]:
        cell = feature["properties"]["h3"]
        s, c, i = scores.loc[cell], confidence.loc[cell], indicators.loc[cell]
        features.append({
            "type": "Feature",
            "geometry": round_coords(feature["geometry"]),
            "properties": {
                "h3": cell,
                "rank": int(s["rank"]),
                "priority": round(float(s["priority"]), 3),
                "hazard": round(float(s["hazard"]), 3),
                "exposure": round(float(s["exposure"]), 3),
                "vulnerability": round(float(s["vulnerability"]), 3),
                "intensity": None if pd.isna(s["intensity"]) else round(float(s["intensity"]), 3),
                "reasons": [r for r in str(s["top_reasons"]).split("; ") if r],
                "stability": c["stability"],
                "rank_low": int(c["rank_low_5pct"]),
                "rank_high": int(c["rank_high_95pct"]),
                "lst": round(float(i["lst_mean_c"]), 1),
                "lst_p90": round(float(i["lst_p90_c"]), 1),
                "people": int(round(float(i["population"]))),
                "green": round(float(i["green_fraction"]), 3),
                "built": round(float(i["built_fraction"]), 3),
                "dist_health": int(round(float(i["dist_health_m"]))),
                "over60": int(round(float(i["people_over60"]))),
                "under5": int(round(float(i["people_under5"]))),
                "c": list(centroid[cell]),
            },
        })

    max_rank = int(scores["rank"].max())
    document = {
        "type": "FeatureCollection",
        "metadata": {
            "area": "Landhi Town, Karachi",
            "cells": len(features),
            "distinguishable_ranks": max_rank,
            "weights_provisional": bool(scores["weights_provisional"].iloc[0]),
            "model_incomplete": bool(scores["model_incomplete"].iloc[0]),
            "missing_indicators": weights_used["missing_indicators"],
            "vulnerability_weights_used": weights_used["within_dimension"]["vulnerability"],
            "licence": "ODbL 1.0 - contains data derived from OpenStreetMap, "
                       "(c) OpenStreetMap contributors",
            "generated": pd.Timestamp.today().strftime("%Y-%m-%d"),
        },
        "features": features,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "cells.geojson"
    path.write_text(json.dumps(document, separators=(",", ":")) + "\n", encoding="utf-8")
    size = path.stat().st_size / 1024
    print(f"Wrote site/data/{path.name}: {len(features)} cells, {size:.0f} kB")
    if size > 1024:
        raise SystemExit(f"FAIL: {size:.0f} kB exceeds the 1 MB budget for the data file")
    print(f"  ranks run 1..{max_rank} ({len(features) - max_rank + 1} cells tie at the bottom)")
    print(f"  weights provisional: {document['metadata']['weights_provisional']}; "
          f"missing indicators: {document['metadata']['missing_indicators']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
