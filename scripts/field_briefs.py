"""P5-01: one A4 field brief per named locality in Landhi, as HTML, PDF and PNG.

Each brief covers the area within 500 m of the point OpenStreetMap marks for the
locality (pipeline/localities.py says why a radius and not a boundary). Everything on
it is read from site/data/, the same files the live map uses, so a brief cannot say
something the map does not.

The HTML is written to site/briefs/, then scripts/render_briefs.mjs prints each page to
PDF and PNG with Playwright's Chromium, so the output is identical on every machine and
testable. Both files must stay under 1 MB so they send on WhatsApp.

Run:
    uv run python scripts/field_briefs.py
"""

from __future__ import annotations

import csv
import html
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = SITE / "briefs"
LOCALITIES = ROOT / "data" / "processed" / "localities.csv"
RADIUS_M = 500
SITE_URL = "https://samrajukrani0-tech.github.io/karachi-heat-map/"
RAMP = ["#F6E3D0", "#D4B5A4", "#B18678", "#8E584B", "#6C2A1F"]
MAX_BYTES = 1_000_000

CSS = """
@page { size: A4; margin: 0; }
:root { --ink:#1A1C1E; --paper:#FFFFFF; --rule:#D8D2C9; --deep:#6C2A1F; --muted:#58554E; }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--paper); color: var(--ink);
  font: 9.8pt/1.35 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }
.page { width: 210mm; height: 297mm; padding: 11mm 13mm 9mm; display: flex;
  flex-direction: column; gap: 2.6mm; overflow: hidden; }
.kicker { font-size: 8.5pt; color: var(--muted); letter-spacing: .02em; margin: 0; }
h1 { font-size: 19pt; margin: 0; line-height: 1.1; }
.lede { font-size: 10.8pt; margin: 0; max-width: 165mm; }
.provisional { border-left: 3px solid var(--deep); padding: 1mm 0 1mm 3mm; font-size: 9pt;
  margin: 0; }
.grid { display: grid; grid-template-columns: 88mm 1fr; gap: 5mm; align-items: start; }
svg { width: 88mm; height: auto; border: 1px solid var(--rule); display: block; }
.key { font-size: 8pt; color: var(--muted); margin: 1mm 0 0; }
.swatches { display: flex; height: 3mm; margin-top: 1mm; }
.swatches span { flex: 1; }
h2 { font-size: 10.5pt; margin: 0 0 1mm; }
ul { margin: 0; padding-left: 4.5mm; }
li { margin: 0 0 .6mm; }
table { border-collapse: collapse; width: 100%; font-size: 8.4pt; }
th, td { text-align: left; padding: 0.8mm 2mm 0.8mm 0; border-bottom: 1px solid var(--rule); }
th { font-weight: 600; } td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
.box { border: 1px solid var(--rule); padding: 2mm 3mm; font-size: 8.3pt; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }
.write { border-bottom: 1px solid var(--rule); height: 5.5mm; }
footer { margin-top: auto; font-size: 7.2pt; color: var(--muted); border-top: 1px solid var(--rule);
  padding-top: 2mm; }
footer p { margin: 0 0 .8mm; }
.count { color: var(--muted); }
.next { margin-top: 3mm; }
"""


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def metres(lon1, lat1, lon2, lat2) -> float:
    """Haversine; at 500 m it agrees with UTM to far better than a cell width."""
    r = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def band(rank: int, max_rank: int) -> str:
    return ("Higher priority for support" if rank <= max_rank * 0.2 else
            "Middle of the range" if rank <= max_rank * 0.6 else
            "Lower priority for support")


def fill(rank: int, max_rank: int) -> str:
    q = math.ceil(rank / max_rank * 5)
    return RAMP[5 - min(max(q, 1), 5)]


def select(cells: list[dict], place: dict) -> list[dict]:
    lon, lat = float(place["lon"]), float(place["lat"])
    chosen = [c for c in cells
              if c["properties"]["h3"] == place["h3_cell"]
              or metres(lon, lat, *c["properties"]["c"]) <= RADIUS_M]
    return sorted(chosen, key=lambda c: c["properties"]["rank"])


