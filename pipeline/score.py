"""P2-03: Hazard, Exposure, Vulnerability, Priority and Intensity per cell.

Priority = H^wH * E^wE * V^wV with the three exponents fixed at 1/3 (D6, D7a).
Intensity = sqrt(H * V), the per-person view, for the equity discussion.

Two rules from D6b are enforced here and tested:
  * Hazard and Vulnerability are floored at 0.01 after normalisation, because an exact
    zero there is an artefact of clipping -- Landhi's coolest cells are still ~40 degC.
  * Exposure is deliberately NOT floored. E = 0 means nobody lives there, which is a real
    absence, so such a cell scores Priority 0 by construction.

Run:
    uv run python -m pipeline.score
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from pipeline.config import PROCESSED, load
from pipeline.normalise import normalise

OUTPUT = PROCESSED / "scores.csv"
# A cell can be below the pilot-area median on every indicator. That is a real answer,
# not a missing one, so it is said rather than left blank -- an empty "why" panel on the
# site would look broken and would tell a coordinator nothing.
NO_REASON_ABOVE_MEDIAN = "Below the Landhi average on every measure we track"
COLUMN_FOR = {"lst_day_mean": "lst_mean_c", "population": "population",
              "lack_green": "lack_green", "dist_health": "dist_health_m",
              "dist_centre": "dist_centre_m"}


class IncompleteDimensionWarning(UserWarning):
    """A dimension is missing one or more of its configured indicators."""


def normalised_indicators(frame: pd.DataFrame, indicators: list[dict], model: dict
                          ) -> tuple[dict[str, np.ndarray], list[str]]:
    """Normalise every indicator that has data. Returns the values and what was missing."""
    norm = model["normalisation"]
    values: dict[str, np.ndarray] = {}
    missing: list[str] = []
    for indicator in indicators:
        column = COLUMN_FOR[indicator["id"]]
        raw = frame[column].to_numpy(dtype="float64", na_value=np.nan)
        if not np.isfinite(raw).any():
            missing.append(indicator["id"])
            continue
        if indicator.get("transform") == "log1p":
            raw = np.log1p(raw)
        values[indicator["id"]] = normalise(
            raw, method=norm["method"], direction=indicator["direction"],
            name=indicator["id"], low_percentile=norm["clip_low_percentile"],
            high_percentile=norm["clip_high_percentile"])
    return values, missing


def dimension_score(values: dict[str, np.ndarray], weights: dict[str, float],
                    dimension: str, n_cells: int) -> tuple[np.ndarray, dict[str, float]]:
    """Weighted arithmetic mean within a dimension, over the indicators that have data.

    When an indicator is missing entirely, its weight is redistributed across the
    survivors rather than the missing values being quietly treated as zero. Both choices
    are decisions; this one is stated, and the weights actually used are returned so they
    can be published alongside the scores.
    """
    available = {name: w for name, w in weights.items() if name in values}
    if not available:
        raise SystemExit(f"dimension {dimension!r} has no indicator with data")
    absent = sorted(set(weights) - set(available))
    total = sum(available.values())
    used = {name: w / total for name, w in available.items()}
    if absent:
        warnings.warn(
            f"dimension {dimension!r} is missing {absent}; the remaining weights were "
            f"renormalised to {({k: round(v, 4) for k, v in used.items()})}. The model is "
            f"incomplete until those indicators exist.",
            IncompleteDimensionWarning, stacklevel=2)
    score = np.zeros(n_cells, dtype="float64")
    for name, weight in used.items():
        score += weight * np.nan_to_num(values[name], nan=0.0)
    return score, used


def weighted_geometric_mean(parts: dict[str, np.ndarray],
                            exponents: dict[str, float]) -> np.ndarray:
    """exp(sum w_i * log x_i), which handles a zero part correctly: the product is 0."""
    total = sum(exponents.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"dimension exponents sum to {total}, not 1")
    stacked = np.vstack([parts[name] for name in exponents])
    powers = np.array([exponents[name] for name in exponents])[:, None]
    zero_anywhere = (stacked <= 0).any(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        logged = np.where(stacked > 0, np.log(stacked), 0.0)
        result = np.exp((powers * logged).sum(axis=0))
    return np.where(zero_anywhere, 0.0, result)


def top_reasons(values: dict[str, np.ndarray], indicators: list[dict], index: int,
                how_many: int = 3) -> list[str]:
    """The indicators pushing this cell furthest above the pilot-area median."""
    phrases = {i["id"]: i["reason_en"] for i in indicators}
    gaps = []
    for name, series in values.items():
        finite = series[np.isfinite(series)]
        if finite.size == 0 or not np.isfinite(series[index]):
            continue
        gap = float(series[index] - np.median(finite))
        if gap > 0:
            gaps.append((gap, phrases.get(name, name)))
    if not gaps:
        return [NO_REASON_ABOVE_MEDIAN]
    gaps.sort(reverse=True)
    return [phrase for _gap, phrase in gaps[:how_many]]


def build() -> dict[str, object]:
    model = load("model")
    weights_cfg = load("weights")
    indicators = load("indicators")["indicators"]
    frame = pd.read_parquet(PROCESSED / "indicators.parquet")
    n = len(frame)

    values, missing = normalised_indicators(frame, indicators, model)
    if missing:
        print(f"  indicators with no data yet: {', '.join(missing)}")

    floors = model["aggregation"]["floor"]
    parts, used_weights = {}, {}
    for dimension in ("hazard", "exposure", "vulnerability"):
        score, used = dimension_score(values, weights_cfg[dimension], dimension, n)
        floor = floors.get(dimension)
        if floor is not None:
            score = np.maximum(score, float(floor))
        parts[dimension] = score
        used_weights[dimension] = used
        note = f"(floored at {floor})" if floor is not None else "(unfloored, D6b)"
        print(f"  {dimension:<14} from {list(used)}  min {score.min():.4f} "
              f"median {np.median(score):.4f} max {score.max():.4f}  {note}")

    exponents = weights_cfg["dimensions"]
    priority = weighted_geometric_mean(parts, exponents)
    # Intensity deliberately excludes Exposure, so it is UNDEFINED where nobody lives:
    # "how bad is it for a person here" has no answer when there is no person here. Left
    # unmasked, an empty cell scored as high as 0.74 and ranked 24th of 265, which would
    # be indefensible on a measure presented as a per-person view.
    intensity = np.sqrt(parts["hazard"] * parts["vulnerability"])
    intensity = np.where(parts["exposure"] > 0, intensity, np.nan)

    reasons = [top_reasons(values, indicators, i) for i in range(n)]
    scores = pd.DataFrame({
        "h3": frame["h3"],
        "hazard": np.round(parts["hazard"], 6),
        "exposure": np.round(parts["exposure"], 6),
        "vulnerability": np.round(parts["vulnerability"], 6),
        "priority": np.round(priority, 6),
        "intensity": np.round(intensity, 6),
        "rank": pd.Series(priority).rank(ascending=False, method="min").astype(int),
        "top_reasons": ["; ".join(r) for r in reasons],
        "weights_provisional": bool(weights_cfg["provisional"]),
        "model_incomplete": bool(missing),
    })
    scores = scores.sort_values("rank").reset_index(drop=True)

    zero_priority = int((priority == 0).sum())
    print(f"\n  priority  min {priority.min():.6f}  median {np.median(priority):.6f}  "
          f"max {priority.max():.6f}")
    finite_intensity = intensity[np.isfinite(intensity)]
    print(f"  intensity min {finite_intensity.min():.6f}  "
          f"median {np.median(finite_intensity):.6f}  max {finite_intensity.max():.6f}  "
          f"({len(intensity) - len(finite_intensity)} undefined: no residents)")
    print(f"  cells with Priority exactly 0 (nobody lives there): {zero_priority}")
    print(f"  weights provisional: {weights_cfg['provisional']}   "
          f"model incomplete: {bool(missing)}")

    if not (0.0 <= priority.min() and priority.max() <= 1.0):
        raise SystemExit(f"FAIL: priority outside [0,1]: {priority.min()}-{priority.max()}")

    scores.to_csv(OUTPUT, index=False)
    print(f"Wrote data/processed/{OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} kB)")
    print("\n  top 5 cells by Priority:")
    for _, row in scores.head(5).iterrows():
        print(f"    {row['rank']:>3}  {row['h3']}  P={row['priority']:.4f}  "
              f"H={row['hazard']:.3f} E={row['exposure']:.3f} V={row['vulnerability']:.3f}")
        print(f"         because: {row['top_reasons']}")

    (PROCESSED / "scores_weights_used.json").write_text(
        json.dumps({"dimension_exponents": exponents, "within_dimension": used_weights,
                    "missing_indicators": missing,
                    "weights_provisional": bool(weights_cfg["provisional"])}, indent=1),
        encoding="utf-8")
    return {"cells": n, "zero_priority": zero_priority, "missing": missing}


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
