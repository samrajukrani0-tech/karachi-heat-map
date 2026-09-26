"""P1-04b: hot-season daytime LST per grid cell.

Mean and 90th-percentile surface temperature for each H3 cell, computed over the
CLIPPED cell (cell intersect pilot boundary) so no cell reports a neighbouring town's
heat (D15). Cells resting on too few pixels or too few clear satellite looks are
flagged rather than silently averaged.

Run:
    uv run python -m pipeline.heat
"""

from __future__ import annotations

import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from shapely.geometry import shape  # noqa: E402

from pipeline.config import ARTIFACTS, PROCESSED, load  # noqa: E402
from pipeline.grid import clip  # noqa: E402
from pipeline.lst import COMPOSITE  # noqa: E402
from pipeline.zonal import summarise  # noqa: E402

GRID = PROCESSED / "grid.geojson"
BOUNDARY = PROCESSED / "pilot_area.geojson"
OUTPUT = PROCESSED / "lst_cells.csv"
PREVIEW = ARTIFACTS / "lst_cells_map.png"


def build() -> dict[str, float]:
    cfg = load("heat")
    cells_cfg = cfg["cells"]
    if not COMPOSITE.exists():
        raise SystemExit("data/raw/derived/lst_hot_season.tif is missing; run "
                         "`uv run python -m pipeline.lst` first (P1-04a)")

    boundary = shape(json.loads(BOUNDARY.read_text(encoding="utf-8"))["features"][0]["geometry"])
    grid = json.loads(GRID.read_text(encoding="utf-8"))

    rows = []
    with rasterio.open(COMPOSITE) as src:
        for feature in grid["features"]:
            cell = feature["properties"]["h3"]
            clipped = clip(shape(feature["geometry"]), boundary)
            stats = summarise(src, clipped, percentile=cells_cfg["percentile"],
                              value_band=1, count_band=2)
            flags = []
            if stats["mean"] is None:
                flags.append("no_pixels")
            else:
                if stats["coverage"] < cells_cfg["min_pixel_coverage"]:
                    flags.append("thin_pixel_coverage")
                if (stats["clear_looks_median"] or 0) < cells_cfg["min_clear_looks"]:
                    flags.append("few_clear_looks")
                if stats["touched_fallback"]:
                    flags.append("all_touched_fallback")
            rows.append({
                "h3": cell,
                "lst_mean_c": None if stats["mean"] is None else round(stats["mean"], 3),
                f"lst_p{cells_cfg['percentile']}_c": (
                    None if stats["percentile"] is None else round(stats["percentile"], 3)),
                "pixels": stats["pixels"],
                "pixel_coverage": round(stats["coverage"], 4),
                "clear_looks_median": (None if stats["clear_looks_median"] is None
                                       else int(stats["clear_looks_median"])),
                "flags": "|".join(flags),
            })

    means = [r["lst_mean_c"] for r in rows if r["lst_mean_c"] is not None]
    p90s = [r[f"lst_p{cells_cfg['percentile']}_c"] for r in rows
            if r[f"lst_p{cells_cfg['percentile']}_c"] is not None]
    flagged = [r for r in rows if r["flags"]]

    print(f"Cells: {len(rows)}; with values: {len(means)}; flagged: {len(flagged)}")
    for flag in ("no_pixels", "thin_pixel_coverage", "few_clear_looks", "all_touched_fallback"):
        count = sum(1 for r in rows if flag in r["flags"])
        if count:
            print(f"  {flag}: {count}")
    print(f"Mean LST per cell: {min(means):.2f} to {max(means):.2f} degC "
          f"(median {np.median(means):.2f}, spread {max(means) - min(means):.2f})")
    print(f"P{cells_cfg['percentile']} LST per cell: {min(p90s):.2f} to {max(p90s):.2f} degC")
    print(f"Pixels per cell: min {min(r['pixels'] for r in rows)}, "
          f"median {int(np.median([r['pixels'] for r in rows]))}")

    low = cfg["plausible_range_celsius"]["min"]
    high = cfg["plausible_range_celsius"]["max"]
    if min(means) < low or max(p90s) > high:
        raise SystemExit(f"FAIL: per-cell values span {min(means):.2f} to {max(p90s):.2f} degC, "
                         f"outside the documented plausible range {low}-{high}.")
    if not means:
        raise SystemExit("FAIL: no cell received a value")

    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote data/processed/{OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} kB)")

    _map(grid, rows, means)
    return {"cells": len(rows), "min": min(means), "max": max(means),
            "median": float(np.median(means)), "flagged": len(flagged)}


def _map(grid: dict, rows: list[dict], means: list[float]) -> None:
    by_cell = {r["h3"]: r for r in rows}
    norm = Normalize(vmin=min(means), vmax=max(means))
    cmap = plt.get_cmap("inferno")
    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=110)
    for feature in grid["features"]:
        row = by_cell[feature["properties"]["h3"]]
        poly = shape(feature["geometry"])
        x, y = poly.exterior.xy
        value = row["lst_mean_c"]
        colour = "#cccccc" if value is None else cmap(norm(value))
        ax.fill(x, y, facecolor=colour, edgecolor="white", linewidth=0.2, zorder=2)
    ax.set_aspect("equal")
    ax.set_xlabel("longitude (EPSG:4326)")
    ax.set_ylabel("latitude (EPSG:4326)")
    ax.set_title("Landhi Town: hot-season daytime surface temperature\n"
                 "mean of the April–June median composite, 2022–2026")
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.75)
    bar.set_label("land surface temperature (°C)")
    ax.grid(True, linewidth=0.3, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PREVIEW)
    plt.close(fig)
    print(f"Wrote {PREVIEW.name} ({PREVIEW.stat().st_size / 1024:.0f} kB) to artifacts/")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
