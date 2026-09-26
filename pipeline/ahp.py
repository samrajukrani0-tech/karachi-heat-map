"""P2-02: set the Vulnerability weights by pairwise comparison (AHP).

Samraj runs this himself. It asks a short series of plain-English questions, turns his
answers into weights as the principal eigenvector of the comparison matrix, and reports
how self-consistent those answers were. If the answers contradict each other badly
(CR >= 0.10) it shows which ones conflict and asks those again.

Per D7 it weights the Vulnerability indicators ONLY. The three H/E/V dimension exponents
are fixed at 1/3 by D6 and are not AHP's business: in a multiplicative model an exponent
is an elasticity, not an importance.

Run:
    uv run python -m pipeline.ahp
"""

from __future__ import annotations

import datetime as dt
import itertools
from collections.abc import Callable

import numpy as np
import yaml

from pipeline.config import CONFIG_DIR, load

# Saaty's random index: the average consistency ratio of randomly filled reciprocal
# matrices of each size. CR compares your inconsistency against random noise.
SAATY_RANDOM_INDEX = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
                      7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
CR_THRESHOLD = 0.10
# Saaty published a graduated threshold rather than a flat 0.10: stricter for small
# matrices, because with few items there is little redundancy for inconsistency to show
# up in. Vulnerability has exactly three indicators (D19), so the n = 3 value is the one
# that applies here. See DECISIONS.md D22.
CR_THRESHOLD_BY_N = {3: 0.05, 4: 0.08}


def cr_threshold(n: int) -> float:
    """The consistency ratio a matrix of this size must beat."""
    return CR_THRESHOLD_BY_N.get(n, CR_THRESHOLD)

SCALE = {
    1: "equally important",
    2: "very slightly more important",
    3: "moderately more important",
    4: "moderately to strongly more important",
    5: "strongly more important",
    6: "strongly to very strongly more important",
    7: "very strongly more important",
    8: "very strongly to extremely more important",
    9: "extremely more important",
}


def principal_eigenvector(matrix: np.ndarray, tolerance: float = 1e-12,
                          max_iterations: int = 10_000) -> np.ndarray:
    """Principal eigenvector by power iteration, normalised to sum to 1.

    A positive reciprocal matrix has a single dominant real eigenvalue (Perron-Frobenius),
    so repeatedly multiplying any positive vector by the matrix converges to its
    eigenvector -- the other components shrink by the ratio of the eigenvalues each pass.
    """
    matrix = np.asarray(matrix, dtype="float64")
    n = matrix.shape[0]
    if matrix.shape != (n, n):
        raise ValueError("comparison matrix must be square")
    if np.any(matrix <= 0):
        raise ValueError("every comparison must be positive")

    vector = np.full(n, 1.0 / n)
    for _ in range(max_iterations):
        nxt = matrix @ vector
        total = nxt.sum()
        if total == 0 or not np.isfinite(total):
            raise ValueError("power iteration diverged; check the matrix")
        nxt = nxt / total
        if np.max(np.abs(nxt - vector)) < tolerance:
            return nxt
        vector = nxt
    raise RuntimeError("power iteration did not converge")


def validate_matrix(matrix: np.ndarray, tolerance: float = 1e-9) -> np.ndarray:
    """Reject a matrix that is not a positive reciprocal comparison matrix.

    Worth failing loudly: if reciprocity is ever entered by hand, someone types 0.33 for
    1/3 and manufactures inconsistency that was never in the judgements.
    """
    matrix = np.asarray(matrix, dtype="float64")
    n = matrix.shape[0]
    if matrix.ndim != 2 or matrix.shape != (n, n):
        raise ValueError("comparison matrix must be square")
    if not np.all(np.isfinite(matrix)) or np.any(matrix <= 0):
        raise ValueError("every comparison must be positive and finite")
    if not np.allclose(np.diag(matrix), 1.0, atol=tolerance):
        raise ValueError("the diagonal of a comparison matrix must be all ones")
    if not np.allclose(matrix * matrix.T, 1.0, atol=tolerance):
        raise ValueError("matrix is not reciprocal: a_ij * a_ji must equal 1")
    return matrix


