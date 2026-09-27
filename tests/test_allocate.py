"""P4-01: the allocation solvers.

Every problem here is SYNTHETIC. That is the point: the answers are known on paper,
so these tests check the arithmetic rather than agreeing with whatever the real data
happens to produce. The two worked examples are written out in docs/allocation.md so
Samraj can solve them himself and compare.
"""

import re

import numpy as np
import pandas as pd
import pytest

from pipeline.allocate import (
    Plan,
    commodity_settings,
    distance_matrix,
    equity_floor,
    greedy_kwargs,
    largest_remainder,
    lp_kwargs,
    need_units,
    objective_value,
    solve_greedy,
    solve_lp,
    stock_holding_centres,
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
    """A guard, not a preference: P4-02 must not quietly publish unverified figures.

    Until P4-02 this asserted the basis still said UNVERIFIED. P4-02 checked the figure
    against the handbook text, so the guard now demands the citation instead -- a
    stronger condition than the placeholder it replaces, and the settings stay
    provisional (D8) until the field visit."""
    assert allocation["provisional"] is True
    water = next(c for c in allocation["commodities"] if c["id"] == "water")
    assert "UNVERIFIED" not in water["basis"]
    assert "Sphere Handbook" in water["basis"] and "p. 107" in water["basis"]


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
    assert "need only 1 between them" in note, note
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


# --- regressions: the second review, on the repaired version --------------------------


def test_the_lp_does_not_strand_supply_when_rounding_to_whole_units():
    """The checker's minimal repro. Rounding a fractional optimum gave 201, not 202.

    ``largest_remainder`` stops at the first zero remainder, so a pair the fractional
    plan left at exactly zero can never receive a freed unit -- even when both the
    centre and the cell have room. Solving the integer problem exactly removes the
    question.
    """
    priority = np.array([0.707, 0.771, 0.057, 0.733, 0.817])
    need = np.array([66.78, 9.37, 102.44, 36.92, 96.5])
    stock = np.array([75.32, 127.43])
    dist = np.array([[2323.2, 4288.8], [4722.1, 5679.1], [1828.5, 8658.5],
                     [2602.2, 2754.2], [2306.8, 607.3]])
    kw = dict(max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.5)

    assert solve_lp(priority, need, stock, dist, **kw).total == 202
    assert solve_lp(priority, need, stock, dist, exact_integers=False, **kw).total == 201


@pytest.mark.parametrize("seed", range(60))
def test_the_lp_beats_greedy_at_the_settings_the_site_will_use(seed):
    """The headline claim, tested at DEFAULTS rather than on the continuous relaxation.

    The first repair made this false in about 5% of problems: whole-unit rounding cost
    the LP more than its advantage over greedy, so the clever method shipped fewer
    litres than the paper map.
    """
    problem = random_problem(np.random.default_rng(seed))
    lp = solve_lp(**problem, max_distance_m=D, epsilon=EPS)
    greedy = solve_greedy(**problem, max_distance_m=D, epsilon=EPS)
    assert lp.objective >= greedy.objective - 1e-9, f"seed {seed}: objective"
    assert lp.total >= greedy.total - 1e-9, f"seed {seed}: units delivered"


def test_the_lp_beats_greedy_at_landhi_scale(root):
    """265 real cells, synthetic centres and stock. Small problems can hide this."""
    scores = pd.read_csv(root / "data" / "processed" / "scores.csv")
    ages = pd.read_csv(root / "data" / "processed" / "age_cells.csv")
    grid = pd.read_csv(root / "data" / "processed" / "access_cells.csv")
    frame = scores.merge(ages, on="h3").merge(grid, on="h3")
    priority = frame["priority"].to_numpy()
    need = need_units(frame["people_over60"] + frame["people_under5"], 3.0)

    rng = np.random.default_rng(0)
    n_centres = 5                                     # SYNTHETIC centres: no verified
    dist = rng.uniform(200, 9000, (len(frame), n_centres))   # centre exists yet (Q2)
    stock = np.full(n_centres, 0.35 * need.sum() / n_centres)

    lp = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                  min_share_top_quintile=0.25)
    greedy = solve_greedy(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                          min_share_top_quintile=0.25)
    assert lp.objective >= greedy.objective
    assert lp.total >= greedy.total, (
        f"the LP delivered {greedy.total - lp.total:,.0f} fewer units than greedy")
    assert np.all(lp.dispatched <= stock + 1e-9)
    assert np.all(lp.delivered <= need + 1e-9)
    assert not np.any(lp.x[dist > D] > 0)


