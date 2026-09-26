"""P2-02: the AHP tool.

The published values checked here were verified from sources during P2-02 rather than
recalled: CI = (lambda_max - n)/(n - 1), CR = CI/RI, RI(3) = 0.58, threshold 0.10, and a
worked example in which lambda_max = 3.085771896 gives CI = 0.042885948 and CR ~= 0.074.
"""

import itertools

import numpy as np
import pytest

from pipeline.ahp import (
    CR_THRESHOLD,
    SAATY_RANDOM_INDEX,
    conflicting_judgements,
    consistency_index,
    consistency_ratio,
    evaluate,
    lambda_max,
    matrix_from_answers,
    principal_eigenvector,
    run_session,
)


def consistent_matrix(weights) -> np.ndarray:
    """A perfectly consistent matrix is by definition a_ij = w_i / w_j."""
    w = np.asarray(weights, dtype="float64")
    return w[:, None] / w[None, :]


# --- the published example and the published table ---------------------------------

def test_reproduces_the_published_worked_example():
    """lambda_max = 3.085771896, n = 3 -> CI = 0.042885948 -> CR ~= 0.074."""
    ci = consistency_index(3.085771896, 3)
    assert ci == pytest.approx(0.042885948, abs=1e-9)
    assert consistency_ratio(ci, 3) == pytest.approx(0.0739412, abs=1e-6)


