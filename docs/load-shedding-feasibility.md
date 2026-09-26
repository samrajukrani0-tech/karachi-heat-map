# Load-shedding exposure: feasibility study (P1-10)

**Date:** 2026-09-26 · **Status:** recommendation made, awaiting Samraj's decision (QUESTIONS.md Q9)

## Why this was attempted

This is the one indicator that comes from the field rather than from a dataset. In June
2024 Faisal Edhi said the deaths his foundation received came mostly from poorer workers'
neighbourhoods **hit by long power cuts** ([Bloomberg](https://bnnbloomberg.ca/karachi-sees-a-surge-in-deaths-as-heat-wave-sears-pakistan-1.2090293)).
A fan that stops working in a 43 °C afternoon is a plausible mechanism connecting heat to
harm, and no other indicator in this model captures it. PROMPT.md §6 therefore calls it
"worth a real attempt", gated behind this study.

## What K-Electric actually publishes

**Found:** a load-shed schedule PDF, cached at
`data/raw/kelectric/Load-Shed-Schedule-Ramadan26.pdf` and recorded in the manifest.

Its structure, read directly from the document:

| Feeder Name | Grid | 1st Cycle | 2nd Cycle | 3rd Cycle | 4th Cycle |
|---|---|---|---|---|---|
| SECTOR 10 RMU | KORANGI EAST | 0835~1105 | 1235~1535 | 1935~2205 | 0005~0205 |
| ZAFAR ICE | KORANGI EAST | 1035~1305 | 1435~1735 | 1935~2135 | 2305~0135 |
| MOMINABAD | BALDIA | 1005~1235 | 1405~1705 | 1935~2105 | 2235~0135 |

Measured from the document:

- **620 feeder rows** across **58 grid stations**
- **26 feeders on the LANDHI grid**; 81 rows mention Landhi, Korangi or Quaidabad
- **Daily outage: minimum 4.0 h, median 7.5 h, maximum 10.0 h**

So the *quantity* exists and it varies substantially — a 6-hour spread between the
best- and worst-served feeders. If it could be placed on a map it would be a strong
indicator.

## Why it cannot be placed on a map

**1. No geography is published.** The schedule gives a feeder name and a grid station.
It contains no coordinates, no boundaries, and no list of which streets a feeder serves.
K-Electric's own guidance is that a customer finds their feeder by entering a **13-digit
account number** into the KE Live app. That is a lookup from *account* to feeder, not
from *place* to feeder, and it cannot be run for 265 map cells.

**2. Feeder names are not reliably geocodable.** Some are place names that could be
located — `ZAMANABAD RMU`, `BURMI COLONY RMU`, `SECTOR 10 RMU`. Many are businesses or
landmarks: `ZAFAR ICE`, `OPEL LAB`, `ROTI PLANT`, `NOOR BHAI`, `HAFIZ SWEETS`,
`BARAF KHANA (Ex-ZAM ZAM ICE)`, `AMAZON`, `CAFE MILLAT`. Several are bare identifiers —
`36 B RMU`, `7 A RMU`, `J 1 AREA RMU`. Geocoding these would be guesswork, and OSM covers
only about 11% of Landhi's built area (D18), so it is a poor gazetteer for the attempt.

**3. Even a perfect point would not give a service area.** 26 feeders would have to be
spread across 265 cells. Assigning each cell to its nearest feeder — a Voronoi
tessellation — would **invent a boundary K-Electric has not published**, and there is no
way to validate it. §2.1 forbids inventing data, and a fabricated service area presented
as an exposure layer is exactly that.

**4. The schedule found is the wrong season.** This is the **Ramadan 2026** schedule
(roughly February–March 2026). The model covers the April–June hot season. Load-shedding
patterns change with demand, so even a perfectly mapped version of this document would
describe the wrong months.

**5. The site cannot be fetched automatically.** `ke.com.pk` resolves but presents a
**self-signed certificate**, so TLS verification fails; plain HTTP times out. Disabling
certificate verification to scrape a utility's website is not something this project will
do. The PDF above was reached through a search-result URL, which is not a reproducible
data source.

## Recommendation

**Do not build the indicator for v1.** Not because load-shedding is unimportant — the
measured 4–10 hour spread suggests it may matter more than several indicators that *are*
in the model — but because there is no honest route from the published data to a per-cell
value. Every available path requires inventing a service boundary.

State this plainly in the model report: **the mechanism Edhi actually named is the one
this model cannot see.**

## The v2 route, which is field-collected rather than scraped

This is a good candidate for the expert-ranking protocol (§7c) rather than for a dataset:

1. Ask a centre manager, or residents, which parts of Landhi lose power longest. People
   know this precisely; it structures their day.
2. Collect feeder names from a handful of K-Electric bills across different parts of
   Landhi. A bill ties a feeder name to a real address, which is the location link the
   published schedule omits.
3. With even 10–15 bills spread across the town, the 26 LANDHI-grid feeders could be
   partially located, and the schedule's outage hours attached to real places.

That is a fieldwork task with a clear method, not a data-processing task. It belongs
after v1.

## Sources

- K-Electric load-shed schedule PDF (cached; structure quoted above)
- Bloomberg on the June 2024 heatwave and power cuts, cited in PROMPT.md §1