def test_a_shortfall_is_never_reported_as_smaller_than_it_is():
    """92.5 units short printed as '92' reads low; a shortfall is rounded up."""
    priority = np.array([0.9, 0.5, 0.4, 0.3, 0.2])
    need = np.full(5, 100.0)
    stock = np.array([10.0, 400.0])
    dist = np.array([[1000.0, 9000.0]] + [[1000.0, 1000.0]] * 4)
    plan = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25)
    assert plan.equity_shortfall == pytest.approx(92.5)
    assert "93 units short of the 103" in plan.notes[0], plan.notes[0]


def test_a_large_need_does_not_make_a_real_shortfall_look_met():
    """np.allclose's relative tolerance called a 5-unit gap 'fully met' at need 1e6."""
    priority = np.array([0.9, 0.5, 0.4, 0.3, 0.2])
    need = np.full(5, 1e6)
    stock = np.array([999_995.0, 4e6])
    dist = np.array([[1000.0, 99_000.0]] + [[1000.0, 1000.0]] * 4)
    plan = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25)
    if plan.equity_shortfall > 0:
        assert "already fully met" not in plan.notes[0], plan.notes[0]


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
def test_a_negative_distance_is_refused(solver):
    """It was accepted, and the tiebreak then paid the solver to use that route."""
    with pytest.raises(ValueError, match="non-negative"):
        solver(np.array([0.9, 0.8]), np.array([10.0, 10.0]), np.array([10.0, 10.0]),
               np.array([[-1e6, 1000.0], [1000.0, 1000.0]]), max_distance_m=D)


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("field", ["priority", "need", "stock"])
@pytest.mark.parametrize("bad_value", [np.nan, np.inf])
def test_a_nan_or_infinite_input_is_refused_by_both_solvers(solver, field, bad_value):
    """Greedy accepted every one of these and returned a nan or -inf objective.

    The nan guard was added after the second review and the infinity guard was not,
    which left the exact failure objective_value's docstring says it exists to prevent:
    a nan objective makes 'did the LP beat greedy?' quietly answer no.
    """
    good = dict(priority=np.array([0.5, 0.5]), need=np.array([1.0, 1.0]),
                stock=np.array([1.0]), dist=np.array([[100.0], [100.0]]))
    bad = {**good, field: np.full_like(good[field], bad_value)}
    with pytest.raises(ValueError, match="nan or infinity"):
        solver(**bad, max_distance_m=D)


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_a_nan_or_infinite_epsilon_is_refused(solver, bad_value):
    good = dict(priority=np.array([0.5, 0.5]), need=np.array([1.0, 1.0]),
                stock=np.array([1.0]), dist=np.array([[100.0], [100.0]]))
    with pytest.raises(ValueError, match="finite|non-negative"):
        solver(**good, max_distance_m=D, epsilon=bad_value)


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
@pytest.mark.parametrize("bad_priority", [[-0.9, 0.8], [5.0, 0.8], [1.5, 0.2]])
def test_a_priority_outside_zero_to_one_is_refused(solver, bad_priority):
    """Both accepted these, and they disagreed on what a negative priority meant:
    the LP refused to serve the cell and greedy served it."""
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        solver(np.array(bad_priority), np.array([10.0, 10.0]), np.array([10.0, 10.0]),
               np.array([[100.0, 100.0], [100.0, 100.0]]), max_distance_m=D)


