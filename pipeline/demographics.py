"""P1-07: per-cell share aged 60+ and share under 5.

Both layers come from the same Meta release as the total used in P1-06, so the shares
are internally consistent and the D16 undercount largely cancels in the ratio.

A share is undefined, not zero, where a cell has no modelled residents. That rule is in
config/population.yaml and is enforced and tested here.

Run:
    uv run python -m pipeline.demographics
"""

from __future__ import annotations

import csv
import json

import numpy as np
import rasterio
from shapely.geometry import shape

from pipeline.config import PROCESSED, load
from pipeline.grid import clip
from pipeline.hdx import fetch_tile
from pipeline.zonal import sum_by_cell

OUTPUT = PROCESSED / "age_cells.csv"


def build() -> dict[str, float]:
    cfg = load("population")
    meta = cfg["sources"]["meta"]
    rule = cfg["zero_population"]

    boundary = shape(json.loads(
        (PROCESSED / "pilot_area.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"])
    grid = json.loads((PROCESSED / "grid.geojson").read_text(encoding="utf-8"))
    cells = [(f["properties"]["h3"], clip(shape(f["geometry"]), boundary))
             for f in grid["features"]]

    with (PROCESSED / "population_cells.csv").open(encoding="utf-8") as fh:
        totals = {r["h3"]: float(r["population"]) for r in csv.DictReader(fh)}

    counts: dict[str, dict[str, float]] = {}
    for key, layer in cfg["age_layers"].items():
        path = fetch_tile(meta["hdx_dataset"], layer["hdx_resource"], layer["zip_member"],
                          layer["cache_path"], licence=meta["licence"],
                          note=f"Meta HRSL v1.5 {key}, 10-degree tile containing Karachi")
        with rasterio.open(path) as src:
            sums, _, _ = sum_by_cell(src, cells)
        counts[layer["column"]] = sums
        print(f"  {key:22s} total over Landhi: {sum(sums.values()):>9,.0f} "
              f"({sum(sums.values()) / sum(totals.values()) * 100:.1f}% of population)")

    rows = []
    undefined = 0
    for cell_id, _ in cells:
        total = totals[cell_id]
        row: dict[str, object] = {"h3": cell_id, "population": round(total, 2)}
        # Counts are kept as well as shares. The shares turned out to carry no
        # within-Landhi signal (D17), but the COUNTS vary with population and are what
        # D8's need definition actually uses.
        for column, sums in counts.items():
            row[column.replace("share_", "people_")] = round(sums[cell_id], 2)
        if total <= 0:
            undefined += 1
            for column in counts:
                row[column] = ""
            row["flags"] = rule["flag"]
        else:
            for column, sums in counts.items():
                row[column] = round(min(sums[cell_id] / total, 1.0), 5)
            row["flags"] = ""
        rows.append(row)

    defined = [r for r in rows if r["flags"] == ""]
    over60 = [float(r["share_over60"]) for r in defined]
    under5 = [float(r["share_under5"]) for r in defined]
    print(f"\nCells: {len(rows)}; shares defined: {len(defined)}; "
          f"undefined ({rule['flag']}): {undefined}")
    print(f"share_over60: min {min(over60):.4f}, median {np.median(over60):.4f}, "
          f"max {max(over60):.4f}")
    print(f"share_under5: min {min(under5):.4f}, median {np.median(under5):.4f}, "
          f"max {max(under5):.4f}")
    correlation = float(np.corrcoef(over60, under5)[0, 1])
    combined = np.array(over60) + np.array(under5)
    print(f"\nWARNING (D17): the two shares correlate at {correlation:+.4f} and their sum "
          f"spans only {combined.min():.5f}-{combined.max():.5f}.")
    print("  Meta's age layers encode an administrative zone, not spatial demography. "
          "The SHARES carry no within-Landhi signal; the COUNTS still do, and D8 uses those.")

    limits = cfg["plausibility"]
    if max(over60) > limits["share_over60_max"] or max(under5) > limits["share_under5_max"]:
        raise SystemExit(
            f"FAIL: shares exceed the documented plausible maxima "
            f"({limits['share_over60_max']}, {limits['share_under5_max']}). "
            f"Check the layers are the ones they claim to be before publishing."
        )
    for value in over60 + under5:
        if not 0.0 <= value <= 1.0:
            raise SystemExit(f"FAIL: share {value} is outside [0, 1]")

    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote data/processed/{OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} kB)")
    return {"cells": len(rows), "undefined": undefined,
            "over60_median": float(np.median(over60)),
            "under5_median": float(np.median(under5))}


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