def collatz_wielandt(matrix: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    """A certified bracket containing lambda_max, for any positive vector.

    min_i (Aw)_i/w_i <= lambda_max <= max_i (Aw)_i/w_i. The width is an honest
    convergence diagnostic -- far better evidence than trusting an iteration count.
    """
    ratios = (np.asarray(matrix, dtype="float64") @ weights) / weights
    return float(ratios.min()), float(ratios.max())


def lambda_max(matrix: np.ndarray, weights: np.ndarray) -> float:
    """The principal eigenvalue, as the mean of (Aw)_i / w_i.

    At n = 3 this is silently a two-sided Rayleigh quotient and is second-order accurate,
    because the Perron vector of a 3x3 reciprocal matrix coincides with its row geometric
    mean, whose reciprocal is the left eigenvector. That coincidence fails from n = 4, so
    do not assume this estimator stays second-order if more indicators are ever added.
    """
    matrix = np.asarray(matrix, dtype="float64")
    weighted = matrix @ weights
    return float(np.mean(weighted / weights))


def inconsistency_kappa(matrix: np.ndarray) -> float:
    """For a 3x3, the entire inconsistency in one number: kappa = a01 * a12 / a02.

    lambda_max, CI and CR are all functions of kappa alone, so it is the most direct
    statement of how far the three judgements fail to multiply through. kappa = 1 is
    perfect consistency.
    """
    matrix = np.asarray(matrix, dtype="float64")
    if matrix.shape != (3, 3):
        raise ValueError("kappa is defined here only for a 3x3 matrix")
    return float(matrix[0, 1] * matrix[1, 2] / matrix[0, 2])


def consistency_index(lmax: float, n: int) -> float:
    """CI = (lambda_max - n) / (n - 1), clamped at 0.

    lambda_max >= n is a theorem for positive reciprocal matrices, with equality exactly
    when the matrix is consistent, so CI is never truly negative. Floating point can
    still return 3.9999999999999996 for a consistent 4x4, which would print as
    "CR = -0.0000". The clamp is cosmetic, not corrective.
    """
    if n < 2:
        return 0.0
    return max((lmax - n) / (n - 1), 0.0)


def consistency_ratio(ci: float, n: int) -> float:
    """CI divided by the random index. n <= 2 is always consistent, so CR is 0."""
    random_index = SAATY_RANDOM_INDEX.get(n)
    if random_index is None:
        raise ValueError(f"no published random index for n = {n}")
    if random_index == 0:
        return 0.0
    return ci / random_index


def evaluate(matrix: np.ndarray) -> dict[str, object]:
    matrix = validate_matrix(matrix)
    n = matrix.shape[0]
    weights = principal_eigenvector(matrix)
    lmax = lambda_max(matrix, weights)
    low, high = collatz_wielandt(matrix, weights)
    if lmax < n - 1e-9:
        raise ValueError(f"lambda_max {lmax} is below n = {n}, which is impossible for a "
                         f"reciprocal matrix; the eigenvector is wrong")
    ci = consistency_index(lmax, n)
    result = {"weights": weights, "lambda_max": lmax, "n": n,
              "consistency_index": ci, "consistency_ratio": consistency_ratio(ci, n),
              "bracket": (low, high), "bracket_width": high - low,
              "threshold": cr_threshold(n)}
    if n == 3:
        result["kappa"] = inconsistency_kappa(matrix)
    return result


def inconsistency_is_shared(scored: list[tuple], tolerance: float = 1e-6) -> bool:
    """True when every judgement is implicated equally, so no single one is the culprit.

    This is always the case for a 3x3 matrix. With three items the only way to be
    inconsistent is a cycle -- you rank A over B, B over C, and C over A, or the
    strengths fail to multiply through -- and the eigenvector spreads that single
    contradiction evenly across all three answers. Re-asking "the worst" one would be
    arbitrary, so the tool says so and asks all three again.
    """
    if len(scored) < 2:
        return True
    errors = [s[0] for s in scored]
    return (max(errors) - min(errors)) <= tolerance * max(errors)


def conflicting_judgements(matrix: np.ndarray, weights: np.ndarray) -> list[tuple]:
    """Rank the judgements by how far each sits from what the weights imply.

    If the answers were perfectly consistent then a_ij would equal w_i / w_j exactly.
    The ratio a_ij * w_j / w_i measures the disagreement, so the pairs furthest from 1
    are the answers worth revisiting.
    """
    matrix = np.asarray(matrix, dtype="float64")
    n = matrix.shape[0]
    scored = []
    for i, j in itertools.combinations(range(n), 2):
        implied = weights[i] / weights[j]
        error = matrix[i, j] / implied
        scored.append((max(error, 1.0 / error), i, j, matrix[i, j], implied))
    scored.sort(reverse=True)
    return scored


def matrix_from_answers(n: int, answers: dict[tuple[int, int], float]) -> np.ndarray:
    matrix = np.ones((n, n), dtype="float64")
    for (i, j), value in answers.items():
        matrix[i, j] = value
        matrix[j, i] = 1.0 / value
    return matrix


# --- the interactive part ----------------------------------------------------------

def _default_ask(prompt: str) -> str:  # pragma: no cover - needs a terminal
    return input(prompt)


def ask_pair(names: list[str], i: int, j: int, ask: Callable[[str], str]) -> float:
    """Ask one comparison as two easy questions rather than one fiddly fraction."""
    a, b = names[i], names[j]
    print("\n  For heat harm in Landhi, which matters more?")
    print(f"    a) {a}")
    print(f"    b) {b}")
    print("    = ) they matter about equally")
    while True:
        choice = ask("  a, b, or = : ").strip().lower()
        if choice == "=":
            return 1.0
        if choice in {"a", "b"}:
            break
        print("    Please answer a, b or =.")
    print(f"\n  How much more important is {a if choice == 'a' else b}?")
    for value, label in SCALE.items():
        if value > 1:
            print(f"    {value} = {label}")
    while True:
        raw = ask("  1-9: ").strip()
        try:
            strength = int(raw)
        except ValueError:
            print("    Please enter a whole number from 1 to 9.")
            continue
        if 1 <= strength <= 9:
            break
        print("    Please enter a whole number from 1 to 9.")
    return float(strength) if choice == "a" else 1.0 / strength


def run_session(names: list[str], ask: Callable[[str], str] = _default_ask,
                max_rounds: int = 5) -> dict[str, object]:
    """Ask every pair, then re-ask the worst conflicts until CR is acceptable."""
    n = len(names)
    pairs = list(itertools.combinations(range(n), 2))
    print(f"\nSetting the Vulnerability weights for {n} indicators "
          f"({len(pairs)} comparisons).")
    answers = {pair: ask_pair(names, *pair, ask=ask) for pair in pairs}

    for round_number in range(1, max_rounds + 1):
        result = evaluate(matrix_from_answers(n, answers))
        cr = float(result["consistency_ratio"])
        threshold = float(result["threshold"])
        print(f"\n  lambda_max = {result['lambda_max']:.6f}   "
              f"CI = {result['consistency_index']:.6f}   CR = {cr:.4f}")
        if "kappa" in result:
            print(f"  Your three answers multiply out to {result['kappa']:.3g} where "
                  f"perfect agreement would be 1.")
        if cr < threshold:
            print(f"  CR is below {threshold} (Saaty's limit for {n} items): your answers "
                  f"are consistent enough.")
            result["rounds"] = round_number
            result["answers"] = answers
            return result
        if round_number == max_rounds:
            break
        worst = conflicting_judgements(matrix_from_answers(n, answers), result["weights"])
        print(f"\n  CR is {cr:.4f}, which is above {threshold}. Some answers "
              f"contradict each other.")
        if inconsistency_is_shared(worst):
            print("  With this few indicators the contradiction is a loop rather than one "
                  "bad answer:")
            for _, i, j, given, implied in worst:
                direction = f"{names[i]} over {names[j]}" if given >= 1 else \
                            f"{names[j]} over {names[i]}"
                strength = given if given >= 1 else 1 / given
                print(f"    you put {direction} by {strength:.3g}, but your other answers "
                      f"imply {implied:.3g}")
            print("  Every answer is implicated equally, so there is no single one to "
                  "correct. Let us go through them again.")
            for pair in pairs:
                answers[pair] = ask_pair(names, *pair, ask=ask)
        else:
            _, i, j, given, implied = worst[0]
            print(f"  The clearest conflict is {names[i]} vs {names[j]}: you said "
                  f"{given:.3g}, but your other answers together imply about "
                  f"{implied:.3g}.")
            print("  Let us try that one again.")
            answers[(i, j)] = ask_pair(names, i, j, ask=ask)

    raise SystemExit(
        f"CR is still {cr:.4f} (limit {threshold}) after {max_rounds} rounds. Nothing is "
        f"broken -- it means the judgements genuinely pull in different directions. Take "
        f"a break and run it again; no weights have been saved."
    )


def save_weights(names: list[str], result: dict[str, object], *, decided_by: str) -> None:
    path = CONFIG_DIR / "weights.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    weights = {name: float(w) for name, w in zip(names, result["weights"], strict=True)}
    document["vulnerability"] = weights
    document["provisional"] = False
    document["decided_by"] = decided_by
    document["decided_on"] = dt.date.today().isoformat()
    document["consistency_ratio"] = round(float(result["consistency_ratio"]), 6)
    document["lambda_max"] = round(float(result["lambda_max"]), 6)
    document["ahp_answers"] = {f"{names[i]} vs {names[j]}": round(float(v), 6)
                               for (i, j), v in result["answers"].items()}
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")
    print("\nSaved to config/weights.yaml:")
    for name, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
        print(f"    {name:<16}{weight:.4f}")


def main() -> int:  # pragma: no cover - interactive
    import argparse

    parser = argparse.ArgumentParser(description="Set the Vulnerability weights by AHP")
    parser.add_argument("--dry-run", action="store_true",
                        help="practise without writing anything to config/weights.yaml")
    args = parser.parse_args()

    indicators = [i for i in load("indicators")["indicators"]
                  if i["dimension"] == "vulnerability"]
    names = [i["id"] for i in indicators]
    print("=" * 70)
    print("AHP: setting the Vulnerability weights (D7)")
    print("=" * 70)
    print("\nYou will be asked to compare indicators two at a time. There are no wrong")
    print("answers -- the tool measures whether your answers agree with each other, and")
    print("asks again if they do not.\n")
    for indicator in indicators:
        print(f"    {indicator['id']:<16}{indicator['name_en']}")
    if args.dry_run:
        print("\n  DRY RUN: nothing will be saved. Run without --dry-run when it counts.\n")
    result = run_session(names)
    if args.dry_run:
        print("\n  Dry run finished. These weights were NOT saved:")
        for name, weight in sorted(zip(names, result["weights"], strict=True),
                                   key=lambda kv: -kv[1]):
            print(f"    {name:<16}{weight:.4f}")
        return 0
    save_weights(names, result, decided_by="Samraj")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
