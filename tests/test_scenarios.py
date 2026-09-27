"""P4-02a: precomputed scenarios. Every centre table here is SYNTHETIC and lives only
in this file; nothing built from it is written to site/ or data/processed/."""

import json
import re

import numpy as np
import pytest

from pipeline import scenarios as sc
from pipeline.allocate import commodity_settings


def _centre(name, role, flag, lat, lon):
    return {"name": name, "org": "SYNTHETIC", "role": role, "can_hold_stock": flag,
            "lat": str(lat), "lon": str(lon), "source": "SYNTHETIC",
            "verified_by": "SYNTHETIC", "verified_on": "2026-09-27", "notes": "SYNTHETIC"}


@pytest.fixture(scope="module")
def cells():
    return sc.load_cells()


@pytest.fixture(scope="module")
def landhi_centre(cells):
    lon, lat = cells.lonlat.mean(axis=0)
    return lat, lon


@pytest.fixture(scope="module")
def built(cells, landhi_centre):
    lat, lon = landhi_centre
    return sc.build_scenarios(cells, [_centre("SYNTHETIC depot", "distribution_point",
                                              "yes", lat, lon)])


def test_cells_come_from_the_committed_data(cells):
    assert len(cells.h3) == 265
    assert np.all((cells.priority >= 0) & (cells.priority <= 1))
    assert np.all(cells.people_in_need >= 0)
    # centroids lie inside Landhi's bounding box (P1-01: 67.148-67.219 E, 24.815-24.870 N)
    assert cells.lonlat[:, 0].min() > 67.14 and cells.lonlat[:, 0].max() < 67.23
    assert cells.lonlat[:, 1].min() > 24.81 and cells.lonlat[:, 1].max() < 24.88


def test_the_scenario_grid_is_complete(built):
    # 2 commodities x 3 stock levels x 3 service distances (D8)
    assert len(built) == 18
    assert len({s["id"] for s in built}) == 18
    assert {s["max_distance_m"] for s in built} == {3000.0, 5000.0, 8000.0}


def test_shares_never_exceed_the_stock(built):
    for s in built:
        for method in ("lp", "greedy"):
            total = sum(c["share_of_stock"] for c in s[method]["cells"])
            assert total <= 1 + 1e-3, (s["id"], method, total)
            assert 0 <= s[method]["undelivered_share"] <= 1
            for c in s[method]["cells"]:
                assert 0 < c["share_of_need_met"] <= 1


def test_the_exact_plan_is_never_worse_than_the_quick_estimate(built):
    for s in built:
        assert s["lp"]["objective"] >= s["greedy"]["objective"] - 1e-6, s["id"]


def test_ample_stock_meets_all_reachable_need_at_8km(built):
    """At 100% of need and a limit wider than Landhi, every populated cell is reached."""
    s = next(s for s in built if s["id"] == "water-100pct-8000m")
    assert s["cells_out_of_reach"] == 0
    assert s["lp"]["cells_served"] == s["cells_with_need"]
    assert all(c["share_of_need_met"] == 1 for c in s["lp"]["cells"])


def test_summaries_state_shares_never_absolute_quantities(built):
    """D21: no 'N litres' or 'N sachets' anywhere a coordinator reads."""
    pattern = re.compile(r"\d[\d,.]*\s*(l\b|litres?|liters?|sachets?|units?)", re.I)
    for s in built:
        assert not pattern.search(s["summary"]), s["summary"]
        assert "provisional" in s["summary"].lower()
        assert "estimated need" in s["summary"]


def test_an_ambulance_standby_row_dispatches_nothing(cells, landhi_centre):
    """P4-02 acceptance (P4-01 checker caveat): the standby point is placed at the
    centre of Landhi, nearest to everything; the only stock holder is 6 km away. With a
    3 km limit the standby point's neighbourhood must receive nothing at all, because
    the standby point is not a source of stock, and it never appears as one."""
    lat, lon = landhi_centre
    rows = [_centre("SYNTHETIC standby", "ambulance_standby", "no", lat, lon),
            _centre("SYNTHETIC far depot", "distribution_point", "yes", lat, lon + 0.06)]
    built = sc.build_scenarios(cells, rows)
    assert built
    for s in built:
        assert [c["name"] for c in s["centres"]] == ["SYNTHETIC far depot"]
    near = next(s for s in built if s["id"] == "water-100pct-3000m")
    served = {c["h3"] for c in near["lp"]["cells"]}
    # cells within 1 km of the standby point are beyond 3 km road distance of the depot
    d = np.hypot((cells.lonlat[:, 0] - lon) * 101_000, (cells.lonlat[:, 1] - lat) * 111_000)
    around_standby = {h for h, km in zip(cells.h3, d, strict=True) if km < 1000}
    assert around_standby and not (served & around_standby)


def test_a_standby_marked_as_holding_stock_stops_the_run(cells, landhi_centre):
    """D29, approved by Samraj: refuse and name the row, never guess."""
    lat, lon = landhi_centre
    rows = [_centre("SYNTHETIC depot", "distribution_point", "yes", lat, lon),
            _centre("SYNTHETIC bad row", "ambulance_standby", "yes", lat, lon)]
    with pytest.raises(ValueError, match="SYNTHETIC bad row"):
        sc.build_scenarios(cells, rows)


def test_no_stock_holder_means_no_scenarios(cells, landhi_centre):
    lat, lon = landhi_centre
    rows = [_centre("SYNTHETIC unchecked", "distribution_point", "unknown", lat, lon)]
    assert sc.build_scenarios(cells, rows) == []
    doc = sc.document([], 1)
    assert doc["status"] == "no_verified_centre" and doc["scenarios"] == []
    assert "Q2" in doc["message"]


def test_the_published_file_matches_the_committed_centres(root, cells):
    """The live export is rebuilt from data/manual/centres.csv and nothing else."""
    published = json.loads((root / "site" / "data" / "scenarios.json").read_text("utf-8"))
    rows = sc.read_centres(root / "data" / "manual" / "centres.csv")
    expected = sc.document(sc.build_scenarios(cells, rows), len(rows))
    assert published == json.loads(json.dumps(expected))
    assert "SYNTHETIC" not in json.dumps(published)
    assert published["provisional"] is True and published["illustrative"] is True
    assert "2.3" in published["undercount_note"]


def test_the_water_figure_is_cited_to_the_sphere_handbook():
    """P4-02 acceptance: verified against the handbook and cited, no longer UNVERIFIED."""
    basis = commodity_settings("water")["basis"]
    assert "UNVERIFIED" not in basis
    for needle in ("Sphere Handbook", "2018", "p. 107", "2.5-3"):
        assert needle in basis, needle
