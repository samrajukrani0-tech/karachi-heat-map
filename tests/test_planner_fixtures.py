"""The planner's end-to-end fixtures must be what the Python solver produces today."""

import json
import math

from tests.fixtures import make_planner_fixtures as mk


def _same(a, b, path="$"):
    """Exact for structure, strings and integers; floats to 1 part in 10^9.

    PROJ on Linux (CI) and macOS disagree in the last bits of a UTM distance -- 4e-10 m
    on a 2.6 km distance -- so exact float equality fails across platforms while
    meaning nothing. A real change to the solver moves numbers by far more.
    """
    if isinstance(a, dict) and isinstance(b, dict):
        assert a.keys() == b.keys(), f"{path}: keys differ"
        for k in a:
            _same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), f"{path}: lengths {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            _same(x, y, f"{path}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9), f"{path}: {a} != {b}"
    else:
        assert a == b, f"{path}: {a!r} != {b!r}"


def test_fixtures_are_current():
    for path, doc in mk.build().items():
        committed = json.loads(path.read_text(encoding="utf-8"))
        _same(committed, json.loads(json.dumps(doc)))


def test_the_comparison_still_catches_a_real_change():
    """Guard the guard: a tolerance this loose would hide a solver change."""
    import pytest
    with pytest.raises(AssertionError):
        _same({"x": 2586.8256}, {"x": 2586.8257})
    with pytest.raises(AssertionError):
        _same({"x": [1, 2]}, {"x": [1, 3]})


def test_fixtures_are_labelled_synthetic():
    for path, doc in mk.build().items():
        assert "SYNTHETIC" in path.name and "SYNTHETIC" in json.dumps(doc)
