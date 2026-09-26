"""features.json is the source of truth for progress, so guard its shape."""

import json

from jsonschema import Draft202012Validator


def _features(root):
    return json.loads((root / "features.json").read_text(encoding="utf-8"))


def test_validates_against_schema(root):
    schema = json.loads((root / "tests" / "features.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(_features(root)))
    assert errors == [], [e.message for e in errors]


def test_ids_are_unique(root):
    ids = [f["id"] for f in _features(root)["features"]]
    assert len(ids) == len(set(ids))


def test_dependencies_exist(root):
    features = _features(root)["features"]
    ids = {f["id"] for f in features}
    for feature in features:
        for dep in feature["depends_on"]:
            assert dep in ids, f"{feature['id']} depends on unknown {dep}"


def test_no_dependency_cycles(root):
    features = {f["id"]: f for f in _features(root)["features"]}
    seen: dict[str, int] = {}

    def visit(fid: str, trail: tuple[str, ...]) -> None:
        assert fid not in trail, f"cycle: {' -> '.join((*trail, fid))}"
        if seen.get(fid):
            return
        for dep in features[fid]["depends_on"]:
            visit(dep, (*trail, fid))
        seen[fid] = 1

    for fid in features:
        visit(fid, ())


def test_dropped_features_state_a_reason(root):
    for feature in _features(root)["features"]:
        if feature["dropped"] is not None:
            assert len(feature["dropped"]) > 40, (
                f"{feature['id']} is dropped without a recorded reason"
            )
            assert not feature["passes"], f"{feature['id']} is both dropped and passing"


def test_passing_features_carry_evidence(root):
    """PROMPT.md section 2.3: a feature passes only with evidence recorded."""
    for feature in _features(root)["features"]:
        if feature["passes"]:
            assert feature["evidence"], f"{feature['id']} passes with no evidence"
