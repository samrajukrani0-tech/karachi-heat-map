"""P2-01: normalisation. Every acceptance criterion has a test here.

All fixtures are SYNTHETIC hand-made arrays, so the properties are checked against
arithmetic rather than against whatever the real data happens to look like.
"""

import numpy as np
import pytest

from pipeline.normalise import (
    METHODS,
    ConstantIndicatorWarning,
    normalise,
    percentile_rank,
    robust_minmax,
)

SYNTHETIC = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])


@pytest.mark.parametrize("method", sorted(METHODS))
def test_output_is_within_zero_and_one(method):
    out = normalise(SYNTHETIC, method=method)
    assert np.nanmin(out) >= 0.0 and np.nanmax(out) <= 1.0


@pytest.mark.parametrize("method", sorted(METHODS))
def test_output_is_monotonic_non_decreasing(method):
    """Order must survive: a hotter cell can never normalise cooler than a cooler one."""
    rng = np.random.default_rng(20260926)
    values = np.sort(rng.normal(40, 4, size=200))
    out = normalise(values, method=method)
    assert np.all(np.diff(out) >= -1e-12)


@pytest.mark.parametrize("method", sorted(METHODS))
def test_direction_minus_one_flips_the_result(method):
    up = normalise(SYNTHETIC, method=method, direction=1)
    down = normalise(SYNTHETIC, method=method, direction=-1)
    assert np.allclose(up, 1.0 - down)
    assert np.argmax(up) == np.argmin(down)


@pytest.mark.parametrize("method", sorted(METHODS))
def test_an_invalid_direction_is_rejected(method):
    with pytest.raises(ValueError):
        normalise(SYNTHETIC, method=method, direction=0)


@pytest.mark.parametrize("method", sorted(METHODS))
def test_ties_normalise_to_the_same_value(method):
    """Equal inputs must give equal outputs, whatever order they arrived in."""
    values = np.array([1.0, 5.0, 5.0, 5.0, 9.0])
    out = normalise(values, method=method)
    assert out[1] == pytest.approx(out[2]) == pytest.approx(out[3])


@pytest.mark.parametrize("method", sorted(METHODS))
def test_a_constant_indicator_becomes_zero_with_a_warning(method):
    """Section 7: a constant indicator becomes 0, with a warning. Zero and not 0.5 --
    an indicator that distinguishes nothing should contribute nothing."""
    with pytest.warns(ConstantIndicatorWarning):
        out = normalise(np.full(12, 7.5), method=method, name="flat")
    assert np.all(out == 0.0)


@pytest.mark.parametrize("method", sorted(METHODS))
def test_missing_values_stay_missing(method):
    values = np.array([1.0, np.nan, 3.0, 4.0, np.nan, 6.0])
    out = normalise(values, method=method)
    assert np.isnan(out[1]) and np.isnan(out[4])
    assert np.isfinite(out[[0, 2, 3, 5]]).all()


@pytest.mark.parametrize("method", sorted(METHODS))
def test_all_missing_returns_all_missing(method):
    out = normalise(np.full(5, np.nan), method=method)
    assert np.isnan(out).all()


def test_robust_minmax_clips_at_the_configured_percentiles():
    """Values beyond the clip points must land exactly on 0 and 1, which is what makes
    the method resistant to a single extreme cell."""
    values = np.concatenate([[-1000.0], np.arange(1.0, 100.0), [1000.0]])
    out = robust_minmax(values, low_percentile=5, high_percentile=95)
    assert out[0] == 0.0 and out[-1] == 1.0
    assert (out == 0.0).sum() >= 2, "the low tail should be clipped, not just the minimum"
    assert (out == 1.0).sum() >= 2


def test_robust_minmax_is_linear_between_the_clip_points():
    values = np.arange(0.0, 101.0)
    out = robust_minmax(values, low_percentile=5, high_percentile=95)
    middle = (values >= 5) & (values <= 95)
    differences = np.diff(out[middle])
    assert np.allclose(differences, differences[0]), "spacing must be preserved (D5)"


def test_robust_minmax_resists_an_outlier_that_would_wreck_plain_minmax():
    ordinary = np.arange(1.0, 51.0)
    with_outlier = np.append(ordinary, 10_000.0)
    plain = (with_outlier - with_outlier.min()) / (with_outlier.max() - with_outlier.min())
    robust = robust_minmax(with_outlier)
    assert plain[:50].max() < 0.01, "plain min-max crushes the real data (the motivation)"
    assert robust[:50].max() == 1.0, "robust min-max keeps the real data spread out"


