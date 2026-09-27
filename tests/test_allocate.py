"""P4-01: the allocation solvers.

Every problem here is SYNTHETIC. That is the point: the answers are known on paper,
so these tests check the arithmetic rather than agreeing with whatever the real data
happens to produce. The two worked examples are written out in docs/allocation.md so
Samraj can solve them himself and compare.
"""

import numpy as np
import pytest

from pipeline.allocate import (
    Plan,
    distance_matrix,
    equity_floor,
    largest_remainder,
    need_units,
    objective_value,
    solve_greedy,
    solve_lp,
    top_quintile,
)

D = 5000.0
EPS = 0.001


# --- SYNTHETIC example A: scarce stock (docs/allocation.md section 4) ----------------

EXAMPLE_A = dict(
    priority=np.array([0.9, 0.6, 0.3]),
    need=np.array([80.0, 90.0, 50.0]),
    stock=np.array([100.0, 60.0]),
    dist=np.array([[1000.0, 4000.0],
                   [2000.0, 1000.0],
                   [6000.0, 2000.0]]),
)

# --- SYNTHETIC example B: the trap greedy falls into (section 5) ---------------------

EXAMPLE_B = dict(
    priority=np.array([0.9, 0.8]),
    need=np.array([10.0, 10.0]),
    stock=np.array([10.0, 10.0]),
    dist=np.array([[1000.0, 2000.0],
                   [1000.0, 6000.0]]),
)


def random_problem(rng, n_cells=12, n_centres=4):
    """A SYNTHETIC problem with a plausible shape: most cells reachable, stock scarce."""
    priority = rng.uniform(0.05, 1.0, n_cells)
    need = np.round(rng.uniform(0, 200, n_cells))
    stock = np.round(rng.uniform(0, 300, n_centres))
    dist = rng.uniform(200, 7000, (n_cells, n_centres))
    return dict(priority=priority, need=need, stock=stock, dist=dist)


