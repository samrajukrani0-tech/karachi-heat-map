"""P6-01, prepared: the import and comparison, exercised on SYNTHETIC rankings only.

No real ranking exists yet; tests/fixtures/expert_rankings_SYNTHETIC.csv is invented
for testing, labelled as such, and never written to data/ or docs/."""

import json
from pathlib import Path

import pytest

from pipeline import expert
from pipeline.localities import read as read_localities

FIXTURE = Path(__file__).parent / "fixtures" / "expert_rankings_SYNTHETIC.csv"


@pytest.fixture(scope="module")
def known():
    return {p["name_en"]: p for p in read_localities()}


@pytest.fixture(scope="module")
def result(known):
    by_person = expert.validate(expert.read_rankings(FIXTURE), known)
    return expert.analyse(by_person, expert.load_cells(), read_localities())


def test_the_real_file_is_waiting_with_only_its_header(root):
    """Phase 6 is prepared, not run: no ranking has been invented to fill the gap."""
    text = (root / "data" / "manual" / "expert_rankings.csv").read_text("utf-8")
    assert text.strip() == ",".join(expert.COLUMNS)
    assert expert.read_rankings(root / "data" / "manual" / "expert_rankings.csv") == []
    assert not (root / "data" / "processed" / "expert_agreement.json").exists()
    assert not (root / "docs" / "expert-agreement.md").exists()


def test_a_model_that_agrees_scores_positive_and_one_that_disagrees_negative(result):
    r01 = result["respondents"]["R01"]["agreement"]       # ranked in the model's order
    r02 = result["respondents"]["R02"]["agreement"]       # the exact reverse
    assert r01["spearman"] > 0.9
    assert r02["spearman"] < -0.9
    assert r01["n_localities"] == 6                       # the write-in has no location


def test_unlocated_write_ins_are_listed_not_guessed(result):
    assert result["unscorable_places"] == ["Somewhere Unmapped"]
    assert result["respondents"]["R01"]["places_ranked"] == 7
    assert result["respondents"]["R01"]["places_scored"] == 6


def test_a_located_write_in_is_scored(result):
    assert result["place_scores"]["Future Colony"]["cells"] >= 1


def test_respondents_who_saw_the_map_are_kept_out_of_the_consensus(result):
    c = result["consensus_of_blind_respondents"]
    assert c["respondents"] == 2                          # R01, R02; not R03
    assert result["respondents"]["R03"]["ranked_before_seeing_map"] is False
    assert c["kendalls_w_between_respondents"] == 0.0     # exact opposites
    # ...so their average ranking is flat, and a correlation with it is undefined --
    # reported as such, not as rho = 0 and not as a crash
    assert "undefined" in c["agreement"]
    assert result["respondents"]["R03"]["agreement"]["weak_sample"] is True


def test_place_scores_use_the_same_cells_as_the_field_briefs(root, known):
    """A place's model score must be about the areas its brief shows."""
    index = json.loads((root / "site" / "briefs" / "index.json").read_text("utf-8"))
    cells = expert.load_cells()
    for b in index["briefs"]:
        p = known[b["name_en"]]
        s = expert.place_score(float(p["lon"]), float(p["lat"]), cells, p["h3_cell"])
        assert s["cells"] == b["areas"], b["name_en"]


def test_weighted_mean_and_maximum_are_both_reported(result):
    s = result["place_scores"]["Ilyas Goth"]
    assert 0 < s["weighted_mean"] <= s["maximum"] <= 1


@pytest.mark.parametrize("bad, message", [
    ("Samraj,x,x,,2026-11-01,yes,Ilyas Goth,1,,,", "anonymous code"),
    ("R09,x,x,,2026-11-01,maybe,Ilyas Goth,1,,,", "yes or no"),
    ("R09,x,x,,2026-11-01,yes,Ilyas Goth,one,,,", "whole number"),
    ("R09,x,x,,2026-11-01,yes,New Place,1,24.8,,", "both lat and lon"),
])
def test_bad_rows_are_refused_with_the_line_named(tmp_path, known, bad, message):
    path = tmp_path / "r.csv"
    path.write_text(",".join(expert.COLUMNS) + "\n" + bad + "\n", encoding="utf-8")
    with pytest.raises(expert.RankingError, match=message):
        expert.validate(expert.read_rankings(path), known)


def test_gaps_or_repeats_in_a_persons_ranks_are_refused(tmp_path, known):
    path = tmp_path / "r.csv"
    path.write_text(",".join(expert.COLUMNS) + "\n"
                    "R01,x,x,,d,yes,Ilyas Goth,1,,,\nR01,x,x,,d,yes,Labour Colony,3,,,\n",
                    encoding="utf-8")
    with pytest.raises(expert.RankingError, match="each used once"):
        expert.validate(expert.read_rankings(path), known)


def test_the_report_is_written_and_readable(result, tmp_path):
    out = tmp_path / "report.md"
    expert.write_report(result, out)
    text = out.read_text("utf-8")
    assert "R01" in text and "saw the map" in text and "Kendall's W" in text
    assert "Somewhere Unmapped" in text
    assert "Samraj decides" in text