def test_percentile_rank_spans_the_full_range():
    out = percentile_rank(SYNTHETIC)
    assert out.min() == 0.0 and out.max() == 1.0


def test_percentile_rank_is_uniform_by_construction():
    """The defining property, and the reason it discards magnitude."""
    rng = np.random.default_rng(7)
    clustered = np.concatenate([rng.normal(10, 0.01, 90), rng.normal(50, 0.01, 10)])
    out = percentile_rank(clustered)
    assert np.percentile(out, 50) == pytest.approx(0.5, abs=0.02)


def test_the_two_methods_differ_on_clustered_data():
    """The D5 trade-off, demonstrated: rank spreads near-identical values apart."""
    clustered = np.concatenate([np.full(90, 10.0) + np.arange(90) * 1e-4, np.full(10, 50.0)])
    rank = percentile_rank(clustered)
    minmax = robust_minmax(clustered)
    assert rank[:90].max() - rank[:90].min() > 0.8, "rank stretches a tight cluster"
    assert minmax[:90].max() - minmax[:90].min() < 0.05, "min-max keeps it tight"


def test_a_single_value_does_not_crash():
    out = percentile_rank(np.array([np.nan, 4.0, np.nan]))
    assert out[1] == 0.0 and np.isnan(out[0])


def test_unknown_method_is_rejected():
    with pytest.raises(ValueError, match="unknown method"):
        normalise(SYNTHETIC, method="magic")


def test_two_dimensional_input_is_rejected():
    with pytest.raises(ValueError):
        robust_minmax(np.ones((3, 3)))


def test_claude_md_stays_within_its_line_limit(root):
    """P0-03: CLAUDE.md loads every session, so it is capped at 150 lines."""
    lines = (root / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 150, f"CLAUDE.md is {len(lines)} lines; trim it or raise the cap"


# --- points raised by the independent checker (PROMPT.md section 3.1) ---------------

@pytest.mark.parametrize("method", sorted(METHODS))
def test_a_constant_indicator_with_direction_minus_one_is_still_zero(method):
    """The checker found the written rule ambiguous: read as steps-in-order, a constant
    indicator with direction -1 would give 1 - 0 = 1, i.e. maximum risk everywhere. The
    constant case short-circuits instead, and this test pins that reading."""
    with pytest.warns(ConstantIndicatorWarning):
        out = normalise(np.full(10, 3.0), method=method, direction=-1, name="flat")
    assert np.all(out == 0.0), "a constant indicator must contribute nothing, not everything"


def test_constant_test_is_relative_to_magnitude():
    """An absolute tolerance would misjudge columns far from 1.0."""
    from pipeline.normalise import _is_constant
    assert _is_constant(1e9, 1e9 + 1e-6), "tiny spread on a huge magnitude is constant"
    assert not _is_constant(0.0, 1e-6), "the same spread on a small magnitude is real"


def test_a_flat_core_with_live_tails_is_reported_not_swallowed():
    """The checker's case: constant between p5 and p95 but varying in the tails. Robust
    min-max discards that variation, so it must say so."""
    from pipeline.normalise import FlatCoreWarning
    values = np.concatenate([[1.0, 2.0], np.full(96, 50.0), [98.0, 99.0]])
    with pytest.warns(FlatCoreWarning):
        robust_minmax(values, name="flat_core")


def test_log1p_is_rank_invariant():
    """The checker verified this is a no-op under percentile rank; pin it so a future
    non-monotone transform cannot silently change the rank branch."""
    values = np.array([0.0, 5.0, 50.0, 500.0, 5000.0])
    assert np.allclose(percentile_rank(values), percentile_rank(np.log1p(values)))


def test_percentile_rank_endpoints_need_not_be_attained_when_values_tie():
    """With k cells tied at the minimum, the lowest rank is the average of 1..k, so the
    normalised minimum is above 0. Documented so nothing downstream asserts min == 0."""
    values = np.concatenate([np.zeros(21), np.arange(1.0, 245.0)])
    out = percentile_rank(values)
    assert out.min() > 0.0
    assert len(set(np.round(out[:21], 12))) == 1, "all tied cells share one value"