# --- the seven checks PROMPT.md section 8 asks for -----------------------------------


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("seed", range(25))
def test_stock_is_never_exceeded(solver, seed):
    problem = random_problem(np.random.default_rng(seed))
    plan = solver(**problem, max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    assert np.all(plan.dispatched <= problem["stock"] + 1e-9), (
        f"{plan.method} sent more than a centre had: "
        f"{plan.dispatched} vs stock {problem['stock']}")


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("seed", range(25))
def test_nobody_receives_more_than_they_need(solver, seed):
    problem = random_problem(np.random.default_rng(seed))
    plan = solver(**problem, max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    assert np.all(plan.delivered <= problem["need"] + 1e-9)


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("seed", range(25))
def test_nothing_is_sent_beyond_the_service_distance(solver, seed):
    problem = random_problem(np.random.default_rng(seed))
    plan = solver(**problem, max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    assert not np.any(plan.x[problem["dist"] > D] > 0), (
        f"{plan.method} sent supply further than {D:,.0f} m")


@pytest.mark.parametrize("seed", range(25))
def test_the_lp_is_never_worse_than_greedy(seed):
    """Greedy's plan is a feasible point of the LP, so the LP's optimum must beat it.

    Compared on the continuous LP, which is the guaranteed statement. Rounding to
    whole units is a separate step and gets its own test below.
    """
    problem = random_problem(np.random.default_rng(seed))
    lp = solve_lp(**problem, max_distance_m=D, epsilon=EPS, round_units=False)
    greedy = solve_greedy(**problem, max_distance_m=D, epsilon=EPS)
    assert lp.objective >= greedy.objective - 1e-6, (
        f"seed {seed}: LP {lp.objective:.4f} < greedy {greedy.objective:.4f}")


@pytest.mark.parametrize("seed", range(25))
def test_rounding_does_not_cost_the_lp_its_advantage(seed):
    """The rounded LP should still beat greedy, which is already integral."""
    problem = random_problem(np.random.default_rng(seed))
    lp = solve_lp(**problem, max_distance_m=D, epsilon=EPS)
    greedy = solve_greedy(**problem, max_distance_m=D, epsilon=EPS)
    assert lp.objective >= greedy.objective - 1e-6


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("seed", range(10))
def test_unlimited_stock_meets_all_reachable_need(solver, seed):
    problem = random_problem(np.random.default_rng(seed))
    problem["stock"] = np.full_like(problem["stock"], 1e7)
    plan = solver(**problem, max_distance_m=D, epsilon=EPS)
    reachable = (problem["dist"] <= D).any(axis=1)
    np.testing.assert_allclose(plan.delivered[reachable], problem["need"][reachable])
    assert np.all(plan.delivered[~reachable] == 0), (
        "supply reached a cell that has no centre within the service distance")


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
def test_zero_stock_sends_nothing(solver):
    problem = random_problem(np.random.default_rng(1))
    problem["stock"] = np.zeros_like(problem["stock"])
    plan = solver(**problem, max_distance_m=D, epsilon=EPS)
    assert plan.total == 0
    assert plan.objective == 0
    np.testing.assert_allclose(plan.unmet, problem["need"])


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("seed", range(5))
def test_the_same_inputs_always_give_the_same_plan(solver, seed):
    problem = random_problem(np.random.default_rng(seed))
    first = solver(**problem, max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    second = solver(**problem, max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    np.testing.assert_array_equal(first.x, second.x)
    assert first.objective == second.objective


# --- the hand solutions in docs/allocation.md ----------------------------------------


def test_example_a_matches_the_hand_solution():
    """Section 4: A gets 80 from C1; B gets 60 from C2 and 20 from C1; C gets nothing."""
    plan = solve_lp(**EXAMPLE_A, max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25)
    expected = np.array([[80.0, 0.0],
                         [20.0, 60.0],
                         [0.0, 0.0]])
    np.testing.assert_allclose(plan.x, expected)
    assert plan.objective == pytest.approx(119.964, abs=1e-6)
    np.testing.assert_allclose(plan.unmet, [0.0, 10.0, 50.0])
    assert plan.equity_shortfall == 0.0, "cell A takes 50%, well above the 25% floor"


def test_example_a_is_a_case_greedy_also_gets_right():
    """Stated in the docs, so it is tested: when every cell is reachable, greedy ties."""
    lp = solve_lp(**EXAMPLE_A, max_distance_m=D, epsilon=EPS)
    greedy = solve_greedy(**EXAMPLE_A, max_distance_m=D, epsilon=EPS)
    np.testing.assert_allclose(lp.x, greedy.x)


def test_example_b_is_where_greedy_falls_over():
    """Section 5: greedy strands cell B by spending its only centre on cell A."""
    lp = solve_lp(**EXAMPLE_B, max_distance_m=D, epsilon=EPS)
    greedy = solve_greedy(**EXAMPLE_B, max_distance_m=D, epsilon=EPS)

    np.testing.assert_allclose(lp.x, [[0.0, 10.0], [10.0, 0.0]])
    assert lp.objective == pytest.approx(16.994, abs=1e-6)

    np.testing.assert_allclose(greedy.x, [[10.0, 0.0], [0.0, 0.0]])
    assert greedy.objective == pytest.approx(8.998, abs=1e-6)

    assert lp.total == 20 and greedy.total == 10, (
        "the LP should deliver twice the supply from the same stock")


# --- the pieces --------------------------------------------------------------------


def test_the_distance_tiebreak_cannot_outweigh_priority():
    """The reason d is divided by D. With raw metres this assertion fails."""
    priority = np.array([1.0])
    dist = np.array([[D]])
    gain = objective_value(np.array([[1.0]]), priority, dist, D, EPS)
    assert gain > 0.99, (
        "a full-priority unit at the far edge of the service area should still be "
        f"worth almost 1.0, not {gain}")


def test_largest_remainder_respects_both_caps():
    x = np.array([[2.6, 1.0], [3.2, 0.9]])       # fractional total 7.7
    stock = np.array([6.0, 2.0])
    need = np.array([4.0, 5.0])
    out = largest_remainder(x, stock, need)
    assert np.all(out == np.floor(out)), "rounding must produce whole units"
    assert np.all(out.sum(axis=0) <= stock)
    assert np.all(out.sum(axis=1) <= need)
    assert out.sum() <= np.floor(x.sum())


@pytest.mark.parametrize("seed", range(25))
def test_largest_remainder_never_breaks_a_cap(seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 30, (6, 3))
    stock = x.sum(axis=0) + rng.uniform(0, 5, 3)
    need = x.sum(axis=1) + rng.uniform(0, 5, 6)
    out = largest_remainder(x, stock, need)
    assert np.all(out.sum(axis=0) <= np.floor(stock))
    assert np.all(out.sum(axis=1) <= np.floor(need))
    assert np.all(out >= 0)


def test_need_comes_from_people_not_from_priority():
    np.testing.assert_allclose(need_units(np.array([10.0, 0.0, 4.0]), 3.0),
                               [30.0, 0.0, 12.0])


def test_top_quintile_ignores_cells_with_no_need():
    priority = np.array([0.99, 0.5, 0.4, 0.3, 0.2, 0.1])
    need = np.array([0.0, 10.0, 10.0, 10.0, 10.0, 10.0])   # the top cell is empty land
    mask = top_quintile(priority, need)
    assert mask.sum() == 1
    assert mask[1], "the quintile should be cut among the five cells that have need"
    assert not mask[0], "a cell nobody lives in cannot be owed a share"


def test_top_quintile_is_empty_when_nothing_is_needed():
    assert not top_quintile(np.array([0.5, 0.2]), np.zeros(2)).any()


def test_the_equity_rule_is_soft_rather_than_infeasible():
    """The top cell is out of range of all stock. A hard floor would return nothing."""
    priority = np.array([0.95, 0.40, 0.30])
    need = np.array([100.0, 100.0, 100.0])
    stock = np.array([150.0])
    dist = np.array([[9000.0], [1000.0], [1500.0]])       # cell 0 unreachable
    plan = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25, equity_penalty=1.0)
    assert plan.total == 150, "the solver should still place all the stock it can"
    assert plan.equity_shortfall > 0, "the missed floor must be reported, not hidden"
    assert plan.notes and "no centre within the service distance" in plan.notes[0]
    assert not plan.reachable[0]


def test_distance_matrix_is_metres_inflated_by_circuity():
    # Two points about 0.01 degrees of latitude apart, near Landhi.
    cells = np.array([[67.20, 24.85]])
    centres = np.array([[67.20, 24.86]])
    straight = distance_matrix(cells, centres, circuity=1.0)[0, 0]
    inflated = distance_matrix(cells, centres, circuity=1.3)[0, 0]
    assert 1050 < straight < 1160, f"0.01 deg of latitude is about 1.11 km, got {straight}"
    assert inflated == pytest.approx(straight * 1.3)


def test_a_circuity_factor_below_one_is_refused():
    with pytest.raises(ValueError, match="circuity"):
        distance_matrix(np.array([[67.2, 24.8]]), np.array([[67.2, 24.9]]), circuity=0.9)


@pytest.mark.parametrize("bad", [
    dict(need=np.array([-1.0, 1.0])),
    dict(stock=np.array([-5.0])),
])
def test_negative_quantities_are_refused(bad):
    problem = dict(priority=np.array([0.5, 0.5]), need=np.array([1.0, 1.0]),
                   stock=np.array([1.0]), dist=np.array([[100.0], [100.0]]))
    problem.update(bad)
    with pytest.raises(ValueError):
        solve_lp(**problem, max_distance_m=D)


def test_a_plan_reports_what_it_could_not_reach():
    priority = np.array([0.9, 0.5])
    dist = np.array([[9000.0], [100.0]])
    plan = solve_lp(priority, np.array([50.0, 50.0]), np.array([500.0]), dist,
                    max_distance_m=D)
    assert isinstance(plan, Plan)
    assert list(plan.reachable) == [False, True]
    assert plan.unmet[0] == 50.0, "an unreachable cell's need is unmet, not zero"


def test_the_config_the_solver_will_run_on_is_still_marked_provisional(allocation):
    """A guard, not a preference: P4-02 must not quietly publish unverified figures."""
    assert allocation["provisional"] is True
    water = next(c for c in allocation["commodities"] if c["id"] == "water")
    assert "UNVERIFIED" in water["basis"]


# --- regressions: every defect the independent checker found in the first version ----
#
# Each of these failed before the fix. They are named after what goes wrong in the
# field, not after the line of code, because that is what a future reader needs.


def test_the_equity_rule_cannot_be_satisfied_by_withholding_supply():
    """The checker's repro. The first version left 280 of 300 units in the warehouse.

    With the floor written as a share of what gets allocated, a unit sent to a non-top
    cell cost alpha * lambda in penalty, so every cell below Priority 0.25 was worth
    not serving -- and the plan reported no shortfall at all while doing it.
    """
    priority = np.array([0.95, 0.20, 0.18, 0.16, 0.14])
    need = np.array([5.0, 100.0, 100.0, 100.0, 100.0])
    stock = np.array([300.0])
    dist = np.full((5, 1), 1000.0)

    without = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                       min_share_top_quintile=0.0)
    with_equity = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                           min_share_top_quintile=0.25, equity_penalty=1.0)

    assert without.total == 300
    assert with_equity.total == 300, (
        f"the equity rule withheld {300 - with_equity.total:,.0f} units of supply "
        "rather than deliver them to low-priority cells")


@pytest.mark.parametrize("seed", range(40))
def test_the_equity_rule_never_reduces_how_much_is_delivered(seed):
    """The general form: turning equity on may move supply, but never shrink it."""
    problem = random_problem(np.random.default_rng(seed))
    off = solve_lp(**problem, max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.0)
    on = solve_lp(**problem, max_distance_m=D, epsilon=EPS,
                  min_share_top_quintile=0.25, equity_penalty=1.0)
    assert on.total >= off.total - 1e-6, (
        f"seed {seed}: equity cut delivery from {off.total:,.0f} to {on.total:,.0f}")


def test_a_cell_just_below_the_share_is_still_worth_serving():
    """The old cutoff sat exactly at alpha * lambda = 0.25. Priority 0.249 was dropped."""
    priority = np.array([0.95, 0.249])
    need = np.array([5.0, 100.0])
    stock = np.array([300.0])
    dist = np.full((2, 1), 1000.0)
    plan = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25, equity_penalty=1.0)
    assert plan.delivered[1] == 100.0, "an ordinary low-priority cell must still be served"


def test_the_shortfall_note_gives_the_real_reason():
    """It used to assert the top cells were out of range even when they plainly were not.

    Here every cell is 1,000 m from the only centre. The floor is unreachable purely
    because the top cell's own need is 1 unit. A brief repeating "not reachable" would
    send someone to solve a distance problem that does not exist.
    """
    priority = np.full(5, 0.9)
    need = np.array([1.0, 100.0, 100.0, 100.0, 100.0])
    stock = np.array([300.0])
    dist = np.full((5, 1), 1000.0)
    plan = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25, equity_penalty=1.0)

    assert plan.reachable.all()
    assert plan.equity_shortfall > 0
    note = plan.notes[0]
    assert "already fully met" in note, note
    assert "service distance" not in note, f"claims a distance problem that is absent: {note}"


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
def test_an_out_of_range_distance_written_as_infinity_does_not_poison_the_objective(solver):
    """inf * 0 is nan, and every comparison against nan is False.

    Summing the distance cost over the whole matrix turned one unservable pair into a
    nan objective -- so "did the LP beat greedy?" would have quietly answered no.
    """
    priority = np.array([0.9, 0.8])
    need = np.array([10.0, 10.0])
    stock = np.array([10.0, 10.0])
    dist = np.array([[1000.0, np.inf], [1000.0, np.inf]])
    plan = solver(priority, need, stock, dist, max_distance_m=D, epsilon=EPS)
    assert np.isfinite(plan.objective), f"{plan.method} objective is {plan.objective}"
    assert plan.objective > 0
    assert not np.any(plan.x[:, 1] > 0), "nothing may be sent to an unreachable centre"


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
def test_both_solvers_refuse_the_same_malformed_input(solver):
    """Greedy is the browser-side path, so malformed input reaches it first."""
    good = dict(priority=np.array([0.5, 0.5]), need=np.array([1.0, 1.0]),
                stock=np.array([1.0]), dist=np.array([[100.0], [100.0]]))

    with pytest.raises(ValueError, match="non-negative"):
        solver(**{**good, "stock": np.array([-5.0])}, max_distance_m=D)
    with pytest.raises(ValueError, match="one entry per cell"):
        solver(**{**good, "need": np.array([1.0])}, max_distance_m=D)
    with pytest.raises(ValueError, match="one entry per centre"):
        solver(**{**good, "stock": np.array([1.0, 1.0])}, max_distance_m=D)
    with pytest.raises(ValueError, match="nan"):
        solver(**{**good, "dist": np.array([[100.0], [np.nan]])}, max_distance_m=D)
    with pytest.raises(ValueError, match="max_distance_m must be positive"):
        solver(**good, max_distance_m=0)
    with pytest.raises(ValueError, match="farther"):
        solver(**good, max_distance_m=D, epsilon=-0.001)


