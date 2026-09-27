"""P6-01, prepared: import real expert rankings and compare them with the model.

    uv run python -m pipeline.expert            # analyse data/manual/expert_rankings.csv
    uv run python -m pipeline.expert --check    # validate the file only

Until Samraj brings completed forms back from the field, the rankings file holds only
its header, and this module says so and writes nothing (§2.1: nothing is simulated in
place of real answers). The analysis is tested on SYNTHETIC rankings in
tests/test_expert.py.

How one form becomes one row per place:
  * Enter each form as rows of ``data/manual/expert_rankings.csv`` -- one row per place
    ranked. The columns are documented in ``docs/expert-ranking-import.md``.
  * ``respondent`` is an anonymous code (R01, R02, ...), never a name (§2.5).
  * A place written in by hand needs ``lat`` and ``lon`` to be scored; without them it is
    listed, not guessed.
  * Forms filled in AFTER seeing the map are kept but analysed separately: their
    agreement is inflated by construction, because the person has seen the answer.

How the model scores a place (D31, approved by Samraj): the
population-weighted mean Priority of the cells within 500 m of the place's point, the
same cells its field brief shows. The unweighted maximum is reported alongside, so the
choice is visible.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from pipeline.config import DOCS, MANUAL, PROCESSED, ROOT
from pipeline.localities import RADIUS_M
from pipeline.localities import read as read_localities
from pipeline.validate import expert_agreement

RANKINGS = MANUAL / "expert_rankings.csv"
OUT_JSON = PROCESSED / "expert_agreement.json"
OUT_DOC = DOCS / "expert-agreement.md"
COLUMNS = ["respondent", "organisation", "role", "years_in_landhi", "date",
           "ranked_before_seeing_map", "place", "rank", "lat", "lon", "notes"]
MIN_PLACES = 5          # fewer than this and a rank correlation means almost nothing


class RankingError(ValueError):
    """A problem in the rankings file, with the row it is on."""


def _metres(lon1, lat1, lon2, lat2) -> float:
    r = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def load_cells(root: Path = ROOT) -> list[dict]:
    doc = json.loads((root / "site" / "data" / "cells.geojson").read_text(encoding="utf-8"))
    return [f["properties"] for f in doc["features"]]


def place_score(lon: float, lat: float, cells: list[dict], h3_cell: str | None = None
                ) -> dict | None:
    """Model score for a place: the cells within RADIUS_M of its point (D31)."""
    near = [c for c in cells
            if c["h3"] == h3_cell or _metres(lon, lat, *c["c"]) <= RADIUS_M]
    if not near:
        return None
    people = np.array([c["people"] for c in near], dtype=float)
    priority = np.array([c["priority"] for c in near], dtype=float)
    weighted = float((people * priority).sum() / people.sum()) if people.sum() else 0.0
    return {"cells": len(near), "weighted_mean": round(weighted, 4),
            "maximum": round(float(priority.max()), 4)}


def read_rankings(path: Path = RANKINGS) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != COLUMNS:
            raise RankingError(f"{path.name}: header must be exactly {','.join(COLUMNS)}")
        return [dict(r, _line=i) for i, r in enumerate(reader, start=2)
                if any((v or "").strip() for k, v in r.items() if k != "_line")]


def validate(rows: list[dict], known: dict[str, dict]) -> dict[str, list[dict]]:
    """Check every row and group by respondent. Refuses, naming the line, on any error."""
    by_person: dict[str, list[dict]] = {}
    for r in rows:
        line = r["_line"]
        who = r["respondent"].strip()
        if not re.fullmatch(r"R\d{2,3}", who):
            raise RankingError(f"line {line}: respondent must be an anonymous code like "
                               f"R01, not {who!r} -- no names in this file (§2.5)")
        if r["ranked_before_seeing_map"].strip().lower() not in ("yes", "no"):
            raise RankingError(f"line {line}: ranked_before_seeing_map must be yes or no")
        try:
            rank = int(r["rank"])
        except ValueError:
            raise RankingError(f"line {line}: rank {r['rank']!r} is not a whole number") \
                from None
        place = r["place"].strip()
        if not place:
            raise RankingError(f"line {line}: place is empty")
        if place not in known and (r["lat"].strip() == "") != (r["lon"].strip() == ""):
            raise RankingError(f"line {line}: give both lat and lon for {place!r}, or neither")
        by_person.setdefault(who, []).append(
            {"place": place, "rank": rank, "lat": r["lat"].strip(), "lon": r["lon"].strip(),
             "before": r["ranked_before_seeing_map"].strip().lower() == "yes",
             "organisation": r["organisation"].strip(), "role": r["role"].strip(),
             "line": line})
    for who, items in by_person.items():
        ranks = sorted(i["rank"] for i in items)
        if ranks != list(range(1, len(ranks) + 1)):
            raise RankingError(f"{who}: ranks must be 1, 2, 3 ... with each used once; "
                               f"got {ranks}")
        places = [i["place"] for i in items]
        if len(set(places)) != len(places):
            raise RankingError(f"{who}: a place is ranked twice")
        if len({i["before"] for i in items}) > 1:
            raise RankingError(f"{who}: ranked_before_seeing_map differs between rows")
    return by_person


def kendalls_w(matrix: np.ndarray) -> float:
    """Agreement among m respondents ranking the same n places: 0 = none, 1 = total."""
    m, n = matrix.shape
    totals = matrix.sum(axis=0)
    s = float(((totals - totals.mean()) ** 2).sum())
    return round(12 * s / (m ** 2 * (n ** 3 - n)), 4)


def analyse(by_person: dict[str, list[dict]], cells: list[dict],
            localities: list[dict]) -> dict:
    known = {p["name_en"]: p for p in localities}
    scores: dict[str, dict | None] = {}
    unscorable: set[str] = set()
    for items in by_person.values():
        for i in items:
            if i["place"] in scores:
                continue
            if i["place"] in known:
                p = known[i["place"]]
                scores[i["place"]] = place_score(float(p["lon"]), float(p["lat"]), cells,
                                                 p["h3_cell"])
            elif i["lat"]:
                scores[i["place"]] = place_score(float(i["lon"]), float(i["lat"]), cells)
            else:
                scores[i["place"]] = None
            if scores[i["place"]] is None:
                unscorable.add(i["place"])

    def compare(items: list[dict], key: str) -> dict | None:
        usable = [i for i in items if scores.get(i["place"])]
        if len(usable) < 3:
            return None
        # model rank 1 = highest priority, the same direction as the form's rank 1
        model = rankdata([-scores[i["place"]][key] for i in usable])
        expert = rankdata([i["rank"] for i in usable])
        if len(set(expert)) < 2 or len(set(model)) < 2:
            # e.g. two respondents who rank in exactly opposite orders average to a
            # flat ranking; a correlation with a constant is undefined, not zero
            return {"undefined": "one side ranks every place equally, so no "
                                 "correlation exists", "n_localities": len(usable)}
        result = expert_agreement(model.tolist(), expert.tolist())
        result["weak_sample"] = len(usable) < MIN_PLACES
        return result

    respondents = {}
    for who, items in sorted(by_person.items()):
        respondents[who] = {
            "organisation": items[0]["organisation"], "role": items[0]["role"],
            "ranked_before_seeing_map": items[0]["before"],
            "places_ranked": len(items),
            "places_scored": sum(bool(scores.get(i["place"])) for i in items),
            "agreement": compare(items, "weighted_mean"),
            "agreement_using_maximum": compare(items, "maximum"),
        }

    # Consensus across blind respondents, on the places every one of them ranked.
    blind = {w: its for w, its in by_person.items() if its[0]["before"]}
    consensus = None
    if len(blind) >= 2:
        common = set.intersection(*({i["place"] for i in its} for its in blind.values()))
        common = sorted(p for p in common if scores.get(p))
        if len(common) >= 3:
            matrix = np.array([[rankdata([next(i["rank"] for i in its if i["place"] == p)
                                          for p in common])[k] for k in range(len(common))]
                               for its in blind.values()])
            mean_rank = matrix.mean(axis=0)
            items = [{"place": p, "rank": r} for p, r in zip(common, mean_rank, strict=True)]
            consensus = {"respondents": len(blind), "places": common,
                         "kendalls_w_between_respondents": kendalls_w(matrix),
                         "mean_expert_rank": {p: round(float(r), 2)
                                              for p, r in zip(common, mean_rank, strict=True)},
                         "agreement": compare(items, "weighted_mean"),
                         "agreement_using_maximum": compare(items, "maximum")}
    return {"status": "analysed",
            "analysed_on": dt.date.today().isoformat(),
            "respondents": respondents,
            "consensus_of_blind_respondents": consensus,
            "place_scores": scores,
            "unscorable_places": sorted(unscorable),
            "place_score_rule": f"population-weighted mean Priority of cells within "
                                f"{RADIUS_M} m (D31); maximum reported too"}


def write_report(result: dict, path: Path = OUT_DOC) -> None:
    lines = ["# Expert agreement (P6-01)", "",
             f"Analysed {result['analysed_on']} from `data/manual/expert_rankings.csv` by "
             "`uv run python -m pipeline.expert`. Generated, not hand-written.", "",
             f"**How a place is scored:** {result['place_score_rule']}.", "",
             "**Reading it:** Spearman ρ runs from −1 (the model ranks places in the "
             "opposite order to the field) through 0 (no relation) to +1 (the same "
             "order). The permutation p is the chance of agreement at least this strong "
             "if the model were guessing. With about a dozen places only strong "
             "agreement is detectable, so a non-significant result is weak evidence "
             "either way.", "", "## Each respondent", "",
             "| Respondent | Organisation | Blind? | Places | ρ | 95% CI (Fisher) | "
             "permutation p |", "|---|---|---|---|---|---|---|"]
    for who, r in result["respondents"].items():
        a = r["agreement"]
        cells = (["—", "too few places", "—"] if not a else
                 ["—", "undefined (flat ranking)", "—"] if "undefined" in a else
                 [f"{a['spearman']:+.2f}", f"{a['spearman_ci95_fisher']}",
                  f"{a['permutation_p_one_sided']:.3f}"])
        blind = "yes" if r["ranked_before_seeing_map"] else "**no, saw the map**"
        lines.append(f"| {who} | {r['organisation'] or '—'} | {blind} | "
                     f"{r['places_scored']} of {r['places_ranked']} | " + " | ".join(cells)
                     + " |")
    c = result["consensus_of_blind_respondents"]
    lines += ["", "## Consensus of blind respondents", ""]
    if c and c["agreement"] and "undefined" in c["agreement"]:
        lines += [f"{c['respondents']} respondents on {len(c['places'])} common places, "
                  f"Kendall's W = {c['kendalls_w_between_respondents']}. Their average "
                  "ranking is flat -- they cancel each other out -- so it cannot be "
                  "compared with the model. Read the individual results above."]
    elif c and c["agreement"]:
        a = c["agreement"]
        lines += [f"{c['respondents']} respondents on {len(c['places'])} common places. "
                  f"They agree with **each other** at Kendall's W = "
                  f"{c['kendalls_w_between_respondents']}. Their mean ranking agrees with "
                  f"the model at ρ = {a['spearman']:+.2f}, 95% CI "
                  f"{a['spearman_ci95_fisher']}, permutation p = "
                  f"{a['permutation_p_one_sided']:.3f}."]
    else:
        lines += ["Not computed: it needs at least two blind respondents ranking at least "
                  "three of the same scorable places."]
    if result["unscorable_places"]:
        lines += ["", "**Places written in without a location, so not scored:** "
                  + ", ".join(result["unscorable_places"])
                  + ". Add lat and lon to include them."]
    lines += ["", "## What happens next", "",
              "Samraj decides whether anything in the model changes (P6-01). Where a "
              "respondent disagrees strongly about a named place, read their notes before "
              "reading the number."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import and analyse expert rankings")
    parser.add_argument("--check", action="store_true", help="validate the file only")
    args = parser.parse_args()
    localities = read_localities()
    by_person = validate(read_rankings(), {p["name_en"]: p for p in localities})
    if not by_person:
        print("No expert rankings yet: data/manual/expert_rankings.csv has only its header.")
        print("Enter each completed form as described in docs/expert-ranking-import.md,")
        print("then run: uv run python -m pipeline.expert")
        return 0
    print(f"Rankings file valid: {len(by_person)} respondent(s).")
    if args.check:
        return 0
    result = analyse(by_person, load_cells(), localities)
    OUT_JSON.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    write_report(result)
    print(f"Wrote data/processed/{OUT_JSON.name} and docs/{OUT_DOC.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
