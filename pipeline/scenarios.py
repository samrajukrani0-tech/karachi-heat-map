"""P4-02a: precomputed allocation scenarios for the site.

A scenario answers one "what if": this commodity, this much stock, this service
distance. For each one the exact solver and the greedy baseline are both run, and the
result is exported as *shares* -- the fraction of the stock each cell receives and the
order in which cells are served -- never as absolute litres or sachets (D21). The
population layer undercounts Landhi by about 2.3x (D16); a share of whatever stock a
centre has is a ratio of two numbers carrying the same bias, an absolute total is not.

Stock is therefore also expressed relative to need: "stock equal to 25% / 50% / 100%
of the model's estimated need". That keeps every figure a ratio, and it is honest
about what the model cannot know -- how much a centre actually holds.

Centres reach the solvers only through ``allocate.stock_holding_centres`` (D13, D29).
Until at least one centre in data/manual/centres.csv is verified in person and can
hold stock (QUESTIONS.md Q2), the export is an honest empty list with the reason, not
a set of scenarios built from invented locations.

Run:
    uv run python -m pipeline.scenarios
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as shp_transform

from pipeline import allocate
from pipeline.config import MANUAL, MEASUREMENT_CRS, PROCESSED, ROOT, STORAGE_CRS, load
from pipeline.grid import clip, load_boundary

SITE_OUT = ROOT / "site" / "data" / "scenarios.json"
PROCESSED_OUT = PROCESSED / "scenarios.json"
STOCK_FRACTIONS = (0.25, 0.5, 1.0)

_TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform
_TO_LONLAT = Transformer.from_crs(MEASUREMENT_CRS, STORAGE_CRS, always_xy=True).transform

UNDERCOUNT_NOTE = (
    "The population layer counts about 295,000 people in Landhi against 681,293 in the "
    "2023 census (D16), so the model's estimate of need is roughly 2.3 times too low. "
    "Shares of the stock are unaffected by that; any absolute quantity would not be.")


@dataclass(frozen=True)
class Cells:
    h3: list[str]
    lonlat: np.ndarray      # (n, 2) centroid of the clipped cell
    priority: np.ndarray
    people_in_need: np.ndarray


def load_cells() -> Cells:
    """Priority and D8's people in need (aged 60+ plus under 5), per clipped cell."""
    grid = json.loads((PROCESSED / "grid.geojson").read_text(encoding="utf-8"))
    scores = pd.read_csv(PROCESSED / "scores.csv").set_index("h3")
    ages = pd.read_csv(PROCESSED / "age_cells.csv").set_index("h3")
    boundary = load_boundary()
    ids, points = [], []
    for feature in grid["features"]:
        cell = feature["properties"]["h3"]
        clipped = clip(shape(feature["geometry"]), boundary)
        centre = shp_transform(_TO_LONLAT, shp_transform(_TO_UTM, clipped).centroid)
        ids.append(cell)
        points.append((centre.x, centre.y))
    need = (ages.loc[ids, "people_over60"] + ages.loc[ids, "people_under5"]).to_numpy(float)
    return Cells(h3=ids, lonlat=np.array(points),
                 priority=scores.loc[ids, "priority"].to_numpy(float),
                 people_in_need=need)


def read_centres(path: Path | None = None) -> list[dict]:
    path = path or MANUAL / "centres.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if any(v.strip() for v in r.values() if v)]


def _cell_rows(cells: Cells, plan: allocate.Plan, stock_total: float) -> list[dict]:
    """Only cells that receive something, as shares of the stock, in serving order."""
    order = np.argsort(-cells.priority, kind="stable")
    rows, position = [], 0
    for i in order:
        got = float(plan.delivered[i])
        if got <= 0:
            continue
        position += 1
        rows.append({"h3": cells.h3[i], "order": position,
                     "share_of_stock": round(got / stock_total, 4),
                     "share_of_need_met": round(got / (got + float(plan.unmet[i])), 3)})
    return rows


def _cause(notes: list[str]) -> str:
    """The reason part of the solver's shortfall note, which carries no quantity."""
    for note in notes:
        if " -- " not in note:
            continue
        cause = note.split(" -- ", 1)[1].split(" (this is")[0]
        if cause.startswith("the floor asks for"):
            # this branch of allocate._why_short quotes units; restate it without them
            return "their whole estimated need is smaller than the floor"
        return cause
    return ""


def summarise(s: dict) -> str:
    """One paragraph a coordinator can read, in shares only (D21)."""
    top = s["lp"]["top_quintile_share"]
    served = s["lp"]["cells_served"]
    parts = [
        f"{s['commodity_name']}, with stock equal to {s['stock_fraction']:.0%} of the "
        f"model's estimated need and a {s['max_distance_m'] / 1000:g} km service limit.",
        f"The plan reaches {served} of {s['cells_with_need']} areas where people live; "
        f"the highest-priority fifth of areas receive {top:.0%} of the stock.",
    ]
    if s["cells_out_of_reach"]:
        parts.append(f"{s['cells_out_of_reach']} areas are beyond the service limit of "
                     "every centre that can hold stock and receive nothing.")
    if s["lp"]["undelivered_share"] > 0.005:
        parts.append(f"{s['lp']['undelivered_share']:.0%} of the stock cannot be used, "
                     "because every area within reach already has its estimated need met.")
    short = s["lp"]["equity_shortfall_share"]
    if short > 0.005:
        # The solver's own note gives this in units; D21 allows only the share.
        parts.append(f"The highest-priority fifth of areas are owed "
                     f"{s['equity_floor_share']:.0%} of the deliverable supply and fall "
                     f"short by {short:.0%} of the stock -- {s['lp']['equity_cause']}.")
    gain = s["lp"]["objective"] - s["greedy"]["objective"]
    relative = gain / max(s["greedy"]["objective"], 1e-9)
    parts.append("The exact plan and the quick estimate agree to within 0.1%."
                 if relative < 0.001 else
                 f"The exact plan scores {relative:.1%} higher than the quick estimate "
                 "on priority-weighted delivery.")
    parts.append("Illustrative: the allocation settings are provisional (D8) and real "
                 "need is higher than the model estimates.")
    return " ".join(p[0].upper() + p[1:] for p in parts)