def test_a_penalty_below_the_tiebreak_is_refused():
    """A penalty under epsilon cannot influence the plan, yet the plan still reported
    a shortfall and blamed it on distance. 1e-4 was legal under the previous check."""
    with pytest.raises(ValueError, match="no larger than the distance tiebreak"):
        solve_lp(np.full(5, 0.6), np.full(5, 200.0), np.array([500.0]),
                 np.array([[4999.0]] + [[10.0]] * 4), max_distance_m=D, epsilon=EPS,
                 min_share_top_quintile=0.25, equity_penalty=1e-4)


def test_a_phantom_shortfall_is_not_reported():
    """Float residue is not a finding. 3.55e-15 was printed as '1 units short of 28'."""
    need = np.array([27.0, 10.54, 33.89, 31.84, 4.73])     # sums to 108.00000000000001
    plan = solve_lp(np.array([0.9, 0.5, 0.4, 0.3, 0.2]), need, np.array([208.0]),
                    np.full((5, 1), 1000.0), max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25)
    assert plan.equity_shortfall == 0.0
    assert not any("short of" in n for n in plan.notes), plan.notes


def test_the_cause_does_not_turn_on_half_a_unit_of_fractional_need():
    """need 10.4 read as 'fully met' and 10.6 as 'not enough stock' -- an arbitrary
    cliff, and on the wrong side of it the stated cause was untrue: 1,000 units sat
    1,000 m away and had been shipped. The diagnosis must not hinge on a fraction."""
    def note_for(top_need):
        need = np.array([top_need, 100.0, 100.0, 100.0, 100.0])
        plan = solve_lp(np.array([0.9, 0.5, 0.4, 0.3, 0.2]), need, np.array([1000.0]),
                        np.full((5, 1), 1000.0), max_distance_m=D, epsilon=EPS,
                        min_share_top_quintile=0.25)
        assert plan.notes, "a shortfall against an unreachable floor should be reported"
        return plan.notes[0], plan.equity_shortfall

    low, low_short = note_for(10.4)
    high, high_short = note_for(10.6)
    for note in (low, high):
        assert "the floor asks for 103 units" in note, note
        assert "need only 1" in note, note            # 10.4 and 10.6, same diagnosis
        assert "service distance" not in note, note
    assert low_short == high_short, "the shortfall must not jump across a half unit"


def test_the_lp_reports_the_shortfall_when_nothing_is_reachable_at_all():
    """The early-return branch said nothing, so the worst case was the quietest one.
    Greedy reported it on the identical input; the LP did not."""
    args = (np.array([0.9, 0.5]), np.array([10.0, 10.0]), np.array([10.0]),
            np.array([[9000.0], [9000.0]]))
    kw = dict(max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    lp, greedy = solve_lp(*args, **kw), solve_greedy(*args, **kw)
    assert lp.equity_shortfall == pytest.approx(greedy.equity_shortfall)
    assert lp.equity_shortfall == pytest.approx(2.5)
    assert any("service distance" in n for n in lp.notes), lp.notes


@pytest.mark.parametrize("bad_penalty", [0.0, -1.0, float("nan")])
def test_a_penalty_that_gives_the_floor_no_force_is_refused(bad_penalty):
    """equity_penalty=0 left the floor in the model but made it toothless, and the
    plan then reported a shortfall it had never tried to avoid."""
    with pytest.raises(ValueError, match="equity_penalty must be positive"):
        solve_lp(np.full(5, 0.6), np.full(5, 200.0), np.array([500.0]),
                 np.array([[4999.0]] + [[10.0]] * 4), max_distance_m=D,
                 min_share_top_quintile=0.25, equity_penalty=bad_penalty)


@pytest.mark.parametrize("bad_share", [1.5, -0.1, float("nan")])
def test_a_share_outside_zero_to_one_is_refused(bad_share):
    with pytest.raises(ValueError, match="share in"):
        solve_lp(np.full(3, 0.6), np.full(3, 10.0), np.array([100.0]),
                 np.full((3, 1), 100.0), max_distance_m=D,
                 min_share_top_quintile=bad_share)


def test_the_equity_rule_still_actually_shifts_supply():
    """A fix that satisfied 'never delivers less' by disabling the rule would be worse."""
    priority = np.full(5, 0.6)
    need = np.full(5, 200.0)
    stock = np.array([500.0])
    dist = np.array([[4999.0]] + [[10.0]] * 4)      # the top cell is the farthest
    off = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                   min_share_top_quintile=0.0)
    on = solve_lp(priority, need, stock, dist, max_distance_m=D, epsilon=EPS,
                  min_share_top_quintile=0.25)
    top = top_quintile(priority, need)
    assert off.delivered[top].sum() == 0, "without the rule the far cell is skipped"
    assert on.delivered[top].sum() == pytest.approx(125.0), "0.25 x min(stock, need)"
    assert on.total == off.total, "and the shift costs no delivered supply"