def svg_map(cells, chosen, roads, place, max_rank) -> str:
    """Landhi in outline, this locality's areas coloured, the main roads for bearings."""
    lon0, lat0 = float(place["lon"]), float(place["lat"])
    k = math.cos(math.radians(lat0))
    xs = [x for c in cells for x, _ in c["geometry"]["coordinates"][0]]
    ys = [y for c in cells for _, y in c["geometry"]["coordinates"][0]]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    width = 1000.0
    scale = width / ((maxx - minx) * k)
    height = (maxy - miny) * scale

    def pt(x, y):
        return f"{(x - minx) * k * scale:.1f},{(maxy - y) * scale:.1f}"

    chosen_ids = {c["properties"]["h3"] for c in chosen}
    parts = [f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
             f'role="img" aria-label="Map of Landhi with the areas around '
             f'{html.escape(place["name_en"])} coloured by priority">',
             f'<rect width="{width:.0f}" height="{height:.0f}" fill="#FFFFFF"/>']
    for f in roads["features"]:
        major = f["properties"]["class"] in ("motorway", "trunk", "primary")
        pts = " ".join(pt(x, y) for x, y in f["geometry"]["coordinates"])
        parts.append(f'<polyline points="{pts}" fill="none" stroke="#B9B4AB" '
                     f'stroke-width="{2.6 if major else 1.2}"/>')
    for c in cells:
        p = c["properties"]
        ring = " ".join(pt(x, y) for x, y in c["geometry"]["coordinates"][0])
        if p["h3"] in chosen_ids:
            dash = ' stroke-dasharray="5 3"' if p["stability"] == "uncertain" else ""
            parts.append(f'<polygon points="{ring}" fill="{fill(p["rank"], max_rank)}" '
                         f'stroke="#1A1C1E" stroke-width="1.6"{dash}/>')
        else:
            parts.append(f'<polygon points="{ring}" fill="#EFEBE5" stroke="#FFFFFF" '
                         f'stroke-width="1"/>')
    cx, cy = pt(lon0, lat0).split(",")
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="#FFFFFF" stroke="#1F5E6B" '
                 f'stroke-width="4"/>')
    # 1 km scale bar and north marker, bottom left
    bar = 1000 / (111_320 * k) * k * scale
    y0 = height - 30
    parts.append(f'<line x1="30" y1="{y0:.0f}" x2="{30 + bar:.0f}" y2="{y0:.0f}" '
                 f'stroke="#1A1C1E" stroke-width="5"/>'
                 f'<text x="30" y="{y0 - 12:.0f}" font-size="26" fill="#1A1C1E">1 km</text>'
                 f'<text x="{width - 50:.0f}" y="50" font-size="30" fill="#1A1C1E">N ↑</text>')
    parts.append("</svg>")
    return "".join(parts)


def reasons(chosen) -> list[tuple[str, int]]:
    counts = Counter(r for c in chosen for r in c["properties"]["reasons"][:3])
    return counts.most_common(4)


