"""P2-05: the validation pack.

Three checks, each labelled with exactly how much it is worth:
  (a) agreement with an equal-weights baseline (Spearman rho);
  (b) face validity against the one June 2024 incident reported inside Landhi (D14);
  (c) an expert-ranking protocol, with its analysis script tested on SYNTHETIC data only
      until Samraj brings real rankings.

Run:
    uv run python -m pipeline.validate
"""

from __future__ import annotations

import json
import warnings

import h3
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from pipeline.config import DOCS, PROCESSED, load
from pipeline.score import IncompleteDimensionWarning, dimension_score, weighted_geometric_mean
from pipeline.sensitivity import precompute

REPORT = PROCESSED / "validation.json"
FORM = DOCS / "expert-ranking-form.md"

# Candidate locations for the one June 2024 incident reported inside Landhi: "the body of
# 40-year-old Sultan was found near Landhi Hospital's Chowrangi" (Express Tribune, text
# supplied by Samraj; see QUESTIONS.md Q1). The phrase names a roundabout by a hospital
# and cannot be resolved to a single point, so every plausible reading is reported rather
# than one being chosen to look precise.
INCIDENT_CANDIDATES = {
    "Karachi Homoeopathic Medical College & Hospital": (24.8409252, 67.1946541),
    "Bismillah Chowrangi, Landhi Town": (24.8306325, 67.1714014),
    "MALC Landhi Leprosy Centre": (24.8374047, 67.1802169),
    "Landhi No 6 (town centroid of the named area)": (24.8351918, 67.1774095),
}

# Named alternative weightings. Unlike the equal-weights baseline these are informative
# right now, because the configured weights are themselves still provisional equal ones.
SCENARIOS = {
    "equal weights (the configured baseline)": {"hazard": 1 / 3, "exposure": 1 / 3,
                                                "vulnerability": 1 / 3},
    "hazard-led": {"hazard": 0.5, "exposure": 0.25, "vulnerability": 0.25},
    "exposure-led": {"hazard": 0.25, "exposure": 0.5, "vulnerability": 0.25},
    "vulnerability-led": {"hazard": 0.25, "exposure": 0.25, "vulnerability": 0.5},
}


def _priority(values, weights_cfg, floors, exponents, n):
    parts = {}
    for dimension in ("hazard", "exposure", "vulnerability"):
        score, _ = dimension_score(values, weights_cfg[dimension], dimension, n)
        floor = floors.get(dimension)
        parts[dimension] = np.maximum(score, float(floor)) if floor is not None else score
    return weighted_geometric_mean(parts, exponents)