def test_rounding_refuses_negative_or_missing_shipments():
    with pytest.raises(ValueError, match="negative"):
        largest_remainder(np.array([[-3.0, 1.0]]), np.array([10.0, 10.0]),
                          np.array([10.0]))
    with pytest.raises(ValueError, match="nan"):
        largest_remainder(np.array([[np.nan]]), np.array([10.0]), np.array([10.0]))


# --- the config and the code must not drift apart -------------------------------------


def test_the_solver_settings_come_from_the_config_file(allocation):
    """Nothing read config/allocation.yaml. Samraj's decisions lived in a file the
    solver never opened, while solve_lp defaulted to no equity rule at all."""
    settings = lp_kwargs()
    assert settings["max_distance_m"] == allocation["service"]["max_distance_m"]
    assert settings["min_share_top_quintile"] == \
        allocation["equity"]["min_share_top_quintile"]
    assert settings["equity_penalty"] == allocation["equity"]["equity_penalty"]
    assert settings["epsilon"] == allocation["equity"]["epsilon_distance_tiebreak"]
    assert settings["exact_integers"] == allocation["solver"]["exact_integers"]
    assert commodity_settings("water")["provisional"] is True


@pytest.mark.parametrize("solver,kwargs", [(solve_lp, lp_kwargs),
                                           (solve_greedy, greedy_kwargs)])
def test_the_configured_settings_can_actually_be_passed_to_the_solver(solver, kwargs):
    """The first version mixed in the commodity rate and could not be passed to either
    solver, while its docstring said P4-02 would build every scenario through it."""
    plan = solver(np.array([0.9, 0.6, 0.3]), np.array([80.0, 90.0, 50.0]),
                  np.array([100.0, 60.0]),
                  np.array([[1000.0, 4000.0], [2000.0, 1000.0], [6000.0, 2000.0]]),
                  **kwargs())
    assert plan.total == 160
    assert np.all(plan.dispatched <= [100, 60])


def test_the_configured_water_rate_is_the_sphere_survival_figure(allocation):
    """Sphere Handbook 2018, Water supply standard 2.1 (p. 107) and Appendix 3
    (p. 145): survival water intake is 2.5-3 litres per person per day."""
    water = commodity_settings("water")
    assert 2.5 <= water["units_per_person_per_day"] <= 3.0
    assert allocation["provisional"] is True


def test_an_unknown_commodity_is_refused():
    with pytest.raises(KeyError, match="lemonade"):
        commodity_settings("lemonade")


# --- regressions: the fourth review ---------------------------------------------------


