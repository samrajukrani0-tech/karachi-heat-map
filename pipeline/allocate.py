"""P4-01: who gets how much, from which centre.

The question: "we have this much supply at these centres -- which cells get what?"

Two solvers, on purpose:
  * ``solve_lp`` is exact. It maximises total priority-weighted supply delivered,
    subject to each centre's stock and each cell's need, over pairs within the
    service distance D.
  * ``solve_greedy`` is the baseline a person would use with a paper map: take the
    highest-priority cell, serve it from the nearest centre that still has stock,
    move on. It is fast enough to run in a browser, which is why the site offers it
    as a "quick estimate", and it is here mainly so the LP has something to beat.

The LP can never do worse than greedy, because greedy's answer is itself a feasible
point of the LP. ``docs/allocation.md`` works two examples by hand, one of which
greedy gets badly wrong.

Nothing here reads a data file. The solvers take arrays and return arrays, so the
tests exercise them on small SYNTHETIC problems whose answers are known on paper.

Run:
    uv run python -m pipeline.allocate
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from pyproj import Transformer
from scipy.optimize import linprog

from pipeline.config import MEASUREMENT_CRS, STORAGE_CRS

_TO_UTM = Transformer.from_crs(STORAGE_CRS, MEASUREMENT_CRS, always_xy=True).transform

# The objective's distance term is scaled by D, not left in metres. See
# docs/allocation.md, "Why the tiebreak is divided by D": at epsilon = 0.001 a raw
# metre distance of 5,000 contributes 5.0 against a priority of at most 1.0, so the
# "small" tiebreak would outweigh the thing it is meant to break ties in.


@dataclass(frozen=True)
class Plan:
    """One allocation. ``x[i, j]`` is units sent from centre j to cell i."""

    x: np.ndarray
    method: str
    objective: float             # the objective value of x itself
    delivered: np.ndarray        # units per cell
    dispatched: np.ndarray       # units per centre
    unmet: np.ndarray            # need not covered, per cell
    equity_shortfall: float      # units by which the top quintile misses its floor
    reachable: np.ndarray        # bool per cell: any centre within D
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        return float(self.x.sum())


def distance_matrix(cells: np.ndarray, centres: np.ndarray, circuity: float) -> np.ndarray:
    """Straight-line metres in UTM 42N, inflated by the circuity factor.

    ``cells`` and ``centres`` are (n, 2) arrays of lon, lat. Road distance is longer
    than straight-line distance; the factor is the documented stand-in for routing
    (config/allocation.yaml, same convention as pipeline/access.py).
    """
    if circuity < 1.0:
        raise ValueError(f"circuity factor must be >= 1, got {circuity}")
    cx, cy = _TO_UTM(cells[:, 0], cells[:, 1])
    sx, sy = _TO_UTM(centres[:, 0], centres[:, 1])
    dx = np.asarray(cx)[:, None] - np.asarray(sx)[None, :]
    dy = np.asarray(cy)[:, None] - np.asarray(sy)[None, :]
    return np.hypot(dx, dy) * circuity


def need_units(people_in_need: np.ndarray, units_per_person_per_day: float) -> np.ndarray:
    """Units of a commodity a cell needs per day.

    Need is defined from the vulnerable population, never from Priority (D8). Using
    Priority here would put the model's own judgement on both sides of the
    optimisation and make any allocation look well targeted by construction.
    """
    return np.asarray(people_in_need, dtype=float) * float(units_per_person_per_day)


def top_quintile(priority: np.ndarray, need: np.ndarray) -> np.ndarray:
    """Boolean mask of the top 20% of cells by priority, among those with need.

    Cells with no need are excluded before the quintile is cut: a cell nobody lives
    in cannot be owed a share of the supply, and leaving it in would shrink the set
    the equity rule is supposed to protect.
    """
    priority, need = np.asarray(priority, float), np.asarray(need, float)
    mask = np.zeros(priority.shape, dtype=bool)
    eligible = np.flatnonzero(need > 0)
    if eligible.size == 0:
        return mask
    k = max(1, int(np.ceil(0.2 * eligible.size)))
    order = eligible[np.argsort(-priority[eligible], kind="stable")]
    mask[order[:k]] = True
    return mask


def objective_value(x: np.ndarray, priority: np.ndarray, dist: np.ndarray,
                    max_distance_m: float, epsilon: float) -> float:
    """Sum of priority-weighted units delivered, less the small distance tiebreak.

    The cost is summed over servable pairs only. Summing over the whole matrix looks
    equivalent -- an unservable pair has x = 0 -- but ``inf * 0`` is ``nan`` in IEEE
    arithmetic, so a single out-of-range distance recorded as ``inf`` would turn the
    objective into ``nan``. Every comparison against a nan is False, so "did the LP
    beat greedy?" would quietly answer no.
    """
    x = np.asarray(x, dtype=float)
    dist = np.asarray(dist, dtype=float)
    servable = dist <= max_distance_m
    gain = float((np.asarray(priority, float)[:, None] * x).sum())
    cost = float(epsilon * (dist[servable] / max_distance_m * x[servable]).sum())
    return gain - cost


def equity_floor(need: np.ndarray, stock: np.ndarray, top: np.ndarray,
                 min_share: float) -> float:
    """The units the top-quintile cells are owed, as a fixed quantity (D27).

    Deliberately NOT a share of what the solver decides to allocate. A floor written
    as ``sum_T x >= alpha * sum x`` can be satisfied by making ``sum x`` smaller, and
    with a penalty of lambda per unit of shortfall a unit sent to a non-top cell nets
    ``p_i - alpha*lambda`` -- so at the configured 0.25 every cell below Priority 0.25
    becomes worth *not* serving, and the plan leaves supply in the warehouse to look
    equitable. Priority is a geometric mean on [0, 1], so sub-0.25 cells are entirely
    ordinary, not a corner case.

    Anchoring the floor to ``min(total stock, total need)`` -- the most that could ever
    be delivered, which the solver cannot influence -- removes the incentive: sending a
    unit to a non-top cell leaves the floor untouched, so it is still worth sending.
    """
    deliverable = min(float(np.asarray(stock, float).sum()),
                      float(np.asarray(need, float).sum()))
    return min_share * deliverable if top.any() else 0.0


def _validate(priority, need, stock, dist, max_distance_m, epsilon):
    """Checks both solvers share, so greedy refuses exactly what the LP refuses.

    Greedy is the path the site exposes as the browser-side "quick estimate", so it is
    the one malformed input reaches first. It used to accept a negative stock as an
    empty centre and a shape mismatch as an IndexError.
    """
    priority = np.asarray(priority, dtype=float)
    need = np.asarray(need, dtype=float)
    stock = np.asarray(stock, dtype=float)
    dist = np.asarray(dist, dtype=float)
    if dist.ndim != 2:
        raise ValueError(f"dist must be (cells, centres), got shape {dist.shape}")
    n_cells, n_centres = dist.shape
    if priority.shape != (n_cells,) or need.shape != (n_cells,):
        raise ValueError(
            f"priority and need must have one entry per cell ({n_cells}), got "
            f"{priority.shape} and {need.shape}")
    if stock.shape != (n_centres,):
        raise ValueError(f"stock must have one entry per centre ({n_centres}), "
                         f"got {stock.shape}")
    if np.any(need < 0) or np.any(stock < 0):
        raise ValueError("need and stock must be non-negative")
    if np.isnan(dist).any():
        raise ValueError("dist contains nan; an unservable pair must be a large "
                         "distance, not a missing one")
    if not max_distance_m > 0:
        raise ValueError(f"max_distance_m must be positive, got {max_distance_m}")
    if epsilon < 0:
        raise ValueError(f"epsilon must be non-negative, got {epsilon}: a negative "
                         "tiebreak would prefer the *farther* centre")
    return priority, need, stock, dist


def solve_lp(priority: np.ndarray, need: np.ndarray, stock: np.ndarray, dist: np.ndarray,
             *, max_distance_m: float, epsilon: float = 0.001,
             min_share_top_quintile: float = 0.0, equity_penalty: float = 1.0,
             round_units: bool = True) -> Plan:
    """Exact allocation by linear programming (HiGHS).

        maximise   sum_ij p_i x_ij - eps * sum_ij (d_ij / D) x_ij - lambda * u
        subject to sum_i x_ij <= s_j            (stock at each centre)
                   sum_j x_ij <= need_i         (nobody gets more than they need)
                   sum_{i in T,j} x_ij  >=  F - u            (equity, soft)
                   x_ij >= 0, defined only where d_ij <= D;  u >= 0

    ``F = alpha * min(total stock, total need)`` is a constant, computed before the
    solve. Writing the floor as a share of ``sum x`` instead lets the solver satisfy
    it by allocating less -- see ``equity_floor`` and D27.

    The rule is soft -- ``u`` absorbs the shortfall at a price -- because a hard
    version can be infeasible when the top-quintile cells are simply not reachable
    from the centres holding stock, and an infeasible solver returns nothing at all
    rather than the best plan available. The shortfall is reported, with its cause.
    """
    priority, need, stock, dist = _validate(
        priority, need, stock, dist, max_distance_m, epsilon)
    n_cells, n_centres = dist.shape

    within = dist <= max_distance_m
    reachable = within.any(axis=1)
    pairs = np.argwhere(within)
    notes: list[str] = []

    if pairs.size == 0 or stock.sum() == 0 or need.sum() == 0:
        x = np.zeros((n_cells, n_centres))
        notes.append("nothing to allocate: no stock, no need, or no cell within reach")
        return _plan(x, "lp", priority, need, dist, max_distance_m, epsilon,
                     np.zeros(n_cells, bool), 0.0, reachable, notes)

    rows, cols = pairs[:, 0], pairs[:, 1]
    m = len(pairs)
    top = top_quintile(priority, need)
    floor_units = equity_floor(need, stock, top, min_share_top_quintile)
    use_equity = floor_units > 0

    # minimise c.x, so the sign of the gain flips
    c = np.concatenate([epsilon * (dist[rows, cols] / max_distance_m) - priority[rows],
                        [equity_penalty] if use_equity else []])

    # The problem is small -- at most one variable per (cell, centre) pair within D --
    # so a dense constraint matrix is clearer here than a sparse one and costs nothing.
    n_vars = m + (1 if use_equity else 0)
    blocks, b = [], []
    centre_of = np.zeros((n_centres, n_vars))
    centre_of[cols, np.arange(m)] = 1.0
    keep_centre = np.flatnonzero(centre_of[:, :m].any(axis=1))
    blocks.append(centre_of[keep_centre])
    b.extend(stock[keep_centre].tolist())

    cell_of = np.zeros((n_cells, n_vars))
    cell_of[rows, np.arange(m)] = 1.0
    keep_cell = np.flatnonzero(cell_of[:, :m].any(axis=1))
    blocks.append(cell_of[keep_cell])
    b.extend(need[keep_cell].tolist())

    if use_equity:
        # floor - sum_{i in T} x - u <= 0, with the floor a constant (D27)
        equity = np.zeros((1, n_vars))
        equity[0, :m] = -top[rows].astype(float)
        equity[0, m] = -1.0
        blocks.append(equity)
        b.append(-floor_units)

    a_ub = np.vstack(blocks)
    upper = np.concatenate([np.minimum(need[rows], stock[cols]),
                            [np.inf] if use_equity else []])
    result = linprog(c, A_ub=a_ub, b_ub=np.array(b, dtype=float),
                     bounds=np.column_stack([np.zeros(n_vars), upper]), method="highs")
    if not result.success:
        raise RuntimeError(f"the allocation LP did not solve: {result.message}")

    x = np.zeros((n_cells, n_centres))
    x[rows, cols] = np.maximum(result.x[:m], 0.0)
    if round_units:
        x = largest_remainder(x, stock, need)
    return _plan(x, "lp", priority, need, dist, max_distance_m, epsilon, top,
                 floor_units, reachable, notes)


def solve_greedy(priority: np.ndarray, need: np.ndarray, stock: np.ndarray,
                 dist: np.ndarray, *, max_distance_m: float, epsilon: float = 0.001,
                 min_share_top_quintile: float = 0.0, round_units: bool = True) -> Plan:
    """The paper-map baseline: highest priority first, nearest centre with stock.

    Deterministic: ties in priority break on cell index and ties in distance on
    centre index, so the same inputs always give the same plan.
    """
    priority, need, stock, dist = _validate(
        priority, need, stock, dist, max_distance_m, epsilon)
    need, left = need.copy(), stock.copy()
    n_cells, n_centres = dist.shape
    x = np.zeros((n_cells, n_centres))

    for i in np.argsort(-priority, kind="stable"):
        if need[i] <= 0:
            continue
        for j in np.argsort(dist[i], kind="stable"):
            if need[i] <= 0:
                break
            if dist[i, j] > max_distance_m or left[j] <= 0:
                continue
            send = min(need[i], left[j])
            if round_units:
                send = float(np.floor(send))
            if send <= 0:
                continue
            x[i, j] += send
            need[i] -= send
            left[j] -= send

    original_need = need + x.sum(axis=1)   # need was decremented in place
    top = top_quintile(priority, original_need)
    floor_units = equity_floor(original_need, stock, top, min_share_top_quintile)
    return _plan(x, "greedy", priority, original_need, dist, max_distance_m, epsilon,
                 top, floor_units, (dist <= max_distance_m).any(axis=1), [])


def largest_remainder(x: np.ndarray, stock: np.ndarray, need: np.ndarray) -> np.ndarray:
    """Round a fractional plan to whole units without exceeding stock or need.

    Floor everything, then hand out the units that floor threw away in order of the
    largest fractional remainder -- but only where the centre still has stock and the
    cell still has unmet need. Both caps are checked at the moment each unit is
    placed, so the rounding cannot break either. Plain per-centre rounding would
    respect stock and quietly break need.

    It can only preserve a cap that ``x`` already respects: flooring 9.7 against a
    stock of 2 gives 9, which is still over. Every plan ``solve_lp`` produces is
    feasible, but this is a public function, so an infeasible input is refused rather
    than quietly passed through -- a future JavaScript port of the browser-side
    estimate is exactly the caller that would be caught out.
    """
    x = np.asarray(x, dtype=float)
    stock = np.asarray(stock, dtype=float)
    need = np.asarray(need, dtype=float)
    if np.any(x.sum(axis=0) > stock + 1e-9) or np.any(x.sum(axis=1) > need + 1e-9):
        raise ValueError("largest_remainder was given a plan that already exceeds "
                         "stock or need; rounding cannot repair an infeasible plan")
    out = np.floor(x)
    centre_left = np.floor(stock) - out.sum(axis=0)
    cell_left = np.floor(need) - out.sum(axis=1)
    remainder = x - out
    # Hand back only the units flooring actually discarded. Without this budget the
    # method can return more than it was given -- flooring 7.7 units of plan down to 6
    # and then adding one unit per position with slack gives 8 -- which is feasible but
    # is no longer a rounding of the plan it was handed.
    budget = int(np.floor(x.sum() + 1e-9) - out.sum())
    order = np.argsort(-remainder, axis=None, kind="stable")
    for flat in order:
        if budget <= 0:
            break
        i, j = np.unravel_index(flat, x.shape)
        if remainder[i, j] <= 0:
            break
        if centre_left[j] >= 1 and cell_left[i] >= 1:
            out[i, j] += 1
            centre_left[j] -= 1
            cell_left[i] -= 1
            budget -= 1
    return out


def _plan(x, method, priority, need, dist, max_distance_m, epsilon, top, floor_units,
          reachable, notes) -> Plan:
    delivered = x.sum(axis=1)
    need = np.asarray(need, float)
    shortfall = max(0.0, floor_units - float(x[top].sum())) if top.any() else 0.0
    if shortfall > 0:
        notes.append(f"the top-priority cells are {shortfall:,.0f} units short of the "
                     f"{floor_units:,.0f} they are owed -- {_why_short(x, top, need, reachable)}")
    return Plan(x=x, method=method,
                objective=objective_value(x, priority, dist, max_distance_m, epsilon),
                delivered=delivered, dispatched=x.sum(axis=0),
                unmet=np.maximum(np.asarray(need, float) - delivered, 0.0),
                equity_shortfall=shortfall, reachable=reachable, notes=notes)


def _why_short(x, top, need, reachable) -> str:
    """Say which of the three causes it actually was.

    The first version of this note asserted the top cells were out of range, which is
    frequently untrue -- the usual cause is that they are already full. A field brief
    repeating that would send someone to solve a distance problem that does not exist.
    """
    if np.allclose(x[top].sum(axis=1), need[top]):
        return ("their own need is already fully met, so the floor asks for more than "
                "they can use")
    if not reachable[top].all():
        return "some of them have no centre within the service distance"
    return "there is not enough stock within reach of them"


def main() -> int:
    import csv

    from pipeline.config import MANUAL

    path = MANUAL / "centres.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8"))) if path.exists() else []
    holders = [r for r in rows if str(r.get("can_hold_stock", "")).strip().lower() == "yes"]
    if not holders:
        print("No verified relief centre can hold stock, so there is nothing to allocate "
              "from (QUESTIONS.md Q2). The solver itself is tested on synthetic problems; "
              "run `uv run pytest tests/test_allocate.py`.")
        return 0
    print(f"{len(holders)} stock-holding centres found. P4-02 builds the scenarios.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
