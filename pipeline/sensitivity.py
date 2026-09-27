"""P2-04: how much does a cell's rank depend on choices nobody can pin down exactly?

A seeded Monte Carlo re-runs the whole score with the arbitrary parts jittered:
  * the Vulnerability weights, drawn from a Dirichlet centred on the chosen weights;
  * the three dimension exponents, jittered around 1/3 (D6/D7a fix them, but the
    sensitivity analysis must show the ranking does not hinge on that choice);
  * the normalisation method, swapped between robust min-max and percentile rank.

Run:
    uv run python -m pipeline.sensitivity
"""

from __future__ import annotations

import json
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pipeline.config import ARTIFACTS, PROCESSED, load  # noqa: E402
from pipeline.normalise import normalise  # noqa: E402
from pipeline.score import (  # noqa: E402
    COLUMN_FOR,
    IncompleteDimensionWarning,
    apply_structural_zero,
    dimension_score,
    weighted_geometric_mean,
)

OUTPUT = PROCESSED / "confidence.csv"
FIGURE = ARTIFACTS / "sensitivity.png"
TOP_FRACTION = 0.20


def precompute(frame: pd.DataFrame, indicators: list[dict], model: dict
               ) -> dict[str, dict[str, np.ndarray]]:
    """Normalise every indicator under both methods once; weights do not affect this."""
    norm = model["normalisation"]
    out: dict[str, dict[str, np.ndarray]] = {}
    for method in (norm["method"], norm["alternative"]):
        values = {}
        for indicator in indicators:
            raw = frame[COLUMN_FOR[indicator["id"]]].to_numpy(dtype="float64", na_value=np.nan)
            if not np.isfinite(raw).any():
                continue
            if indicator.get("transform") == "log1p":
                raw = np.log1p(raw)
            scaled = normalise(
                raw, method=method, direction=indicator["direction"], name=indicator["id"],
                low_percentile=norm["clip_low_percentile"],
                high_percentile=norm["clip_high_percentile"])
            # D23 applies here too. Without it, percentile rank gave the 21 empty cells
            # exposure 0.0379 in half the draws, so they outranked real residents and
            # widened everyone's intervals, while the headline score (score.py) was fine.
            values[indicator["id"]] = apply_structural_zero(scaled, frame, indicator)
        out[method] = values
    return out


def one_draw(values: dict[str, np.ndarray], weights_cfg: dict, floors: dict,
             v_weights: dict[str, float], exponents: dict[str, float], n: int) -> np.ndarray:
    parts = {}
    for dimension in ("hazard", "exposure", "vulnerability"):
        base = v_weights if dimension == "vulnerability" else weights_cfg[dimension]
        score, _ = dimension_score(values, base, dimension, n)
        floor = floors.get(dimension)
        parts[dimension] = np.maximum(score, float(floor)) if floor is not None else score
    return weighted_geometric_mean(parts, exponents)


