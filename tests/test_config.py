"""The config files encode Samraj's decisions D2-D8. Tests keep them honest."""

VALID_DIMENSIONS = {"hazard", "exposure", "vulnerability"}


def test_indicator_fields(indicators):
    for ind in indicators["indicators"]:
        for field in ("id", "name_en", "dimension", "unit", "direction", "transform", "source"):
            assert field in ind, f"{ind.get('id')} missing {field}"
        assert ind["dimension"] in VALID_DIMENSIONS
        assert ind["direction"] in (1, -1)
        assert ind["reason_en"].strip(), f"{ind['id']} needs a plain-language reason"


def test_indicator_ids_unique(indicators):
    ids = [i["id"] for i in indicators["indicators"]]
    assert len(ids) == len(set(ids))


def test_d4_indicator_count(indicators):
    """D4 approved exactly eight indicators; adding one is a decision, not a tweak."""
    assert len(indicators["indicators"]) == 8


def test_dropped_indicators_state_a_reason(indicators):
    for dropped in indicators.get("dropped", []):
        assert len(dropped["reason"]) > 40, f"{dropped['id']} dropped without a reason"


def test_weights_sum_to_one(weights):
    for group in ("dimensions", "vulnerability", "hazard", "exposure"):
        assert abs(sum(weights[group].values()) - 1.0) < 1e-9, group


def test_weight_keys_match_indicators(indicators, weights):
    by_dim: dict[str, set[str]] = {d: set() for d in VALID_DIMENSIONS}
    for ind in indicators["indicators"]:
        by_dim[ind["dimension"]].add(ind["id"])
    for dim, ids in by_dim.items():
        assert set(weights[dim]) == ids, f"{dim} weights do not match its indicators"


def test_d7a_dimension_exponents_are_equal(weights):
    """D7a: dimension exponents are fixed at 1/3 and are not set by AHP."""
    values = list(weights["dimensions"].values())
    assert all(abs(v - 1 / 3) < 1e-9 for v in values)


def test_provisional_weights_have_no_owner(weights):
    if weights["provisional"]:
        assert weights["decided_by"] is None
        assert weights["consistency_ratio"] is None


def test_d6b_floor_rules(model):
    """D6b: H and V are floored, E is not - a zero there is a real absence of people."""
    floor = model["aggregation"]["floor"]
    assert floor["hazard"] == 0.01
    assert floor["vulnerability"] == 0.01
    assert floor["exposure"] is None


def test_d5_normalisation(model):
    norm = model["normalisation"]
    assert norm["method"] == "robust_minmax"
    assert norm["clip_low_percentile"] == 5
    assert norm["clip_high_percentile"] == 95
    assert norm["alternative"] == "percentile_rank"


def test_d6a_geometric_aggregation(model):
    assert model["aggregation"]["across_dimensions"] == "weighted_geometric_mean"


def test_sensitivity_is_seeded(model):
    assert model["sensitivity"]["n"] >= 1000
    assert isinstance(model["sensitivity"]["seed"], int)


def test_d8_need_is_not_defined_from_priority(allocation):
    """Defining need from Priority would count the model's own judgement twice."""
    assert allocation["need"]["definition"] == "age_vulnerable"


def test_d8_values_present(allocation):
    assert allocation["provisional"] is True
    assert allocation["service"]["max_distance_m"] == 5000
    assert 0 < allocation["equity"]["min_share_top_quintile"] < 1
    for commodity in allocation["commodities"]:
        assert commodity["units_per_person_per_day"] > 0
        assert commodity["basis"].strip()


def test_d3_grid_resolution(area):
    assert area["grid"]["system"] == "h3"
    assert area["grid"]["resolution"] == 9


def test_crs_settings(area):
    assert area["crs"]["storage"] == "EPSG:4326"
    assert area["crs"]["measurement"] == "EPSG:32642"
