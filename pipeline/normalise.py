"""P2-01: normalise each indicator to 0-1, where 1 always means more risk.

Two methods, both implemented because the sensitivity analysis (section 7) swaps between
them. D5 chose robust min-max as the headline; percentile rank is the alternative.

Rules that apply to both:
  * `direction` +1 means a higher raw value is more risk; -1 flips the result.
  * Missing values stay missing. They are excluded from percentiles and ranks rather
    than imputed, because inventing a value would invent evidence (section 2.1).
  * A constant indicator becomes 0 for every cell, with a warning (section 7). Zero, not
    0.5: an indicator that does not vary distinguishes nothing, so it should contribute
    nothing rather than contribute a constant middling amount.

Run:
    uv run python -m pipeline.normalise
"""

from __future__ import annotations

import warnings

import numpy as np

# Relative, not absolute: an absolute 1e-12 would call a column of values around 1e9
# constant only if it were truly identical, but would miss a column whose spread is
# genuine yet tiny relative to its magnitude. Scaled by the magnitude of the range.
CONSTANT_TOLERANCE = 1e-12


def _is_constant(low: float, high: float) -> bool:
    return (high - low) <= CONSTANT_TOLERANCE * max(1.0, abs(high), abs(low))


class ConstantIndicatorWarning(UserWarning):
    """Raised when an indicator has no spread and therefore carries no information."""


class FlatCoreWarning(UserWarning):
    """The 5th-95th percentile band is flat but the tails are not.

    Robust min-max would map every cell to 0 and silently discard variation that exists
    only in the clipped tails. Worth saying out loud rather than swallowing.
    """


def _as_float(values) -> np.ndarray:
    array = np.asarray(values, dtype="float64")
    if array.ndim != 1:
        raise ValueError("normalisation works on one indicator at a time")
    return array


def _apply_direction(scaled: np.ndarray, direction: int) -> np.ndarray:
    if direction == 1:
        return scaled
    if direction == -1:
        return 1.0 - scaled
    raise ValueError(f"direction must be +1 or -1, not {direction!r}")


def _constant(array: np.ndarray, name: str) -> np.ndarray:
    """Section 7: a constant indicator becomes 0, with a warning.

    The direction flip is deliberately NOT applied here. Applying it would turn a
    constant indicator with direction -1 into 1.0 everywhere -- maximum risk in every
    cell -- which is the opposite of "contributes nothing". This short-circuit is the
    intended reading of the rule and is pinned by a test.
    """
    warnings.warn(
        f"indicator {name!r} is constant across every cell with a value, so it "
        f"distinguishes nothing and is normalised to 0 (section 7)",
        ConstantIndicatorWarning, stacklevel=3)
    return np.where(np.isfinite(array), 0.0, np.nan)


def robust_minmax(values, *, direction: int = 1, low_percentile: float = 5,
                  high_percentile: float = 95, name: str = "indicator") -> np.ndarray:
    """Clip at the given percentiles, then scale linearly to 0-1 (D5)."""
    array = _as_float(values)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return np.full(array.shape, np.nan)

    low = float(np.percentile(finite, low_percentile))
    high = float(np.percentile(finite, high_percentile))
    if _is_constant(low, high):
        if not _is_constant(float(finite.min()), float(finite.max())):
            warnings.warn(
                f"indicator {name!r} is flat between the {low_percentile}th and "
                f"{high_percentile}th percentiles but varies in the tails "
                f"({finite.min():.6g} to {finite.max():.6g}); robust min-max discards that "
                f"variation, so percentile rank may suit this indicator better",
                FlatCoreWarning, stacklevel=2)
        return _constant(array, name)

    clipped = np.clip(array, low, high)
    scaled = (clipped - low) / (high - low)
    return _apply_direction(scaled, direction)