def brief_html(place, chosen, cells, roads, meta, generated) -> str:
    max_rank = meta["distinguishable_ranks"]
    name = html.escape(place["name_en"])
    n = len(chosen)
    top = [c for c in chosen if c["properties"]["rank"] <= max_rank * 0.2]
    best = chosen[0]["properties"]["rank"]
    sure_in = sum(c["properties"]["stability"] == "confidently in" for c in chosen)
    unsure = sum(c["properties"]["stability"] == "uncertain" for c in chosen)
    if top:
        lede = (f"<strong>{len(top)} of the {n} areas</strong> within {RADIUS_M} m of "
                f"{name} are in Landhi's highest-priority fifth for heat support. The "
                f"highest ranks {best} of {max_rank}.")
    else:
        lede = (f"None of the {n} areas within {RADIUS_M} m of {name} is in Landhi's "
                f"highest-priority fifth. The highest ranks {best} of {max_rank}.")
    sure_out = sum(c["properties"]["stability"] == "confidently out" for c in chosen)
    if sure_in:
        confidence = (f"The model is confident that {sure_in} "
                      f"{'is' if sure_in == 1 else 'are'} in the top fifth")
    elif sure_out == n:
        confidence = "The model is confident that none of them is in the top fifth"
    else:
        confidence = "The model is not confident that any of them is in the top fifth"
    confidence += (f"; {unsure} {'moves' if unsure == 1 else 'move'} a lot when the "
                   "assumptions change (dashed outline)." if unsure else ".")

    rows = "".join(
        f'<tr><td class="n">{p["rank"]}</td><td>{band(p["rank"], max_rank)}</td>'
        f'<td>{p["stability"]}</td><td class="n">{p["lst"]:.1f}</td>'
        f'<td class="n">{p["people"]:,}</td><td class="n">{p["over60"] + p["under5"]:,}</td>'
        f'<td class="n">{round(p["green"] * 100)}%</td>'
        f'<td class="n">{p["dist_health"]:,}</td></tr>'
        for p in (c["properties"] for c in chosen))
    why = "".join(f'<li>{html.escape(r)} <span class="count">({k} of {n} '
                  f'areas)</span></li>' for r, k in reasons(chosen)) or \
        "<li>Below the Landhi average on every measure we track.</li>"
    provisional = ""
    if meta["weights_provisional"] or meta["model_incomplete"]:
        provisional = ('<p class="provisional"><strong>Provisional.</strong> The weights are '
                       'placeholders until they are set by the project, and distance to a '
                       'relief centre has no data yet because no centre has been verified '
                       'in person. Rankings may change.</p>')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — field brief — Karachi Heat Priority Map</title>
