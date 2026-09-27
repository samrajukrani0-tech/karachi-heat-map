"""Write the SYNTHETIC fixtures the planner's end-to-end tests compare against.

    uv run python tests/fixtures/make_planner_fixtures.py

Both files are SYNTHETIC by name and content, live under tests/, and are only ever
served to the page through Playwright route interception -- never from site/.
tests/test_planner_fixtures.py fails if they drift from what this script produces.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from pipeline import allocate, scenarios  # noqa: E402

GREEDY = HERE / "greedy_parity_SYNTHETIC.json"
SCENARIOS = HERE / "scenarios_SYNTHETIC.json"


def greedy_cases(seed: int = 20260927, n: int = 60) -> list[dict]:
    """Random problems, including ties, fractional need and unreachable pairs."""
    rng = np.random.default_rng(seed)
    cases = []
    for k in range(n):
        cells, points = int(rng.integers(1, 12)), int(rng.integers(1, 4))
        priority = np.round(rng.uniform(0, 1, cells), 2 if k % 3 == 0 else 6)  # ties
        need = np.round(rng.uniform(0, 60, cells), 2)
        need[rng.uniform(size=cells) < 0.15] = 0
        stock = np.round(rng.uniform(0, 120, points), 1)
        dist = np.round(rng.uniform(0, 8000, (cells, points)))
        max_d = 5000.0
        plan = allocate.solve_greedy(priority, need, stock, dist, max_distance_m=max_d)
        cases.append({"priority": priority.tolist(), "need": need.tolist(),
                      "stock": stock.tolist(), "dist": dist.tolist(),
                      "max_distance_m": max_d, "expected_x": plan.x.tolist()})
    # Hand-written cases where tie order decides the answer. Random draws almost never
    # produce one: a mutation reversing the tie-break passed all 60 of them.
    ties = [
        # equal priority, stock for only one cell: the lower index must win
        ([0.5, 0.5], [10, 10], [10], [[100], [100]]),
        # equidistant points: the lower-index point must be drawn first
        ([0.9], [5], [5, 5], [[200, 200]]),
        # both at once
        ([0.7, 0.7, 0.2], [6, 6, 6], [4, 4], [[300, 300], [300, 300], [300, 300]]),
    ]
    for priority, need, stock, dist in ties:
        plan = allocate.solve_greedy(np.array(priority, float), np.array(need, float),
                                     np.array(stock, float), np.array(dist, float),
                                     max_distance_m=5000.0)
        cases.append({"priority": priority, "need": need, "stock": stock, "dist": dist,
                      "max_distance_m": 5000.0, "expected_x": plan.x.tolist()})
    return cases


def distance_cases() -> list[dict]:
    """Python's UTM 42N distances between real cell centroids and a test point."""
    cells = scenarios.load_cells()
    point = np.array([[67.18, 24.845]])
    idx = [0, 50, 100, 150, 200, 264]
    d = allocate.distance_matrix(cells.lonlat[idx], point, 1.3)[:, 0]
    return [{"cell": cells.lonlat[i].tolist(), "point": point[0].tolist(),
             "circuity": 1.3, "expected_m": float(m)} for i, m in zip(idx, d, strict=True)]


def scenario_document() -> dict:
    """A scenarios.json as it would look with one verified depot. SYNTHETIC."""
    cells = scenarios.load_cells()
    lon, lat = cells.lonlat.mean(axis=0)
    row = {"name": "SYNTHETIC depot", "org": "SYNTHETIC", "role": "distribution_point",
           "can_hold_stock": "yes", "lat": str(lat), "lon": str(lon),
           "source": "SYNTHETIC", "verified_by": "SYNTHETIC",
           "verified_on": "2026-09-27", "notes": "SYNTHETIC test fixture"}
    return scenarios.document(scenarios.build_scenarios(cells, [row]), 1)


def build() -> dict[Path, dict]:
    return {GREEDY: {"note": "SYNTHETIC", "greedy": greedy_cases(),
                     "distance": distance_cases()},
            SCENARIOS: scenario_document()}


def main() -> int:
    for path, doc in build().items():
        path.write_text(json.dumps(doc, separators=(",", ":")) + "\n", encoding="utf-8")
        print(f"wrote {path.name} ({path.stat().st_size / 1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