def percentile_rank(values, *, direction: int = 1, name: str = "indicator") -> np.ndarray:
    """Rank position scaled to 0-1. Ties share the average rank, so equal inputs give
    equal outputs -- otherwise the order they happened to arrive in would matter."""
    from scipy.stats import rankdata

    array = _as_float(values)
    mask = np.isfinite(array)
    if mask.sum() == 0:
        return np.full(array.shape, np.nan)
    finite = array[mask]
    if _is_constant(float(finite.min()), float(finite.max())):
        return _constant(array, name)
    if finite.size == 1:
        out = np.full(array.shape, np.nan)
        out[mask] = 0.0
        return out

    ranks = rankdata(finite, method="average")
    scaled_finite = (ranks - 1.0) / (finite.size - 1.0)
    out = np.full(array.shape, np.nan)
    out[mask] = _apply_direction(scaled_finite, direction)
    return out


METHODS = {"robust_minmax": robust_minmax, "percentile_rank": percentile_rank}


def normalise(values, *, method: str, direction: int = 1, name: str = "indicator",
              low_percentile: float = 5, high_percentile: float = 95) -> np.ndarray:
    if method not in METHODS:
        raise ValueError(f"unknown method {method!r}; expected one of {sorted(METHODS)}")
    if method == "robust_minmax":
        return robust_minmax(values, direction=direction, name=name,
                             low_percentile=low_percentile, high_percentile=high_percentile)
    return percentile_rank(values, direction=direction, name=name)


def main() -> int:
    """Normalise the real indicator table with both methods and report the difference."""
    import pandas as pd

    from pipeline.config import PROCESSED, load

    model = load("model")["normalisation"]
    indicators = load("indicators")["indicators"]
    column_for = {"lst_day_mean": "lst_mean_c", "population": "population",
                  "lack_green": "lack_green", "dist_health": "dist_health_m",
                  "dist_centre": "dist_centre_m"}

    frame = pd.read_parquet(PROCESSED / "indicators.parquet")
    out = frame[["h3"]].copy()
    print(f"{'indicator':<16}{'method':<17}{'min':>7}{'median':>9}{'max':>7}   note")
    for indicator in indicators:
        column = column_for[indicator["id"]]
        raw = frame[column].to_numpy(dtype="float64", na_value=np.nan)
        if not np.isfinite(raw).any():
            print(f"{indicator['id']:<16}{'-':<17}{'':>7}{'':>9}{'':>7}   skipped: no values yet")
            continue
        if indicator.get("transform") == "log1p":
            # Note: log1p is strictly increasing, so it changes nothing under percentile
            # rank -- it is a no-op there, verified to 0.0 difference. It matters only for
            # robust min-max, where spacing is preserved. Kept in one place so the two
            # branches see identical input.
            raw = np.log1p(raw)
        for method in (model["method"], model["alternative"]):
            scaled = normalise(raw, method=method, direction=indicator["direction"],
                               name=indicator["id"],
                               low_percentile=model["clip_low_percentile"],
                               high_percentile=model["clip_high_percentile"])
            suffix = "" if method == model["method"] else "_rank"
            out[f"{indicator['id']}_n{suffix}"] = scaled
            finite = scaled[np.isfinite(scaled)]
            note = "log1p first" if indicator.get("transform") == "log1p" else ""
            print(f"{indicator['id']:<16}{method:<17}{finite.min():>7.3f}"
                  f"{np.median(finite):>9.3f}{finite.max():>7.3f}   {note}")

    from scipy.stats import spearmanr
    print("\nAgreement between the two methods, per indicator (Spearman rho):")
    for indicator in indicators:
        a, b = f"{indicator['id']}_n", f"{indicator['id']}_n_rank"
        if a in out and b in out:
            rho = spearmanr(out[a], out[b], nan_policy="omit").statistic
            print(f"   {indicator['id']:<16}{rho:>7.4f}")

    path = PROCESSED / "indicators_normalised.csv"
    out.to_csv(path, index=False)
    print(f"\nWrote data/processed/{path.name} ({path.stat().st_size / 1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