<style>{CSS}</style></head>
<body><main class="page">
<p class="kicker">FIELD BRIEF · LANDHI TOWN, KARACHI · HEAT SUPPORT</p>
<h1>{name}</h1>
<p class="lede">{lede} {confidence}</p>
{provisional}
<div class="grid">
<div>{svg_map(cells, chosen, roads, place, max_rank)}
<div class="swatches">{"".join(f'<span style="background:{c}"></span>' for c in RAMP)}</div>
<p class="key">Lower priority → highest priority, within Landhi. Circle: where
OpenStreetMap marks {name}. Grey: the rest of Landhi. Lines: main roads.</p></div>
<div>
<h2>What pushes these areas' scores up</h2><ul>{why}</ul>
<h2 class="next">Worth checking on the ground</h2>
<ul><li>Where do people go to cool down, and is there drinking water there?</li>
<li>How long are the power cuts here in the hot months?</li>
<li>Where do older people or young children live who may struggle in the heat?</li>
<li>Is the map wrong about anywhere here? That is the most useful thing to know.</li></ul>
</div></div>
<table><thead><tr><th scope="col" class="n">Rank</th><th scope="col">Priority</th>
<th scope="col">Confidence</th><th scope="col" class="n">Ground °C</th>
<th scope="col" class="n">People*</th><th scope="col" class="n">60+ / under 5*</th>
<th scope="col" class="n">Green</th><th scope="col" class="n">Clinic (m)</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="two">
<div class="box"><strong>What this cannot tell you.</strong>
*People are modelled, and the model counts about half the people the 2023 census found
in Landhi: compare areas, never read them as headcounts. Ground temperature is the
surface, not the air, and says nothing about humidity. Power cuts are not included,
although they are a large part of why heat harms people here. This describes areas, not
the people in them, and is never a verdict on a neighbourhood.</div>
<div class="box"><strong>Notes from the visit</strong>
<div class="write"></div><div class="write"></div><div class="write"></div>
<div class="write"></div></div>
</div>
<footer>
<p>Not an official warning system: for heatwave warnings follow the Pakistan
Meteorological Department and PDMA Sindh. Priority is a ranking within Landhi Town,
not a measure of risk on any absolute scale, and not a prediction of deaths.
"Areas" are hexagons of about 0.1 km² within {RADIUS_M} m of the OpenStreetMap point.</p>
<p>Generated {generated} from the data behind {SITE_URL} · Built with Claude Code as a
coding assistant. Research question, modelling decisions, weights and fieldwork by
Samraj Lal Ukrani. · Text CC BY 4.0 · data ODbL 1.0, © OpenStreetMap contributors;
surface temperature USGS Landsat; population Meta Data for Good (CC BY 4.0).</p>
</footer>
</main></body></html>
"""


def build(out: Path = OUT, generated: str | None = None) -> list[dict]:
    """Write the HTML briefs into ``out`` and return what was written (no rendering)."""
    doc = json.loads((SITE / "data" / "cells.geojson").read_text(encoding="utf-8"))
    roads = json.loads((SITE / "data" / "roads.geojson").read_text(encoding="utf-8"))
    with LOCALITIES.open(encoding="utf-8") as fh:
        places = list(csv.DictReader(fh))
    generated = generated or doc["metadata"]["generated"]
    if out.exists():
        shutil.rmtree(out)     # a place removed from OSM must not leave a stale brief
    out.mkdir(parents=True)
    written = []
    for place in places:
        chosen = select(doc["features"], place)
        name = slug(place["name_en"])
        (out / f"{name}.html").write_text(
            brief_html(place, chosen, doc["features"], roads, doc["metadata"], generated),
            encoding="utf-8")
        written.append({"name_en": place["name_en"], "slug": name,
                        "areas": len(chosen), "best_rank": chosen[0]["properties"]["rank"],
                        "top_fifth": sum(c["properties"]["rank"]
                                         <= doc["metadata"]["distinguishable_ranks"] * 0.2
                                         for c in chosen),
                        "cells": [c["properties"]["h3"] for c in chosen]})
    (out / "index.json").write_text(json.dumps(
        {"generated": generated, "radius_m": RADIUS_M, "briefs": written}, indent=1) + "\n",
        encoding="utf-8")
    return written


def write_index_page(written: list[dict], generated: str) -> None:
    """Rewrite the list on site/briefs.html between its two markers."""
    page = SITE / "briefs.html"
    text = page.read_text(encoding="utf-8")
    start, end = "<!-- briefs:start -->", "<!-- briefs:end -->"
    if start not in text or end not in text:
        raise SystemExit("site/briefs.html is missing its briefs markers")
    rows = "".join(
        f'<tr><th scope="row">{html.escape(w["name_en"])}</th>'
        f'<td class="num">{w["best_rank"]}</td><td class="num">{w["top_fifth"]} of '
        f'{w["areas"]}</td><td><span class="links"><a href="briefs/{w["slug"]}.html">View</a>'
        f'<a href="briefs/{w["slug"]}.pdf" download>PDF</a>'
        f'<a href="briefs/{w["slug"]}.png" download>Image</a></span></td></tr>'
        for w in sorted(written, key=lambda w: w["best_rank"]))
    block = (f'{start}\n<table class="briefs"><caption class="small muted">Generated '
             f'{generated}. Sorted by the highest-ranked area near each place.</caption>'
             '<thead><tr><th scope="col">Place</th><th class="num" scope="col">Highest '
             'rank</th><th class="num" scope="col">Areas in the top fifth</th>'
             f'<th scope="col">Brief</th></tr></thead><tbody>{rows}</tbody></table>\n{end}')
    before, rest = text.split(start, 1)
    after = rest.split(end, 1)[1]
    page.write_text(before + block + after, encoding="utf-8")


def main() -> int:
    written = build()
    doc = json.loads((OUT / "index.json").read_text(encoding="utf-8"))
    write_index_page(written, doc["generated"])
    print(f"Wrote {len(written)} HTML briefs to site/briefs/")
    node = shutil.which("node")
    if not node:
        print("node is not installed, so no PDF/PNG was rendered (npm ci first)")
        return 1
    subprocess.run([node, str(ROOT / "scripts" / "render_briefs.mjs")], check=True, cwd=ROOT)
    too_big = [p.name for p in OUT.glob("*.p[dn][fg]") if p.stat().st_size >= MAX_BYTES]
    if too_big:
        print(f"FAIL: over 1 MB: {too_big}")
        return 1
    for w in written:
        sizes = [(OUT / f"{w['slug']}.{ext}").stat().st_size // 1024 for ext in ("pdf", "png")]
        print(f"  {w['name_en']:<22} {w['areas']:>2} areas, best rank {w['best_rank']:>3}, "
              f"PDF {sizes[0]} kB, PNG {sizes[1]} kB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