@pytest.mark.parametrize("share", [0.25, 0.5, 0.9])
@pytest.mark.parametrize("seed", range(20))
def test_the_equity_floor_never_changes_greedys_plan(share, seed):
    """Greedy's plan ignores the floor entirely, and that is a limitation, not a proof.

    An earlier version of this test justified the behaviour by arguing that priority
    order already meets any floor that can be met. **That argument is false** -- see
    test_greedy_can_miss_a_floor_the_lp_meets for a counterexample at the configured
    0.25 share, where greedy delivers 10 units to the top quintile and the LP delivers
    20 from the same stock. Serving the top cells first is not enough, because greedy
    also picks the nearest centre rather than the one that leaves the others an option.

    The behaviour is kept because PROMPT.md section 8 defines greedy as the paper-map
    baseline, and choosing centres by matching instead of proximity would make it the
    LP. What changed is the honesty of the label: greedy's shortfall is reported as its
    own, not as the achievable one.
    """
    problem = random_problem(np.random.default_rng(seed))
    base = solve_greedy(**problem, max_distance_m=D, epsilon=EPS)
    with_floor = solve_greedy(**problem, max_distance_m=D, epsilon=EPS,
                              min_share_top_quintile=share)
    np.testing.assert_array_equal(base.x, with_floor.x)


