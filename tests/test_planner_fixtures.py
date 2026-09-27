"""The planner's end-to-end fixtures must be what the Python solver produces today."""

import json

from tests.fixtures import make_planner_fixtures as mk


def test_fixtures_are_current():
    for path, doc in mk.build().items():
        committed = json.loads(path.read_text(encoding="utf-8"))
        assert committed == json.loads(json.dumps(doc)), (
            f"{path.name} is stale: run uv run python tests/fixtures/make_planner_fixtures.py")


def test_fixtures_are_labelled_synthetic():
    for path, doc in mk.build().items():
        assert "SYNTHETIC" in path.name and "SYNTHETIC" in json.dumps(doc)
