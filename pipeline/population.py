"""P1-06: people per cell, from two independent sources, compared honestly.

Neither source is rescaled to match the census. Population counts are summed with each
pixel assigned to exactly one cell, so totals conserve.

Run:
    uv run python -m pipeline.population
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402
from shapely.geometry import shape  # noqa: E402

from pipeline.config import ARTIFACTS, PROCESSED, RAW, load  # noqa: E402
from pipeline.fetch import fetch  # noqa: E402
from pipeline.grid import clip  # noqa: E402
from pipeline.hdx import fetch_tile  # noqa: E402
from pipeline.zonal import sum_by_cell  # noqa: E402

OUTPUT = PROCESSED / "population_cells.csv"
COMPARISON = PROCESSED / "population_source_comparison.csv"
PREVIEW = ARTIFACTS / "population_cells_map.png"


def ensure_sources(cfg: dict) -> dict[str, Path]:
    meta = cfg["sources"]["meta"]
    worldpop = cfg["sources"]["worldpop"]
    fetch_tile(meta["hdx_dataset"], meta["hdx_resource"], meta["zip_member"],
               meta["cache_path"], licence=meta["licence"], note=meta["name"])
    fetch(worldpop["url"], worldpop["cache_path"], licence=worldpop["licence"],
          note=worldpop["name"])
    return {"meta": RAW / meta["cache_path"], "worldpop": RAW / worldpop["cache_path"]}


def build() -> dict[str, float]:
    cfg = load("population")
    paths = ensure_sources(cfg)

    boundary = shape(json.loads(
        (PROCESSED / "pilot_area.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"])
    grid = json.loads((PROCESSED / "grid.geojson").read_text(encoding="utf-8"))
    cells = [(f["properties"]["h3"], clip(shape(f["geometry"]), boundary))
             for f in grid["features"]]
    areas = {f["properties"]["h3"]: f["properties"]["clipped_area_km2"]
             for f in grid["features"]}

    results = {}
    for key, path in paths.items():
        with rasterio.open(path) as src:
            sums, pixels, _ = sum_by_cell(src, cells)
        results[key] = {"sums": sums, "pixels": pixels, "total": sum(sums.values())}
        print(f"{cfg['sources'][key]['name'][:44]:44s} total {results[key]['total']:>10,.0f}"
              f"  px/cell median {int(np.median(list(pixels.values())))}")

    meta_values = np.array([results["meta"]["sums"][c] for c, _ in cells])
    wp_values = np.array([results["worldpop"]["sums"][c] for c, _ in cells])
    from scipy.stats import spearmanr
    rho = spearmanr(meta_values, wp_values).statistic
    pearson = float(np.corrcoef(meta_values, wp_values)[0, 1])
    print(f"Per-cell agreement between the two sources: Spearman rho {rho:.3f}, "
          f"Pearson r {pearson:.3f}")

    check = cfg["independent_check"]["pilot"]
    print(f"\nIndependent figure: {check['unit']} {check['figure']:,} ({check['source']})")
    for key in results:
        ratio = results[key]["total"] / check["figure"]
        print(f"  {key:9s} {results[key]['total']:>10,.0f}  =  {ratio:.2f} x the census figure")

    chosen = cfg["chosen"]
    other = "worldpop" if chosen == "meta" else "meta"
    rows = []
    for cell_id, _ in cells:
        people = results[chosen]["sums"][cell_id]
        rows.append({
            "h3": cell_id,
            "population": round(people, 2),
            "population_alt": round(results[other]["sums"][cell_id], 2),
            "density_per_km2": round(people / areas[cell_id], 1) if areas[cell_id] else 0.0,
            "source_pixels": results[chosen]["pixels"][cell_id],
        })
    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with COMPARISON.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source", "resolution_m", "reference_year", "pilot_total",
                         "median_pixels_per_cell", "cells_with_zero_people",
                         "census_2023_landhi", "ratio_to_census"])
        for key in ("meta", "worldpop"):
            total = results[key]["total"]
            writer.writerow([
                cfg["sources"][key]["name"], cfg["sources"][key]["resolution_m"],
                cfg["sources"][key]["reference_year"], round(total),
                int(np.median(list(results[key]["pixels"].values()))),
                sum(1 for v in results[key]["sums"].values() if v == 0),
                check["figure"], round(total / check["figure"], 3),
            ])
    print(f"Wrote data/processed/{OUTPUT.name} and {COMPARISON.name}")

    densities = [r["density_per_km2"] for r in rows]
    print(f"Density per km2: min {min(densities):,.0f}, median {np.median(densities):,.0f}, "
          f"max {max(densities):,.0f}")
    _map(grid, rows)
    return {"total": results[chosen]["total"], "rho": float(rho),
            "ratio": results[chosen]["total"] / check["figure"]}


def _map(grid: dict, rows: list[dict]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    by_cell = {r["h3"]: r for r in rows}
    positive = [r["population"] for r in rows if r["population"] > 0]
    norm = LogNorm(vmin=max(min(positive), 1), vmax=max(positive))
    cmap = plt.get_cmap("viridis")
    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=110)
    for feature in grid["features"]:
        row = by_cell[feature["properties"]["h3"]]
        x, y = shape(feature["geometry"]).exterior.xy
        colour = "#e8e8e8" if row["population"] <= 0 else cmap(norm(row["population"]))
        ax.fill(x, y, facecolor=colour, edgecolor="white", linewidth=0.2, zorder=2)
    ax.set_aspect("equal")
    ax.set_xlabel("longitude (EPSG:4326)")
    ax.set_ylabel("latitude (EPSG:4326)")
    ax.set_title("Landhi Town: modelled people per cell\n"
                 "Meta High Resolution Population Density (2020), grey = no people modelled")
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.75)
    bar.set_label("people per cell (log scale)")
    ax.grid(True, linewidth=0.3, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PREVIEW)
    plt.close(fig)
    print(f"Wrote {PREVIEW.name} to artifacts/")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