def build() -> dict[str, object]:
    model = load("model")
    cfg = model["sensitivity"]
    weights_cfg = load("weights")
    indicators = load("indicators")["indicators"]
    frame = pd.read_parquet(PROCESSED / "indicators.parquet")
    n_cells = len(frame)
    n_draws = int(cfg["n"])
    alpha = float(cfg["dirichlet_concentration"])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", IncompleteDimensionWarning)
        precomputed = precompute(frame, indicators, model)
        methods = list(precomputed)

        # The vulnerability weights that actually exist (dist_centre has no data yet).
        available = [k for k in weights_cfg["vulnerability"] if k in precomputed[methods[0]]]
        base_v = np.array([weights_cfg["vulnerability"][k] for k in available], dtype="float64")
        base_v = base_v / base_v.sum()
        base_exponents = np.array([weights_cfg["dimensions"][d]
                                   for d in ("hazard", "exposure", "vulnerability")])

        rng = np.random.default_rng(int(cfg["seed"]))
        ranks = np.empty((n_draws, n_cells), dtype="int32")
        priorities = np.empty((n_draws, n_cells), dtype="float64")
        method_used = []
        for draw in range(n_draws):
            method = methods[draw % len(methods)]          # stratified, not random
            method_used.append(method)
            v_draw = rng.dirichlet(alpha * base_v)
            exponent_draw = (rng.dirichlet(alpha * base_exponents)
                             if cfg["vary_dimension_exponents"] else base_exponents)
            priority = one_draw(
                precomputed[method], weights_cfg, model["aggregation"]["floor"],
                dict(zip(available, v_draw, strict=True)),
                dict(zip(("hazard", "exposure", "vulnerability"), exponent_draw, strict=True)),
                n_cells)
            ranks[draw] = pd.Series(priority).rank(ascending=False, method="min").to_numpy()
            priorities[draw] = priority
        # The score is far better behaved than the rank: rank is competitive, so a cell
        # moves when OTHER cells move, and the priority curve is nearly flat through the
        # middle of the ranking.
        priority_low = np.percentile(priorities, 5, axis=0)
        priority_high = np.percentile(priorities, 95, axis=0)

    top_n = int(np.ceil(TOP_FRACTION * n_cells))

    def summarise(subset: np.ndarray) -> dict[str, np.ndarray]:
        return {"p": (subset <= top_n).mean(axis=0),
                "median": np.median(subset, axis=0),
                "low": np.percentile(subset, 5, axis=0, method="nearest"),
                "high": np.percentile(subset, 95, axis=0, method="nearest")}

    pooled = summarise(ranks)
    by_method = {m: summarise(ranks[[i for i, u in enumerate(method_used) if u == m]])
                 for m in methods}
    # Monte Carlo standard error on a proportion. Reporting P to four decimals would
    # claim precision about 300x finer than 1000 draws support.
    se = np.sqrt(pooled["p"] * (1 - pooled["p"]) / n_draws)
    method_gap = np.abs(by_method[methods[0]]["p"] - by_method[methods[1]]["p"])

    # Classify from the PUBLISHED (rounded) numbers, so a reader checking
    # "certainty 0.80 -> high" against the table finds it true.
    pooled["p"] = np.round(pooled["p"], 2)
    certainty = np.round(np.maximum(pooled["p"], 1.0 - pooled["p"]), 2)
    classes = cfg["confidence_classes"]

    def classify(values: np.ndarray) -> list[str]:
        return ["high" if v >= classes["high"] else "medium" if v >= classes["medium"]
                else "low" for v in values]

    def stability(values: np.ndarray) -> list[str]:
        """Directional and actionable: the 'uncertain' band is the list a human reads."""
        return ["confidently in" if v >= classes["high"]
                else "confidently out" if v <= 1 - classes["high"] else "uncertain"
                for v in values]

    scores = pd.read_csv(PROCESSED / "scores.csv").set_index("h3")
    out = pd.DataFrame({
        "h3": frame["h3"],
        "priority": scores.loc[frame["h3"], "priority"].to_numpy(),
        "rank": scores.loc[frame["h3"], "rank"].to_numpy(),
        "median_rank": pooled["median"].astype(int),
        "rank_low_5pct": pooled["low"].astype(int),
        "rank_high_95pct": pooled["high"].astype(int),
        "rank_interval_width": (pooled["high"] - pooled["low"]).astype(int),
        "priority_low_5pct": np.round(priority_low, 3),
        "priority_high_95pct": np.round(priority_high, 3),
        "p_top20": pooled["p"],
        "p_top20_se": np.round(se, 3),
        f"p_{methods[0]}": np.round(by_method[methods[0]]["p"], 2),
        f"p_{methods[1]}": np.round(by_method[methods[1]]["p"], 2),
        "method_gap": np.round(method_gap, 2),
        "stability": stability(pooled["p"]),
        "certainty": certainty,
        "confidence": classify(certainty),
        "confidence_literal": classify(pooled["p"]),
    # rank then h3: 21 cells tie at the bottom, and quicksort ordered them differently
    # on CI's Linux runner than on macOS, which broke the byte-for-byte check.
    }).sort_values(["rank", "h3"], kind="stable").reset_index(drop=True)

    print(f"Monte Carlo: {n_draws} draws, seed {cfg['seed']}, Dirichlet concentration {alpha}")
    print(f"  methods run SEPARATELY then pooled: {methods} "
          f"({method_used.count(methods[0])} / {method_used.count(methods[1])} draws)")
    print(f"  top 20% is the top {top_n} of {n_cells} cells")
    print(f"  rank interval width: median {np.median(out['rank_interval_width']):.0f}, "
          f"max {out['rank_interval_width'].max()}")
    print(f"  priority interval width: median "
          f"{np.median(out['priority_high_95pct'] - out['priority_low_5pct']):.3f} "
          f"on a 0-{out['priority'].max():.2f} scale -- far better behaved than ranks")
    print(f"  Monte Carlo standard error on P: max {se.max():.3f} "
          f"(so P is reported to 2 dp, not 4)")

    print("\n  stability of the top-20% call:")
    for label in ("confidently in", "uncertain", "confidently out"):
        count = (out["stability"] == label).sum()
        print(f"    {label:<18}{count:>4} cells ({count / n_cells * 100:>5.1f}%)")

    print("\n  THE NORMALISATION CHOICE IS NOT A DETAIL:")
    print(f"    mean |P_robust - P_percentile| = {method_gap.mean():.3f}")
    print(f"    cells where the two methods disagree by more than 0.5: "
          f"{(method_gap > 0.5).sum()}")
    print("    pooling them would hide that; they are reported separately")

    stable = out[out["rank"] <= top_n]
    print(f"\n  of the {len(stable)} cells in the headline top 20%, "
          f"{(stable['p_top20'] >= 0.8).sum()} stay there in at least 80% of draws, "
          f"and {(stable['p_top20'] < 0.5).sum()} are on the wrong side of a coin flip")

    out.to_csv(OUTPUT, index=False)
    print(f"Wrote data/processed/{OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} kB)")
    _figure(out, ranks, top_n)
    return {"draws": n_draws, "seed": int(cfg["seed"]),
            "dirichlet_concentration": alpha,
            "median_rank_interval": float(np.median(out["rank_interval_width"])),
            "median_priority_interval": round(float(np.median(
                out["priority_high_95pct"] - out["priority_low_5pct"])), 3),
            "mean_method_gap": float(method_gap.mean()),
            "confidently_in": int((out["stability"] == "confidently in").sum()),
            "uncertain": int((out["stability"] == "uncertain").sum()),
            "confidently_out": int((out["stability"] == "confidently out").sum())}