def baseline_comparison(frame, indicators, model, weights_cfg) -> dict:
    """(a) Spearman rho against an equal-weights baseline, plus named alternatives."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", IncompleteDimensionWarning)
        values = precompute(frame, indicators, model)[model["normalisation"]["method"]]
        floors = model["aggregation"]["floor"]
        n = len(frame)
        headline = _priority(values, weights_cfg, floors, weights_cfg["dimensions"], n)
        out = {}
        for label, exponents in SCENARIOS.items():
            alt = _priority(values, weights_cfg, floors, exponents, n)
            out[label] = {"spearman": round(float(spearmanr(headline, alt).statistic), 4),
                          "kendall": round(float(kendalltau(headline, alt).statistic), 4)}
    return out


def face_validity(scores: pd.DataFrame, grid_ids: set[str], resolution: int) -> dict:
    """(b) D14: locate the single reported incident and report that cell's rank."""
    by_cell = scores.set_index("h3")
    n = len(scores)
    results = []
    for label, (lat, lon) in INCIDENT_CANDIDATES.items():
        cell = h3.latlng_to_cell(lat, lon, resolution)
        if cell not in grid_ids:
            results.append({"location": label, "cell": cell, "inside_pilot": False})
            continue
        row = by_cell.loc[cell]
        # Ranks are reported against the number of DISTINGUISHABLE positions, not the
        # cell count: 21 unpopulated cells tie at the bottom, so ranks run 1..245.
        distinguishable = int(scores["rank"].max())
        results.append({
            "location": label, "cell": cell, "inside_pilot": True,
            "rank": int(row["rank"]), "of_cells": n,
            "of_distinguishable_positions": distinguishable,
            "priority": round(float(row["priority"]), 4),
            "percentile": round(100 * (1 - (row["rank"] - 1) / (distinguishable - 1)), 1),
        })
    inside = [r for r in results if r.get("inside_pilot")]
    return {
        "incident": "one body recovered near Landhi Hospital's Chowrangi, 24 June 2024",
        "source": "Express Tribune story 2473712, text supplied by Samraj (QUESTIONS.md Q1)",
        "candidates": results,
        "ranks": sorted(r["rank"] for r in inside),
        "verdict_strength": "none -- illustrative context only",
        "why_weak": [
            "It is a single incident. There is no denominator: we observe one place where "
            "an event happened and no sample of places where it did not, so nothing "
            "distinguishes the model from chance in either direction.",
            "The location is a phrase, not a coordinate. 'Landhi Hospital's Chowrangi' "
            "resolves to several plausible points, and they rank differently.",
            "Street-death reports depend on where ambulances patrol and where bodies are "
            "found in public, so they sample reporting infrastructure, not heat harm. A "
            "body located by reference to a landmark is selected for landmark density.",
            "The observed ranks sit mid-distribution -- which is exactly what a randomly "
            "drawn cell would give. This is neither support nor refutation.",
        ],
    }