def build_scenarios(cells: Cells, centre_rows: list[dict]) -> list[dict]:
    """Every (commodity x stock level x service distance) scenario for these centres.

    Stock is split equally between the stock-holding centres. That is an assumption,
    stated in every scenario, until centres report what they actually hold.
    """
    holders = allocate.stock_holding_centres(centre_rows)
    if not holders:
        return []
    cfg = load("allocation")
    kwargs = allocate.lp_kwargs()
    centres = np.array([[float(r["lon"]), float(r["lat"])] for r in holders])
    circuity = float(cfg["service"]["circuity_factor"])
    dist = allocate.distance_matrix(cells.lonlat, centres, circuity)
    distances = sorted({float(cfg["service"]["max_distance_m"]),
                        *map(float, cfg["service"]["sensitivity_distances_m"])})
    out = []
    for commodity in cfg["commodities"]:
        rate = allocate.commodity_settings(commodity["id"])["units_per_person_per_day"]
        need = np.floor(allocate.need_units(cells.people_in_need, rate))
        for fraction in STOCK_FRACTIONS:
            total = float(np.floor(fraction * need.sum()))
            stock = np.full(len(holders), np.floor(total / len(holders)))
            stock_total = float(stock.sum())
            for d in distances:
                kw = {**kwargs, "max_distance_m": d}
                lp = allocate.solve_lp(cells.priority, need, stock, dist, **kw)
                gr = allocate.solve_greedy(
                    cells.priority, need, stock, dist,
                    **{k: v for k, v in kw.items() if k in allocate.greedy_kwargs()})
                top = allocate.top_quintile(cells.priority, need)
                scenario = {
                    "id": f"{commodity['id']}-{int(fraction * 100)}pct-{int(d)}m",
                    "commodity": commodity["id"],
                    "commodity_name": commodity["name_en"],
                    "stock_fraction": fraction,
                    "max_distance_m": d,
                    "centres": [{"name": r["name"], "org": r["org"], "role": r["role"],
                                 "stock_share": round(1 / len(holders), 4)}
                                for r in holders],
                    "stock_split": "equal between stock-holding centres (assumption)",
                    "cells_with_need": int((need > 0).sum()),
                    "cells_out_of_reach": int(((need > 0) & ~lp.reachable).sum()),
                    "equity_floor_share": kw["min_share_top_quintile"],
                }
                for name, plan in (("lp", lp), ("greedy", gr)):
                    scenario[name] = {
                        "objective": round(plan.objective, 4),
                        "cells_served": int((plan.delivered > 0).sum()),
                        "top_quintile_share": round(
                            float(plan.delivered[top].sum()) / stock_total, 4)
                        if stock_total else 0.0,
                        "undelivered_share": round(1 - plan.total / stock_total, 4)
                        if stock_total else 0.0,
                        "equity_shortfall_share": round(
                            plan.equity_shortfall / stock_total, 4) if stock_total else 0.0,
                        "equity_cause": _cause(plan.notes),
                        # Per-cell rows for the exact plan only: the site draws the exact
                        # plan, and the greedy rows would double the file for no reader.
                        "cells": (_cell_rows(cells, plan, stock_total)
                                  if stock_total and name == "lp" else []),
                    }
                scenario["summary"] = summarise(scenario)
                out.append(scenario)
    return out


def document(scenarios: list[dict], n_rows: int) -> dict:
    cfg = load("allocation")
    water = next(c for c in cfg["commodities"] if c["id"] == "water")
    if scenarios:
        status, message = "ok", f"{len(scenarios)} precomputed scenarios."
    else:
        status = "no_verified_centre"
        message = ("No relief centre that can hold stock has been verified in person yet "
                   "(QUESTIONS.md Q2), so there are no exact scenarios to show. They are "
                   "computed automatically once one is added to data/manual/centres.csv. "
                   "Nothing here is built from unverified or invented locations.")
    return {
        "status": status,
        "message": message,
        "provisional": bool(cfg["provisional"]),
        "illustrative": True,
        "shares_only": "D21: every figure is a share of the stock or of estimated need, "
                       "never an absolute quantity.",
        "undercount_note": UNDERCOUNT_NOTE,
        "water_basis": water["basis"].strip(),
        "centre_rows_read": n_rows,
        # What the browser-side quick estimate needs, so the page never hard-codes a
        # decision that lives in config/allocation.yaml.
        "planner": {
            "commodities": [{"id": c["id"], "name_en": c["name_en"], "unit": c["unit"],
                             "units_per_person_per_day": float(c["units_per_person_per_day"])}
                            for c in cfg["commodities"]],
            "max_distance_m": float(cfg["service"]["max_distance_m"]),
            "distances_m": sorted({float(cfg["service"]["max_distance_m"]),
                                   *map(float, cfg["service"]["sensitivity_distances_m"])}),
            "circuity_factor": float(cfg["service"]["circuity_factor"]),
        },
        "scenarios": scenarios,
    }


def main() -> int:
    rows = read_centres()
    doc = document(build_scenarios(load_cells(), rows), len(rows))
    text = json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n"
    for path in (PROCESSED_OUT, SITE_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"Scenarios: {len(doc['scenarios'])} ({doc['status']}); "
          f"{len(text) / 1024:.1f} kB; centre rows read: {len(rows)}")
    print(doc["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