def _figure(out: pd.DataFrame, ranks: np.ndarray, top_n: int) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), dpi=110)
    order = out.sort_values("median_rank")
    axes[0].fill_between(range(len(order)), order["rank_low_5pct"], order["rank_high_95pct"],
                         alpha=0.35, color="#4c72b0", label="90% rank interval")
    axes[0].plot(range(len(order)), order["median_rank"], color="#1b3a5c", lw=1.2,
                 label="median rank")
    axes[0].axhline(top_n, color="#a6341b", ls="--", lw=1, label=f"top 20% (rank {top_n})")
    axes[0].set_xlabel("cells, ordered by median rank")
    axes[0].set_ylabel("rank (1 = highest priority)")
    axes[0].invert_yaxis()
    axes[0].legend(fontsize=8)
    axes[0].set_title("How much each cell's rank moves", fontsize=10)

    axes[1].hist(out["p_top20"], bins=25, color="#4c72b0", edgecolor="white")
    axes[1].set_xlabel("probability of being in the top 20%")
    axes[1].set_ylabel("cells")
    axes[1].set_title("Most cells are decisively in or out", fontsize=10)

    axes[2].scatter(out["rank"], out["rank_interval_width"], s=9, alpha=0.6, color="#4c72b0")
    axes[2].set_xlabel("headline rank")
    axes[2].set_ylabel("width of the 90% rank interval")
    axes[2].set_title("Where the ranking is least settled", fontsize=10)
    fig.suptitle(f"Sensitivity: {ranks.shape[0]} seeded draws jittering weights, "
                 f"dimension exponents and normalisation method", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGURE)
    plt.close(fig)
    print(f"Wrote {FIGURE.name} to artifacts/")


def main() -> int:
    result = build()
    (PROCESSED / "sensitivity_meta.json").write_text(json.dumps(result, indent=1), "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