def test_the_cause_is_about_the_cells_that_are_actually_short():
    """It asked about centres in reach of ANY top cell, including fully-served ones.

    Here the short cell is cell 1, whose only in-range centre is empty; the 195 spare
    units are 9,000 m away at a centre serving cell 0. The note claimed they were
    'within reach of them, unsent'.
    """
    plan = solve_lp(np.array([0.99, 0.98, 0.5, 0.4, 0.3, 0.2]),
                    np.array([5.0, 100.0, 100.0, 100.0, 100.0, 100.0]),
                    np.array([200.0, 10.0]),
                    np.array([[1000.0, 9000.0], [9000.0, 1000.0]] + [[9000.0, 9000.0]] * 4),
                    max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    assert "not enough stock within reach" in plan.notes[0], plan.notes[0]


def test_sub_unit_leftovers_at_separate_centres_are_not_added_up():
    """Two centres holding 0.5 units each produced a shortfall no plan could close.

    The floor was measured on raw stock while the integer solve was capped at its
    floor, so each centre contributed up to a unit of phantom shortfall -- 4.0 units
    with eight centres. The floor is now measured on the same quantities the solve is
    capped at, so the two agree and there is nothing to report.
    """
    plan = solve_lp(np.array([0.99, 0.98, 0.5, 0.4, 0.3, 0.2]), np.full(6, 100.0),
                    np.array([10.5, 10.5]),
                    np.array([[1000.0, 1000.0]] * 2 + [[9000.0, 9000.0]] * 4),
                    max_distance_m=D, epsilon=EPS, min_share_top_quintile=1.0)
    assert plan.equity_shortfall == 0.0
    assert plan.notes == []


def test_a_fractional_shortfall_is_reported_when_the_plan_is_fractional():
    """The one-unit reporting floor is only sound for whole-unit plans. On the
    continuous relaxation a real shortfall of 0.7 units was reported as none."""
    plan = solve_lp(np.array([0.9, 0.5, 0.4, 0.3, 0.2]),
                    np.array([4.0, 3.7, 3.7, 3.7, 3.7]), np.array([50.0]),
                    np.full((5, 1), 1000.0), max_distance_m=D, epsilon=EPS,
                    min_share_top_quintile=0.25, round_units=False)
    assert plan.equity_shortfall == pytest.approx(0.7, abs=1e-6)
    assert plan.notes and "short of" in plan.notes[0]


def test_contradictory_rounding_flags_are_refused():
    """exact_integers was silently ignored when round_units was False."""
    args = (np.array([0.9]), np.array([10.5]), np.array([10.5]), np.array([[100.0]]))
    with pytest.raises(ValueError, match="contradicts"):
        solve_lp(*args, max_distance_m=D, round_units=False, exact_integers=True)
    fractional = solve_lp(*args, max_distance_m=D, round_units=False)
    assert fractional.total == pytest.approx(10.5), "the relaxation stays fractional"


def test_an_infinite_equity_penalty_is_refused():
    with pytest.raises(ValueError, match="equity_penalty must be positive"):
        solve_lp(np.full(3, 0.6), np.full(3, 10.0), np.array([100.0]),
                 np.full((3, 1), 100.0), max_distance_m=D,
                 min_share_top_quintile=0.25, equity_penalty=np.inf)


@pytest.mark.parametrize("solver", [solve_lp, solve_greedy])
def test_a_tiebreak_big_enough_to_stop_delivery_is_refused(solver):
    """epsilon had no upper bound, so a 'tiebreak' of 2.0 shipped nothing at all --
    the exact failure the module header warns about, one order of magnitude up."""
    with pytest.raises(ValueError, match="epsilon must be below 1"):
        solver(np.full(3, 0.9), np.full(3, 10.0), np.array([100.0]),
               np.full((3, 1), 4000.0), max_distance_m=D, epsilon=2.0)


def test_both_solvers_accept_the_same_equity_settings():
    """greedy hard-coded a penalty of 1.0 and never passed epsilon, so the two solvers
    disagreed about which settings were legal."""
    args = (np.full(3, 0.6), np.full(3, 10.0), np.array([100.0]), np.full((3, 1), 100.0))
    for bad in (1.5, -0.1, float("nan")):
        for solver in (solve_lp, solve_greedy):
            with pytest.raises(ValueError, match="share in"):
                solver(*args, max_distance_m=D, min_share_top_quintile=bad)


# --- regressions: the fifth review ----------------------------------------------------


def _stranding_problem():
    """The counterexample to 'greedy needs no equity pass'.

    Cell 0 can reach centres 0 and 1; cell 1 can reach only centre 0. Both are in the
    top quintile. Greedy sends cell 0 to the NEARER centre 0 and drains it, so cell 1
    gets nothing -- the same myopia as worked example B, reaching the equity floor.
    """
    n_cells, n_centres = 10, 8
    priority = np.linspace(0.95, 0.2, n_cells)
    need = np.full(n_cells, 10.0)
    stock = np.full(n_centres, 10.0)
    dist = np.full((n_cells, n_centres), 9_000.0)
    dist[0, 0], dist[0, 1] = 1000.0, 2000.0
    dist[1, 0] = 1000.0
    for i in range(2, n_cells):
        dist[i, (i % (n_centres - 2)) + 2] = 1500.0
    return priority, need, stock, dist


def test_greedy_can_miss_a_floor_the_lp_meets():
    """Pins the counterexample, because the docstring once claimed this was impossible.

    The earlier reasoning -- 'greedy serves the top cells first with the stock
    untouched, so if the floor can be met this order meets it' -- ignored that greedy
    also chooses the NEAREST centre, not the one that leaves the other top cell an
    option. If this ever starts passing trivially, the counterexample has decayed and
    needs rebuilding, not deleting.
    """
    args = _stranding_problem()
    kw = dict(max_distance_m=D, epsilon=EPS, min_share_top_quintile=0.25)
    greedy, lp = solve_greedy(*args, **kw), solve_lp(*args, **kw)
    top = top_quintile(args[0], args[1])

    assert greedy.delivered[top].sum() == 10, "greedy strands the second top cell"
    assert lp.delivered[top].sum() == 20, "the LP meets the floor from the same stock"
    assert greedy.equity_shortfall > 0 and lp.equity_shortfall == 0


def test_greedys_shortfall_is_labelled_as_its_own():
    """Greedy is what the site exposes as the quick estimate. Reporting its shortfall
    as if it were the achievable one would tell a relief team the top-priority cells
    cannot be covered when they can."""
    greedy = solve_greedy(*_stranding_problem(), max_distance_m=D, epsilon=EPS,
                          min_share_top_quintile=0.25)
    note = next(n for n in greedy.notes if "short of" in n)
    assert "quick method" in note and "exact solver may do better" in note, note

    lp = solve_lp(np.array([0.9, 0.5]), np.array([10.0, 10.0]), np.array([10.0]),
                  np.array([[9000.0], [9000.0]]), max_distance_m=D, epsilon=EPS,
                  min_share_top_quintile=0.25)
    assert all("quick method" not in n for n in lp.notes), "only greedy carries it"


def test_a_starved_unreachable_cell_is_not_called_fully_met():
    """A top cell needing 0.9 units and receiving nothing, because it is out of range,
    was reported as 'their own need is already fully met'."""
    plan = solve_lp(np.array([0.9, 0.5, 0.4, 0.3, 0.2]),
                    np.array([0.9, 100.0, 100.0, 100.0, 100.0]), np.array([100.0]),
                    np.array([[9000.0]] + [[1000.0]] * 4), max_distance_m=D,
                    epsilon=EPS, min_share_top_quintile=0.25)
    note = next(n for n in plan.notes if "short of" in n)
    assert "fully met" not in note, note
    assert "need only 0.9 between them" in note, "report the real need, not its floor"


def test_the_floor_cannot_exceed_what_the_solve_is_capped_at():
    """The floor used raw stock while the integer solve was capped at floor(stock), so
    each centre contributed up to a unit of shortfall no plan could ever close."""
    for n_centres in (2, 4, 8):
        stock = np.full(n_centres, 10.5)
        dist = np.tile(np.array([[1000.0] * n_centres]), (4, 1))
        plan = solve_lp(np.array([0.99, 0.98, 0.5, 0.4]), np.full(4, 100.0), stock,
                        dist, max_distance_m=D, epsilon=EPS, min_share_top_quintile=1.0)
        assert plan.equity_shortfall == 0.0, (
            f"{n_centres} centres left a phantom shortfall of "
            f"{plan.equity_shortfall}")


def test_a_fractional_shortfall_survives_an_integer_looking_optimum():
    """The whole-unit test was inferred from the data, so a real 0.5-unit shortfall was
    zeroed whenever the fractional optimum happened to land on whole numbers."""
    plan = solve_lp(np.array([0.9, 0.5, 0.4, 0.3, 0.2]), np.full(5, 4.0),
                    np.array([18.0]), np.full((5, 1), 1000.0), max_distance_m=D,
                    epsilon=EPS, min_share_top_quintile=0.25, round_units=False)
    assert plan.equity_shortfall == pytest.approx(0.5)
    assert plan.notes and "short of" in plan.notes[0]


@pytest.mark.parametrize("degenerate", [
    dict(stock=np.zeros(1)),
    dict(need=np.zeros(2)),
    dict(dist=np.array([[9000.0], [9000.0]])),
])
def test_contradictory_flags_are_refused_even_on_the_degenerate_path(degenerate):
    """The check sat after the early return, so zero stock, zero need or nothing in
    reach silently accepted it. Input validation must not depend on the data."""
    good = dict(priority=np.array([0.9, 0.5]), need=np.array([10.0, 10.0]),
                stock=np.array([10.0]), dist=np.array([[1000.0], [1000.0]]))
    with pytest.raises(ValueError, match="contradicts"):
        solve_lp(**{**good, **degenerate}, max_distance_m=D, round_units=False,
                 exact_integers=True)


def test_the_note_never_claims_more_is_short_than_is_owed():
    """math.ceil against math.floor produced '26 units short of the 25 they are owed'."""
    rng = np.random.default_rng(3)
    for _ in range(400):
        nc, ns = rng.integers(3, 8), rng.integers(1, 4)
        args = (rng.uniform(0.02, 1, nc), np.round(rng.uniform(0, 150, nc), 2),
                np.round(rng.uniform(0, 150, ns), 2), rng.uniform(200, 9000, (nc, ns)))
        plan = solve_lp(*args, max_distance_m=D, epsilon=EPS,
                        min_share_top_quintile=0.25)
        for note in plan.notes:
            if "short of" not in note:
                continue
            short, owed = (int(n.replace(",", "")) for n in
                           re.findall(r"(\d[\d,]*) unit[s]? short of the (\d[\d,]*)",
                                      note)[0])
            assert short <= owed, note


# --- D13: only centres that can hold stock are ever given any ------------------------


def _centre(name, role, can_hold_stock):
    """One SYNTHETIC centres.csv row. Coordinates are irrelevant to the gate."""
    return {"name": name, "org": "SYNTHETIC", "role": role,
            "can_hold_stock": can_hold_stock, "lat": "24.85", "lon": "67.20"}


def test_only_centres_marked_yes_can_hold_stock():
    rows = [_centre("A", "distribution_point", "yes"),
            _centre("B", "distribution_point", "no"),
            _centre("C", "clinic", "unknown"),
            _centre("D", "office", "yes")]
    assert [r["name"] for r in stock_holding_centres(rows)] == ["A", "D"]


def test_unknown_is_not_treated_as_yes():
    """'unknown' means nobody has checked. Stock cannot be sent from a guess."""
    assert stock_holding_centres([_centre("A", "clinic", "unknown")]) == []


def test_an_ambulance_standby_is_never_assigned_stock():
    """D13, P4-01 acceptance. The standby point is the nearest centre to every cell,
    and in the raw table it is listed with the most stock -- the strongest possible
    pull towards using it. It must still dispatch nothing, because it never reaches
    the solver at all."""
    rows = [_centre("Standby", "ambulance_standby", "no"),
            _centre("Store", "distribution_point", "yes")]
    raw_stock = {"Standby": 500.0, "Store": 40.0}
    raw_dist = {"Standby": [300.0, 400.0], "Store": [3000.0, 4000.0]}

    holders = stock_holding_centres(rows)
    names = [r["name"] for r in holders]
    assert "Standby" not in names

    stock = np.array([raw_stock[n] for n in names])
    dist = np.array([raw_dist[n] for n in names]).T
    for solver in (solve_lp, solve_greedy):
        plan = solver(np.array([0.9, 0.5]), np.array([30.0, 30.0]), stock, dist,
                      max_distance_m=D)
        # Every unit dispatched comes from the one real store, and all of it goes out.
        assert names == ["Store"]
        assert plan.dispatched.tolist() == pytest.approx([40.0])
        assert plan.total == pytest.approx(40.0)


def test_an_ambulance_standby_marked_as_holding_stock_is_refused():
    """A standby point is somewhere an ambulance waits, not a store. If the table says
    it holds stock, one of the two fields is wrong, and guessing which would quietly
    add or remove supply. Refuse, and name the row."""
    rows = [_centre("Store", "distribution_point", "yes"),
            _centre("Korangi Standby", "ambulance_standby", "yes")]
    with pytest.raises(ValueError, match="Korangi Standby"):
        stock_holding_centres(rows)


@pytest.mark.parametrize("flag", ["Yes", " yes ", "YES"])
def test_the_stock_flag_is_read_case_and_space_insensitively(flag):
    assert len(stock_holding_centres([_centre("A", "clinic", flag)])) == 1


@pytest.mark.parametrize("flag", ["y", "true", "", "maybe"])
def test_an_unrecognised_stock_flag_is_refused(flag):
    """A typo must not silently become 'no' -- that would remove a centre's supply
    from the plan with nothing on screen to say so."""
    with pytest.raises(ValueError, match="can_hold_stock"):
        stock_holding_centres([_centre("A", "clinic", flag)])


def test_an_unrecognised_role_is_refused():
    with pytest.raises(ValueError, match="role"):
        stock_holding_centres([_centre("A", "warehouse", "yes")])


def test_the_gate_uses_the_same_vocabulary_as_the_centres_schema_test():
    """tests/test_centres.py and the gate must agree, or a row could pass the schema
    check and still be refused by the solver (or the reverse)."""
    from pipeline.allocate import CENTRE_ROLES, STOCK_FLAGS
    from tests.test_centres import ROLES, STOCK
    assert CENTRE_ROLES == ROLES
    assert STOCK_FLAGS == STOCK