def _spearman_against(model_ranks: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Spearman of `model_ranks` against every row of `matrix`, vectorised.

    Both sides are already rankings, so Spearman is just Pearson on the values -- which
    turns 10,000 correlations into one matrix multiply instead of 10,000 scipy calls.
    """
    a = model_ranks - model_ranks.mean()
    a = a / np.linalg.norm(a)
    b = matrix - matrix.mean(axis=1, keepdims=True)
    b = b / np.linalg.norm(b, axis=1, keepdims=True)
    return b @ a


def permutation_p(model_ranks: np.ndarray, expert_ranks: np.ndarray, *,
                  draws: int = 10_000, seed: int = 20260927) -> float:
    """One-sided p: how often does a random ranking agree at least this well?

    This, not the confidence interval, is the test of "better than chance".
    """
    rng = np.random.default_rng(seed)
    observed = float(spearmanr(model_ranks, expert_ranks).statistic)
    shuffled = rng.permuted(np.tile(expert_ranks, (draws, 1)), axis=1)
    hits = int((_spearman_against(model_ranks, shuffled) >= observed - 1e-12).sum())
    return (hits + 1) / (draws + 1)


def fisher_z_interval(rho: float, n: int) -> list[float] | None:
    """Fisher-z interval. Near rho = 1 the percentile bootstrap pins against the ceiling;
    working on the transformed scale does not."""
    if n < 4 or abs(rho) >= 1.0:
        return None  # undefined at the boundary; None survives JSON, nan does not
    z = np.arctanh(rho)
    # Bonett-Wright: the Fisher transform's variance needs a correction for Spearman's
    # rho. Using the Pearson SE of 1/sqrt(n-3) gives an interval that is slightly too
    # narrow, which for a small-n field exercise is the wrong direction to be wrong in.
    se = np.sqrt(1.06 / (n - 3))
    return [round(float(np.tanh(z - 1.96 * se)), 4), round(float(np.tanh(z + 1.96 * se)), 4)]


def expert_agreement(model_ranks: list[float], expert_ranks: list[float],
                     bootstrap: int = 10_000, seed: int = 20260927) -> dict:
    """(c) Agreement between a model ranking and a field ranking, with bootstrap CIs.

    Used on SYNTHETIC data until Samraj brings real rankings back from the field.
    """
    model_ranks = np.asarray(model_ranks, dtype="float64")
    expert_ranks = np.asarray(expert_ranks, dtype="float64")
    if model_ranks.shape != expert_ranks.shape:
        raise ValueError("the two rankings must cover the same localities")
    if model_ranks.size < 3:
        raise ValueError("at least three localities are needed for a rank correlation")

    rho = float(spearmanr(model_ranks, expert_ranks).statistic)
    tau = float(kendalltau(model_ranks, expert_ranks).statistic)
    rng = np.random.default_rng(seed)
    n = model_ranks.size
    # Vectorised: resample all at once, re-rank each resample (resampling creates ties,
    # so Spearman needs midranks), then correlate row by row.
    from scipy.stats import rankdata
    idx = rng.integers(0, n, size=(bootstrap, n))
    model_draws = rankdata(model_ranks[idx], axis=1)
    expert_draws = rankdata(expert_ranks[idx], axis=1)
    usable = ((model_draws.max(axis=1) > model_draws.min(axis=1))
              & (expert_draws.max(axis=1) > expert_draws.min(axis=1)))
    a = model_draws[usable] - model_draws[usable].mean(axis=1, keepdims=True)
    b = expert_draws[usable] - expert_draws[usable].mean(axis=1, keepdims=True)
    draws = ((a * b).sum(axis=1)
             / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)))
    draws = draws[np.isfinite(draws)]
    return {
        "n_localities": int(n),
        "spearman": round(rho, 4),
        "kendall": round(tau, 4),
        "spearman_ci95": [round(float(np.percentile(draws, 2.5)), 4),
                          round(float(np.percentile(draws, 97.5)), 4)],
        "spearman_ci95_fisher": fisher_z_interval(rho, n),
        "permutation_p_one_sided": round(permutation_p(model_ranks, expert_ranks,
                                                       seed=seed), 5),
        "bootstrap_draws": int(draws.size),
        "note": ("The permutation p, not the interval, tests 'better than chance'. Near "
                 "rho = 1 the percentile bootstrap pins against the ceiling, so the "
                 "Fisher-z interval is the more honest one."),
    }


def write_form(localities: list[str]) -> None:
    lines = [
        "# Which parts of Landhi need heat support first?",
        "",
        "A one-page form for field staff. Please fill it in **before** looking at the map,",
        "so your answer is your own knowledge and not a reaction to ours.",
        "",
        "**Your role (optional):** ______________________  **Date:** ____________",
        "",
        "**Years working in Landhi (optional):** ______",
        "",
        "## The task",
        "",
        f"Below are {len(localities)} places in Landhi, with room to add more. Please put",
        "a **1** next to the one",
        "that needs drinking water, ORS and cooling support first during a heatwave, a",
        "**2** next to the second, and so on. Use every number once.",
        "",
        "There are no right answers. We are comparing your judgement with a computer",
        "model to find out where the model is wrong.",
        "",
        "| Rank | Place |",
        "|---|---|",
    ]
    lines += [f"|      | {name} |" for name in localities]
    lines += ["|      | _________________________ |"] * 13
    lines += [
        "",
        "**Please add any place we have missed.** Our list comes from OpenStreetMap,",
        "which maps only a small part of Landhi, so it is certainly incomplete. The more",
        "places on this list, the more the comparison is worth: with a dozen places the",
        "exercise can only detect very strong agreement, and about 25 are needed before",
        "it can tell a genuinely useful model apart from guesswork.",
        "",
        "## Two questions in your own words",
        "",
        "**1. What made you put your number 1 first?**",
        "",
        "_______________________________________________________________",
        "",
        "**2. Is there anything about heat in Landhi that a map built from satellite and",
        "census data would miss?**",
        "",
        "_______________________________________________________________",
        "",
        "---",
        "",
        "*Built by Samraj Lal Ukrani. This form collects no personal data. Your name is",
        "not required and will not be published.*",
        "",
    ]
    FORM.parent.mkdir(parents=True, exist_ok=True)
    FORM.write_text("\n".join(lines), encoding="utf-8")


def build() -> dict:
    model = load("model")
    weights_cfg = load("weights")
    indicators = load("indicators")["indicators"]
    area = load("area")
    frame = pd.read_parquet(PROCESSED / "indicators.parquet")
    scores = pd.read_csv(PROCESSED / "scores.csv")

    print("(a) Agreement with alternative weightings (Spearman rho):")
    comparison = baseline_comparison(frame, indicators, model, weights_cfg)
    for label, stats in comparison.items():
        print(f"    {label:<42} rho {stats['spearman']:+.4f}  tau {stats['kendall']:+.4f}")
    if weights_cfg["provisional"]:
        print("    NOTE: the configured weights ARE equal weights and are still")
        print("    provisional, so (a) is trivially 1.0 and tells us nothing yet. It")
        print("    becomes informative the moment P2-02b lands Samraj's own weights.")

    print("\n(b) Face validity against the one reported Landhi incident (D14):")
    grid_ids = set(scores["h3"])
    face = face_validity(scores, grid_ids, int(area["grid"]["resolution"]))
    for row in face["candidates"]:
        if row["inside_pilot"]:
            print(f"    {row['location'][:44]:<44} rank {row['rank']:>3} of "
                  f"{row['of_distinguishable_positions']}  priority {row['priority']:.3f}"
                  f"  (top {100 - row['percentile']:.0f}%)")
        else:
            print(f"    {row['location'][:46]:<46} falls outside the pilot area")
    print(f"    ranks across plausible readings: {face['ranks']} -- all mid-distribution.")
    print("    VERDICT: illustrative context only. One incident has no denominator, so it")
    print("    is neither support nor refutation. The expert ranking is the real test (D14).")

    print("\n(c) Expert-ranking protocol:")
    # Real named places recorded in OpenStreetMap inside the Landhi Town boundary.
    # Not invented: every one is an OSM place node with a name (section 2.1, 2.5).
    localities = ["Allah Buksh Goth", "Bagh-e-Korangi", "Future Colony", "Ilyas Goth",
                  "Korangi Sector 29", "Landhi 89 Chowk", "Landhi Sector 21",
                  "Mansehra Colony", "Muhammad Nagar", "Sharafi Goth Landhi",
                  "Sherpao Colony", "Labour Colony"]
    write_form(localities)
    print(f"    wrote docs/{FORM.name} ({len(localities)} named localities from OSM, "
          f"plus 13 blank rows)")
    print(f"    STATISTICAL POWER: with {len(localities)} localities the permutation null "
          f"sits near rho = 0.50, so only very strong")
    print("    agreement is detectable. About 25 are needed for a realistically good "
          "model; field staff are asked to add more.")
    print("    the analysis script is tested on SYNTHETIC rankings only, until real ones exist")

    baseline_status = ("not applicable yet: the configured weights ARE equal weights and "
                       "are provisional pending P2-02b, so this comparison correlates a "
                       "vector with itself and is 1.0 by construction. The question it "
                       "was meant to answer -- does the weighting choice matter? -- is "
                       "answered meanwhile by the P2-04 sensitivity analysis."
                       ) if weights_cfg["provisional"] else "computed"
    report = {"equal_weights_baseline_status": baseline_status,
              "equal_weights_and_alternatives": comparison,
              "weights_provisional": bool(weights_cfg["provisional"]),
              "face_validity": face,
              "expert_ranking": {"form": f"docs/{FORM.name}", "localities": localities,
                                 "localities_source": "OpenStreetMap place nodes inside "
                                                      "the Landhi Town boundary",
                                 "n_localities": len(localities),
                                 "power_note": ("At n = 12 the one-sided 5% permutation "
                                                "critical value is near rho = 0.50, so "
                                                "only very strong agreement is "
                                                "detectable. n = 25 is needed for 80% "
                                                "power at a true rho of 0.5."),
                                 "real_rankings_collected": False}}
    REPORT.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\nWrote data/processed/{REPORT.name}")
    return report


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
