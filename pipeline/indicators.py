"""P1-11: join every per-cell layer into one indicator table.

One row per H3 cell, one column per indicator or piece of context, with a QA report and
an explicit missing-value summary. Columns that are indicators are marked as such; the
rest are context shown in the cell panel but not scored (LST p90, built fraction, age
counts).

Run:
    uv run python -m pipeline.indicators
"""

from __future__ import annotations

import json
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from pipeline.config import ARTIFACTS, PROCESSED, load  # noqa: E402

PARQUET = PROCESSED / "indicators.parquet"
CSV = PROCESSED / "indicators.csv"
QA = ARTIFACTS / "indicators_qa.png"

# column -> (source file, role, unit, description)
LAYERS: dict[str, tuple[str, str, str, str]] = {
    "lst_mean_c": ("lst_cells.csv", "indicator", "degC",
                   "Hot-season daytime land surface temperature, mean of the April-June "
                   "median composite 2022-2026"),
    "lst_p90_c": ("lst_cells.csv", "context", "degC",
                  "90th percentile of the same composite: how hot the cell gets at worst. "
                  "Shown in the panel, not indexed (D4)"),
    "population": ("population_cells.csv", "indicator", "people",
                   "Modelled residents, Meta HRSL v1.5 (2020). Undercounts: see D16"),
    "density_per_km2": ("population_cells.csv", "context", "people per km2",
                        "Population divided by the clipped cell area"),
    "people_over60": ("age_cells.csv", "context", "people",
                      "Modelled residents aged 60+. Used by D8's need definition, not indexed"),
    "people_under5": ("age_cells.csv", "context", "people",
                      "Modelled residents under 5. Used by D8's need definition, not indexed"),
    "lack_green": ("landcover_cells.csv", "indicator", "fraction",
                   "1 minus green cover fraction, ESA WorldCover 10 m (2021)"),
    "green_fraction": ("landcover_cells.csv", "context", "fraction",
                       "Vegetation classes 10/20/30/40/95"),
    "built_fraction": ("landcover_cells.csv", "context", "fraction",
                       "WorldCover built-up surface. Dropped as an indicator by D19 "
                       "(correlates ~0.93 with lack_green and double-counts Hazard)"),
    "dist_health_m": ("access_cells.csv", "indicator", "m",
                      "Straight-line distance to the nearest OSM health facility x 1.3 "
                      "circuity factor. Overstates isolation: OSM maps ~11% of Landhi (D18)"),
}
PENDING = {
    "dist_centre_m": ("indicator", "m",
                      "Distance to the nearest VERIFIED relief centre. Empty: P1-09b is "
                      "blocked on QUESTIONS.md Q2, and there is no open-data fallback"),
}


def build() -> dict[str, Any]:
    grid = json.loads((PROCESSED / "grid.geojson").read_text(encoding="utf-8"))
    frame = pd.DataFrame({
        "h3": [f["properties"]["h3"] for f in grid["features"]],
        "clipped_area_km2": [f["properties"]["clipped_area_km2"] for f in grid["features"]],
        "inside_fraction": [f["properties"]["inside_fraction"] for f in grid["features"]],
    })

    for column, (filename, *_rest) in LAYERS.items():
        source = pd.read_csv(PROCESSED / filename)
        if column not in source.columns:
            raise SystemExit(f"{filename} has no column {column}")
        merged = source[["h3", column]]
        before = len(frame)
        frame = frame.merge(merged, on="h3", how="left", validate="one_to_one")
        if len(frame) != before:
            raise SystemExit(f"joining {filename} changed the row count")

    for column in PENDING:
        frame[column] = pd.NA

    indicators = [c for c, (_, role, *_x) in LAYERS.items() if role == "indicator"]
    configured = {i["id"] for i in load("indicators")["indicators"]}
    print(f"Cells: {len(frame)}; columns: {len(frame.columns)}")
    print(f"Indicator columns present: {len(indicators)} of {len(configured)} configured")

    missing_rows = []
    for column in list(LAYERS) + list(PENDING):
        missing = int(frame[column].isna().sum())
        missing_rows.append({"column": column, "missing": missing,
                             "missing_pct": round(missing / len(frame) * 100, 2)})
    print("\nMissing-value summary:")
    for row in missing_rows:
        flag = "  <-- BLOCKED" if row["missing"] == len(frame) else ""
        print(f"   {row['column']:22s} {row['missing']:>4} missing "
              f"({row['missing_pct']:>5.1f}%){flag}")

    for column in indicators:
        if column in PENDING:
            continue
        if frame[column].isna().any():
            raise SystemExit(f"FAIL: indicator {column} has missing values; every scored "
                             f"indicator must be complete for the cells it covers")

    PARQUET.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(PARQUET, index=False)
    frame.to_csv(CSV, index=False)
    print(f"\nWrote data/processed/{PARQUET.name} ({PARQUET.stat().st_size / 1024:.0f} kB) "
          f"and {CSV.name} ({CSV.stat().st_size / 1024:.0f} kB)")

    _qa_figure(frame, indicators)
    _data_dictionary(frame, missing_rows)
    return {"cells": len(frame), "columns": len(frame.columns),
            "indicators_present": len(indicators)}