def test_saaty_random_index_table():
    assert SAATY_RANDOM_INDEX == {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
                                  7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    assert CR_THRESHOLD == 0.10


def test_consistency_index_formula():
    for n in range(3, 11):
        assert consistency_index(float(n), n) == pytest.approx(0.0)
        assert consistency_index(n + (n - 1) * 0.5, n) == pytest.approx(0.5)


def test_an_unknown_matrix_size_is_refused_rather_than_guessed():
    with pytest.raises(ValueError, match="no published random index"):
        consistency_ratio(0.1, 11)


# --- a perfectly consistent matrix gives CR ~= 0 -----------------------------------

@pytest.mark.parametrize("weights", [
    [1.0, 1.0, 1.0], [0.6, 0.3, 0.1], [0.5, 0.25, 0.15, 0.10], [0.4, 0.3, 0.2, 0.07, 0.03],
])
def test_a_consistent_matrix_has_lambda_max_equal_to_n_and_cr_zero(weights):
    result = evaluate(consistent_matrix(weights))
    n = len(weights)
    assert result["lambda_max"] == pytest.approx(n, abs=1e-9)
    assert result["consistency_index"] == pytest.approx(0.0, abs=1e-9)
    assert result["consistency_ratio"] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("weights", [[0.6, 0.3, 0.1], [0.5, 0.25, 0.15, 0.10]])
def test_a_consistent_matrix_recovers_the_weights_that_built_it(weights):
    """The strongest possible check: build the matrix from known weights, then see
    whether the eigenvector returns them."""
    recovered = evaluate(consistent_matrix(weights))["weights"]
    assert np.allclose(recovered, np.array(weights) / np.sum(weights), atol=1e-9)


# --- an inconsistent matrix is caught ----------------------------------------------

def test_an_inconsistent_matrix_is_caught():
    """A contradicts itself: A beats B, B beats C, but C beats A."""
    circular = np.array([[1, 5, 1 / 5], [1 / 5, 1, 5], [5, 1 / 5, 1]], dtype="float64")
    result = evaluate(circular)
    assert result["consistency_ratio"] > CR_THRESHOLD
    assert result["lambda_max"] > 3.0


def test_mild_inconsistency_passes_the_threshold():
    """Real answers are never perfect; the threshold must not reject reasonable ones."""
    result = evaluate(np.array([[1, 3, 5], [1 / 3, 1, 3], [1 / 5, 1 / 3, 1]]))
    assert result["consistency_ratio"] < CR_THRESHOLD
    assert result["lambda_max"] == pytest.approx(3.038511, abs=1e-5)


def test_lambda_max_is_never_below_n():
    """A mathematical guarantee for positive reciprocal matrices; a violation would mean
    the eigenvector is wrong."""
    rng = np.random.default_rng(20260926)
    for _ in range(50):
        n = int(rng.integers(3, 8))
        matrix = np.ones((n, n))
        for i, j in itertools.combinations(range(n), 2):
            value = float(rng.choice([1 / 9, 1 / 5, 1 / 3, 1, 3, 5, 9]))
            matrix[i, j], matrix[j, i] = value, 1 / value
        result = evaluate(matrix)
        assert result["lambda_max"] >= n - 1e-9
        assert result["weights"].sum() == pytest.approx(1.0)
        assert (result["weights"] > 0).all()


# --- power iteration agrees with a completely different algorithm -------------------

def test_power_iteration_agrees_with_a_direct_eigen_solver():
    """Cross-validation against numpy's LAPACK solver: a much stronger check than
    matching one textbook number, because it covers 60 random matrices."""
    rng = np.random.default_rng(11)
    for _ in range(60):
        n = int(rng.integers(3, 9))
        matrix = np.ones((n, n))
        for i, j in itertools.combinations(range(n), 2):
            value = float(rng.choice([1 / 9, 1 / 7, 1 / 5, 1 / 3, 1, 3, 5, 7, 9]))
            matrix[i, j], matrix[j, i] = value, 1 / value
        mine = principal_eigenvector(matrix)
        values, vectors = np.linalg.eig(matrix)
        dominant = np.argmax(values.real)
        theirs = np.abs(vectors[:, dominant].real)
        theirs = theirs / theirs.sum()
        assert np.allclose(mine, theirs, atol=1e-8)
        assert lambda_max(matrix, mine) == pytest.approx(values[dominant].real, abs=1e-8)


def test_malformed_matrices_are_refused():
    with pytest.raises(ValueError, match="square"):
        principal_eigenvector(np.ones((2, 3)))
    with pytest.raises(ValueError, match="positive"):
        principal_eigenvector(np.array([[1.0, 0.0], [0.0, 1.0]]))


# --- the interactive session --------------------------------------------------------

def scripted(answers: list[str]):
    """Drive the interactive prompts without a terminal."""
    queue = list(answers)
    return lambda _prompt: queue.pop(0)


def test_a_consistent_session_finishes_in_one_round(capsys):
    # lack_green > dist_health (3), lack_green > dist_centre (5), dist_health > centre (3)
    result = run_session(["lack_green", "dist_health", "dist_centre"],
                         ask=scripted(["a", "3", "a", "5", "a", "3"]))
    assert result["rounds"] == 1
    assert result["consistency_ratio"] < CR_THRESHOLD
    assert result["weights"].sum() == pytest.approx(1.0)
    assert result["weights"][0] > result["weights"][1] > result["weights"][2]
    assert "CR" in capsys.readouterr().out


def test_equal_answers_give_equal_weights():
    result = run_session(["a", "b", "c"], ask=scripted(["=", "=", "="]))
    assert np.allclose(result["weights"], 1 / 3)
    assert result["consistency_ratio"] == pytest.approx(0.0, abs=1e-9)


def test_contradictory_answers_trigger_a_re_ask(capsys):
    """a over b by 9, b over c by 9, but c over a by 9 -- a loop. With three indicators
    every answer is equally implicated, so all three are asked again."""
    result = run_session(["a", "b", "c"],
                         ask=scripted(["a", "9", "b", "9", "a", "9",   # the loop
                                       "a", "3", "a", "5", "a", "3"]))  # the re-ask
    out = capsys.readouterr().out
    assert "contradict each other" in out
    assert "a loop rather than one bad answer" in out
    assert "no single one to correct" in out
    assert result["rounds"] == 2
    assert result["consistency_ratio"] < CR_THRESHOLD


def test_with_three_indicators_no_single_answer_can_be_blamed():
    """A mathematical property worth pinning, because Vulnerability has exactly three
    indicators (D19), so Samraj's real session is a 3x3. Inconsistency in a 3x3 is one
    cycle, and the eigenvector shares it equally across all three judgements."""
    from pipeline.ahp import inconsistency_is_shared
    rng = np.random.default_rng(3)
    for _ in range(25):
        answers = {pair: float(rng.choice([1 / 9, 1 / 5, 1 / 3, 2, 3, 5, 9]))
                   for pair in itertools.combinations(range(3), 2)}
        matrix = matrix_from_answers(3, answers)
        scored = conflicting_judgements(matrix, evaluate(matrix)["weights"])
        errors = [s[0] for s in scored]
        assert max(errors) - min(errors) < 1e-9, "a 3x3 should implicate all pairs equally"
        assert inconsistency_is_shared(scored)


def test_with_four_indicators_a_culprit_can_be_identified():
    """From n = 4 upward the disagreements genuinely differ, so pointing at the worst
    answer is meaningful rather than arbitrary."""
    from pipeline.ahp import inconsistency_is_shared
    answers = {(0, 1): 2.0, (0, 2): 4.0, (0, 3): 8.0,
               (1, 2): 2.0, (1, 3): 4.0, (2, 3): 1 / 9}  # the last is the odd one out
    matrix = matrix_from_answers(4, answers)
    scored = conflicting_judgements(matrix, evaluate(matrix)["weights"])
    assert not inconsistency_is_shared(scored)
    assert (scored[0][1], scored[0][2]) == (2, 3)


def test_it_refuses_to_save_weights_it_cannot_justify():
    """If the answers stay contradictory it stops rather than writing them anyway."""
    circular = ["a", "9", "b", "9", "a", "9"] + ["a", "9"] * 8
    with pytest.raises(SystemExit, match="no weights have been saved"):
        run_session(["a", "b", "c"], ask=scripted(circular), max_rounds=3)


def test_bad_input_is_re_prompted_not_crashed():
    result = run_session(["a", "b"], ask=scripted(["x", "maybe", "a", "nine", "0", "12", "4"]))
    assert result["weights"][0] > result["weights"][1]


def test_conflicting_judgements_reports_every_pair_with_its_implied_value():
    answers = {(0, 1): 3.0, (0, 2): 5.0, (1, 2): 1 / 7}
    matrix = matrix_from_answers(3, answers)
    weights = evaluate(matrix)["weights"]
    worst = conflicting_judgements(matrix, weights)
    assert len(worst) == 3
    for error, i, j, given, implied in worst:
        assert error >= 1.0
        assert given == pytest.approx(matrix[i, j])
        assert implied == pytest.approx(weights[i] / weights[j])


def test_matrix_from_answers_is_reciprocal():
    matrix = matrix_from_answers(3, {(0, 1): 3.0, (0, 2): 5.0, (1, 2): 2.0})
    assert np.allclose(matrix * matrix.T, 1.0)
    assert np.allclose(np.diag(matrix), 1.0)


# --- points raised by the second independent checker --------------------------------

def test_the_three_checker_matrices_reproduce():
    """Independently re-derived by a checker subagent from the written spec alone."""
    m1 = evaluate(np.array([[1, 3, 5], [1 / 3, 1, 3], [1 / 5, 1 / 3, 1]]))
    assert np.allclose(m1["weights"], [0.6369855717, 0.2582849944, 0.1047294339], atol=1e-9)
    assert m1["lambda_max"] == pytest.approx(3.038511090558, abs=1e-9)
    assert m1["consistency_ratio"] == pytest.approx(0.0331992, abs=1e-6)

    m2 = evaluate(np.array([[1, 5, 1 / 5], [1 / 5, 1, 5], [5, 1 / 5, 1]]))
    assert np.allclose(m2["weights"], 1 / 3), "a circulant matrix gives a three-way tie"
    assert m2["lambda_max"] == pytest.approx(6.2, abs=1e-9), "the common row sum"
    assert m2["consistency_ratio"] > 1.0, "worse than an average random matrix"

    m3 = evaluate(np.array([[1, 2, 4, 8], [1 / 2, 1, 2, 4], [1 / 4, 1 / 2, 1, 2],
                            [1 / 8, 1 / 4, 1 / 2, 1]]))
    assert np.allclose(m3["weights"], np.array([8, 4, 2, 1]) / 15, atol=1e-9)
    assert m3["lambda_max"] == pytest.approx(4.0, abs=1e-9)


def test_a_uniform_weight_vector_hides_a_catastrophic_matrix():
    """M2 says a beats b by 5, b beats c by 5, c beats a by 5. The weights come back a
    perfect three-way tie and look entirely reasonable. Only CR catches it -- which is
    the argument for why the consistency check is not optional."""
    result = evaluate(np.array([[1, 5, 1 / 5], [1 / 5, 1, 5], [5, 1 / 5, 1]]))
    assert np.allclose(result["weights"], 1 / 3)
    assert result["consistency_ratio"] > result["threshold"]


def test_consistency_index_is_never_negative():
    """lambda_max >= n is a theorem, but floating point can return 3.9999999999999996."""
    assert consistency_index(3.9999999999999996, 4) == 0.0
    assert consistency_index(2.9999999999, 3) == 0.0


def test_the_collatz_wielandt_bracket_certifies_convergence():
    """min_i (Aw)_i/w_i <= lambda_max <= max_i, for any positive w. A tight bracket is
    real evidence of convergence; an iteration count is not."""
    result = evaluate(np.array([[1, 3, 5], [1 / 3, 1, 3], [1 / 5, 1 / 3, 1]]))
    low, high = result["bracket"]
    assert low <= result["lambda_max"] <= high
    assert result["bracket_width"] < 1e-9


def test_at_n_equals_three_the_eigenvector_is_the_row_geometric_mean():
    """A sharp regression test: it catches sign, normalisation and eigenvalue-selection
    bugs at once. It holds ONLY at n = 3, and the next test documents that boundary."""
    rng = np.random.default_rng(42)
    for _ in range(30):
        matrix = np.ones((3, 3))
        for i, j in itertools.combinations(range(3), 2):
            value = float(rng.choice([1 / 9, 1 / 5, 1 / 3, 2, 3, 5, 9]))
            matrix[i, j], matrix[j, i] = value, 1 / value
        geometric = np.exp(np.log(matrix).mean(axis=1))
        geometric = geometric / geometric.sum()
        assert np.allclose(principal_eigenvector(matrix), geometric, atol=1e-9)


def test_that_coincidence_does_not_survive_to_n_equals_four():
    """Documents the boundary: do not assume the n = 3 properties hold if indicators
    are ever added back."""
    matrix = np.array([[1, 9, 3, 1 / 5], [1 / 9, 1, 5, 3], [1 / 3, 1 / 5, 1, 7],
                       [5, 1 / 3, 1 / 7, 1]])
    geometric = np.exp(np.log(matrix).mean(axis=1))
    geometric = geometric / geometric.sum()
    assert not np.allclose(principal_eigenvector(matrix), geometric, atol=1e-3)


def test_kappa_is_the_whole_inconsistency_story_at_n_three():
    """lambda_max, CI and CR are all functions of kappa = a01*a12/a02 alone."""
    from pipeline.ahp import inconsistency_kappa
    consistent = np.array([[1, 3, 9], [1 / 3, 1, 3], [1 / 9, 1 / 3, 1]])
    assert inconsistency_kappa(consistent) == pytest.approx(1.0)
    assert evaluate(consistent)["consistency_ratio"] == pytest.approx(0.0, abs=1e-9)
    # two different matrices with the same kappa must give the same CR
    a = matrix_from_answers(3, {(0, 1): 2.0, (1, 2): 3.0, (0, 2): 5.0})
    b = matrix_from_answers(3, {(0, 1): 3.0, (1, 2): 2.0, (0, 2): 5.0})
    assert inconsistency_kappa(a) == pytest.approx(inconsistency_kappa(b))
    assert evaluate(a)["consistency_ratio"] == pytest.approx(evaluate(b)["consistency_ratio"])


def test_graduated_threshold_follows_saatys_own_guidance():
    """D22: Saaty published 0.05 for n=3 and 0.08 for n=4, not a flat 0.10."""
    from pipeline.ahp import cr_threshold
    assert cr_threshold(3) == 0.05
    assert cr_threshold(4) == 0.08
    assert cr_threshold(5) == 0.10 == CR_THRESHOLD


def test_a_non_reciprocal_matrix_is_refused():
    """Someone typing 0.33 for 1/3 would manufacture inconsistency that was never in the
    judgements, so the input is validated rather than trusted."""
    from pipeline.ahp import validate_matrix
    with pytest.raises(ValueError, match="reciprocal"):
        validate_matrix(np.array([[1.0, 3.0], [0.33, 1.0]]))
    with pytest.raises(ValueError, match="diagonal"):
        validate_matrix(np.array([[2.0, 3.0], [1 / 3, 1.0]]))


def test_n_of_two_is_always_consistent_and_never_divides_by_zero():
    """RI(2) is 0.00, so a naive CI/RI would raise or return nan."""
    for value in (1.0, 3.0, 9.0):
        result = evaluate(np.array([[1.0, value], [1 / value, 1.0]]))
        assert result["lambda_max"] == pytest.approx(2.0, abs=1e-9)
        assert result["consistency_ratio"] == 0.0