def test_rounding_refuses_a_plan_that_is_already_infeasible():
    """floor(9.7) is 9, which is still 4.5x over a stock of 2. Rounding cannot fix that."""
    with pytest.raises(ValueError, match="already exceeds"):
        largest_remainder(np.array([[9.7]]), stock=np.array([2.0]), need=np.array([100.0]))


@pytest.mark.parametrize("seed", range(25))
def test_rounding_never_returns_more_than_it_was_given(seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 30, (6, 3))
    out = largest_remainder(x, stock=x.sum(axis=0) + 5, need=x.sum(axis=1) + 5)
    assert out.sum() <= np.floor(x.sum()) + 1e-9, (
        f"rounding turned {x.sum():.2f} units of plan into {out.sum():.0f}")


def test_the_equity_floor_is_a_fixed_quantity_not_a_share_of_the_decision():
    """D27. The floor must not depend on anything the solver chooses."""
    need = np.array([10.0, 10.0, 10.0])
    stock = np.array([12.0])
    top = np.array([True, False, False])
    assert equity_floor(need, stock, top, 0.25) == pytest.approx(0.25 * 12)   # stock binds
    assert equity_floor(need, np.array([100.0]), top, 0.25) == pytest.approx(0.25 * 30)
    assert equity_floor(need, stock, np.zeros(3, bool), 0.25) == 0.0