def _qa_figure(frame: pd.DataFrame, indicators: list[str]) -> None:
    numeric = [c for c in LAYERS if frame[c].notna().any()]
    cols = 3
    rows = (len(numeric) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(13, 3.1 * rows), dpi=110)
    for ax, column in zip(axes.ravel(), numeric, strict=False):
        values = frame[column].dropna().astype(float)
        ax.hist(values, bins=28, color="#4c72b0" if column in indicators else "#b0b0b0",
                edgecolor="white", linewidth=0.4)
        role = "indicator" if column in indicators else "context"
        ax.set_title(f"{column}  ({role})", fontsize=9)
        ax.tick_params(labelsize=7)
        ax.axvline(values.median(), color="#a6341b", linewidth=1.1)
    for ax in axes.ravel()[len(numeric):]:
        ax.axis("off")
    fig.suptitle("Landhi indicator table: distributions (red line = median). "
                 "Blue = scored indicator, grey = panel context", fontsize=11)
    fig.tight_layout()
    fig.savefig(QA)
    plt.close(fig)
    print(f"Wrote {QA.name} to artifacts/")


def _data_dictionary(frame: pd.DataFrame, missing_rows: list[dict]) -> None:
    missing_by_column = {r["column"]: r for r in missing_rows}
    lines = [
        "# Data dictionary",
        "",
        "`data/processed/indicators.parquet` and `indicators.csv` — one row per H3 cell.",
        "",
        f"**Cells:** {len(frame)} · **Columns:** {len(frame.columns)} · "
        "**Grid:** H3 resolution 9 over Landhi Town (D2, D3)",
        "",
        "Every value is computed over the **clipped** cell — the part of the hexagon inside",
        "the pilot boundary — so no cell reports a neighbouring town's measurements (D15).",
        "",
        "| Column | Role | Unit | Missing | Description |",
        "|---|---|---|---|---|",
        "| `h3` | key | — | 0 | H3 cell index, resolution 9 |",
        "| `clipped_area_km2` | key | km² | 0 | Area of the cell inside the pilot boundary |",
        "| `inside_fraction` | key | fraction | 0 | Share of the hexagon inside the boundary |",
    ]
    for column, (_source, role, unit, description) in LAYERS.items():
        info = missing_by_column[column]
        lines.append(f"| `{column}` | {role} | {unit} | {info['missing']} | {description} |")
    for column, (role, unit, description) in PENDING.items():
        info = missing_by_column[column]
        lines.append(f"| `{column}` | {role} | {unit} | **{info['missing']} (all)** | "
                     f"{description} |")

    lines += [
        "",
        "## Missing values",
        "",
        "Every scored indicator is complete except one, and that gap is structural rather",
        "than accidental:",
        "",
        "- **`dist_centre_m` is empty for all cells.** P1-09b is blocked on QUESTIONS.md Q2:",
        "  no relief centre has been verified in person, and there is no open-data fallback.",
        "  OpenStreetMap covers about 11% of Landhi's built area (D18), so its silence about",
        "  relief facilities is not evidence that none exist. 11 unverified candidates are",
        "  listed in `data/manual/centre_candidates.csv`; none may enter the model.",
        "  The table is rebuilt once a centre is verified.",
        "",
        "## What these numbers are not",
        "",
        "- `lst_mean_c` is **land surface temperature, not air temperature**, and carries no",
        "  humidity information — which matters enormously in Karachi.",
        "- `population` **undercounts by roughly a factor of 2.3** against the 2023 census",
        "  (D16). Relative ranking survives a uniform factor; the bias may not be uniform.",
        "- `dist_health_m` **overstates** isolation from care, because unmapped clinics can",
        "  only make the true distance shorter (D18).",
        "- Age **shares** were dropped (D17) because Meta's layers encode an administrative",
        "  zone rather than spatial demography. The **counts** here are still usable.",
        "- Load-shedding is absent (D20). The mechanism Faisal Edhi named in June 2024 is the",
        "  one this model cannot see.",
        "",
        "## Provenance",
        "",
        "Every dataset, its licence, access date, resolution and caveats are in",
        "`data/SOURCES.md`. Raw downloads are checksummed in `data/raw/manifest.json`.",
    ]
    path = PROCESSED.parent.parent / "docs" / "data-dictionary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote docs/{path.name} ({len(lines)} lines)")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
