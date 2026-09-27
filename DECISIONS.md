# Decisions

Judgement calls belong to Samraj (PROMPT.md §5). Each entry records the question,
the options, Claude's recommendation and reasons, Samraj's decision in his words,
a status (approved / provisional / deferred), and the date.

---

## D1 — Hazard

**Question:** Which hazard does v1 map?

**Options:**
1. Heat now, monsoon flooding as a later version.
2. Monsoon flooding instead.
3. Both hazards in v1.

**Recommendation (Claude):** Option 1, heat.
- Heat hazard is measurable from open data end to end: Landsat 8/9 Collection 2
  Level-2 surface temperature, modelled population, OSM access.
- Credible flood modelling needs Karachi drainage and nullah data that is not
  openly published; the model would rest on unverifiable assumptions.
- Edhi Foundation's own June 2024 experience is a heat event, which gives an
  honest, citable face-validity check.
- Decided 2026-09-26, so the April–June 2027 heat season is about seven months
  out — the right lead time for a tool whose purpose is pre-positioning supplies
  before the season, and enough time to get field feedback over the winter.
- Main alternative (flooding) would need a DEM-based proxy such as HAND or TWI;
  the maths is fine but the evidence base is much weaker.
- What would change this: access to a real KMC/KWSB drainage or nullah dataset,
  or a contact working in flood response.

**Samraj's decision:** "Heat, flooding later" — map heat for v1, keep monsoon
flooding as v2.

**Status:** approved
**Date:** 2026-09-26

---

## D2 — Pilot area

**Question:** Which locality is the pilot area?

**Evidence gathered in Phase 0** (methods repeated properly in P1-01/P1-06):
- Areas computed from OSM administrative boundary relations (admin_level=7),
  reprojected to EPSG:32642:
  Landhi Town 25.37 km² (rel 16350631), Shah Faisal Town 14.93 km² (rel 16350629),
  Malir Town 16.71 km² (rel 16351913), Korangi Town 74.15 km² (rel 16350630),
  Bin Qasim Town 580.09 km² (rel 16351914).
- Population: Korangi District 3,128,971 and Malir District 2,432,248 at the
  2023 census (census date 2023-03-01), via citypopulation.de citing the
  Pakistan Bureau of Statistics. Not split by town — P1-06 does that per cell.
- OSM health facilities (amenity=hospital|clinic|doctors) inside each town:
  Korangi 56, Malir 41, Shah Faisal 39, Landhi 32.
- OSM Edhi/Saylani-named objects inside each candidate town: **zero**. The query
  is sound — citywide it returns 55 such objects, several of them false matches
  ("Edhi Interchange", "Medhi Manji Lab"). Consequence: there is no usable open
  data on relief centres in the pilot area, so data/manual/centres.csv (P1-09)
  is the only source and must be verified in person.
- June 2024 reporting, read directly: Dawn, 25 June 2024,
  https://www.dawn.com/news/1841754 — names Landhi as an origin of a body
  brought to an Edhi mortuary, and records Edhi's Korangi mortuary receiving
  10 bodies against a normal 5–6. Express Tribune story 2473712 returned HTTP
  403 and has NOT been read; nothing from it is cited yet (see QUESTIONS.md Q1).

**Options:** Landhi Town; Korangi Town; Shah Faisal Town; defer until a relief
centre contact is secured.

**Recommendation (Claude):** Landhi Town — inside the 10–60 km² band, ~242 cells
at H3 resolution 9, named in verified June 2024 reporting, dense residential plus
the Landhi industrial estate, and reachable from DHA along Korangi Road. Main
alternative: Korangi Town, which has a named Edhi facility but is 74 km² and
would need a documented clip to its built-up area.

**Samraj's decision:** "Landhi Town — 25.4 km²".

**Status:** approved
**Date:** 2026-09-26

**Follow-up:** if his contacts (Nadeem Ghani at Nixor College, or his uncle) open
a door at a centre outside Landhi, revisit this entry rather than silently
stretching the boundary.

---

## D3 — Grid resolution

**Question:** What H3 resolution does the analysis grid use?

**Options for Landhi Town (25.37 km²):**
- res 8: ~0.74 km²/cell, ~34 cells, edge ~460 m
- res 9: ~0.105 km²/cell, ~242 cells, edge ~174 m
- res 10: ~0.015 km²/cell, ~1,690 cells, edge ~66 m

**Recommendation (Claude):** resolution 9. Landsat's TIRS instrument senses at
about 100 m and is only delivered resampled to 30 m, so a cell narrower than
~100 m would display structure the sensor never measured — false precision
(§2.1). A res-9 hexagon (edge ~174 m) sits just above that floor. It also
averages roughly a hundred Meta 30 m population pixels per cell, and 242 cells
keeps the site's data payload far inside the 1.5 MB budget. Res 8 is defensible
on data grounds but 34 cells is too coarse to direct a field team to a street,
and would leave the Phase 4 allocation planner almost no choices.

**Samraj's decision:** "Resolution 9 — ~0.105 km²".

**Status:** approved
**Date:** 2026-09-26

---

## D4 — Indicators

**Question:** Which indicators go into the index, including §6's optional ones?

**Approved set (8):**
| Indicator | Dimension | Notes |
|---|---|---|
| Hot-season daytime LST, mean °C | Hazard | April–June Landsat 8/9 C2 L2 cloud-masked median composite |
| People per cell | Exposure | `log1p` transform |
| Share aged 60+ | Vulnerability | Meta demographic layers; zero-population rule tested |
| Share under 5 | Vulnerability | as above |
| Building footprint fraction | Vulnerability | Google Open Buildings / MS ML footprints, OSM fallback |
| Lack of green cover | Vulnerability | ESA WorldCover 10 m and/or Sentinel-2 NDVI |
| Distance to nearest health facility | Vulnerability | OSM; circuity factor documented if straight-line |
| Distance to nearest verified relief centre | Vulnerability | data/manual/centres.csv only; also used in allocation (note the double use in the model report). Blocked on QUESTIONS.md Q2 |

Per-cell LST 90th percentile is still computed and shown in the cell panel, but is
**not** an index indicator: it is strongly correlated with the mean, so indexing
both would double-count hazard.

**Rationale for a short list:** AHP requires n(n−1)/2 pairwise comparisons within a
dimension. Six vulnerability indicators is 15 comparisons plus 3 across dimensions
(~18 judgements), which is realistically consistent (CR < 0.10). Eight would be 28
and consistency becomes unlikely. Each added indicator costs consistency.

**Dropped for v1:**
- **Night-time LST (P1-05).** MODIS night LST is 1 km, about 25 pixels over the
  whole 25.37 km² pilot area spread across 242 cells, so nearly all between-cell
  variation would be an artefact of area-weighting. To be marked `dropped` in
  features.json with this reason, and stated in the model report's limitations:
  night heat matters medically (cumulative load when nights stay near 30 °C) but
  could not be resolved at this scale. ECOSTRESS (~70 m) noted as a v2 candidate.
- **Relative Wealth Index.** ~2.4 km tiles, four or five covering all of Landhi;
  near-constant across cells, and costs an AHP comparison for no information.

**Kept as a gated study:**
- **P1-10 load-shedding feasibility.** Write docs/load-shedding-feasibility.md on
  what K-Electric publishes and whether feeder/area names can be matched to cells
  reliably. Build the indicator only if Samraj approves after reading it. This is
  the mechanism Faisal Edhi named in June 2024, so it deserves an honest attempt.

**Samraj's decisions:** "Mean in the index, p90 shown in the panel"; "Drop [night
heat] from v1, record the reason"; keep only the "Load-shedding feasibility study".

**Status:** approved
**Date:** 2026-09-26

---

## D5 — Normalisation

**Question:** How is each indicator normalised to 0–1 (1 = more risk)?

**Note:** P2-01 implements both methods either way, because §7's sensitivity
analysis swaps between them. D5 chooses the headline method; the other becomes
the robustness check.

**Recommendation (Claude):** robust min–max — clip at the 5th and 95th percentile
(about 12 of 242 cells at each tail), then scale linearly to 0–1. It preserves
spacing between cells, so a cell twice as far from a clinic reads as twice as far,
while clipping prevents a single extreme cell (the Landhi industrial estate will
produce some) from compressing everything else.

Percentile rank was the main alternative: immune to outliers, but it discards
magnitude by construction, so forty cells within a few tenths of a degree would be
spread across the full 0–1 range and the map would show differences that are
really measurement noise.

**Known consequence, resolved in D6:** robust min–max assigns exactly 0 to cells at
or below the 5th percentile. Under geometric aggregation that would force Priority
to 0 regardless of the other dimensions.

**Samraj's decision:** "Robust min–max, clip 5th/95th".

**Status:** approved
**Date:** 2026-09-26

---

## D6 — Combining dimensions

**Question:** How are Hazard, Exposure and Vulnerability combined into Priority?

**Recommendation (Claude):** geometric, Priority = (H·E·V)^(1/3).

Concrete argument: the Landhi industrial estate will produce cells with hot roofs,
no green cover and almost no residents — H ≈ 1, V ≈ 0.8, E ≈ 0. An equal-weight
arithmetic mean scores that 0.6 and ranks it near the top, i.e. it sends water to an
empty factory yard. The geometric mean scores it 0. Arithmetic aggregation lets one
dimension compensate for the absence of another; for risk, where all three must be
present for harm to occur, that compensation is the failure mode. By AM–GM the
geometric mean never exceeds the arithmetic one, so this is also the more cautious
choice.

Honest cost: geometric aggregation is unforgiving near zero, so cells with small
populations are heavily penalised. This goes in the model report's limitations.

**Samraj's decision (D6a):** "Geometric: (H·E·V)^⅓".

**D6b — zero floor.** Robust min–max (D5) assigns exactly 0 to the bottom 5% of
each indicator, which under multiplication forces Priority to 0.
- **Decision:** floor **H and V** at 0.01 before aggregation; leave **E unfloored**.
- Reason: H = 0 only means "coolest 5% within Landhi" — those cells are still around
  40 °C in June, so a zero is a statistical artefact of the normalisation, and the
  same argument applies to V. E = 0 means nobody lives there, which is a real
  absence and should genuinely zero the Priority.
- The floor value is documented, unit-tested, and varied in the §7 sensitivity
  analysis.

**Also computed regardless:** Intensity = √(H·V), the per-person view, for the
equity discussion in the model report.

**Status:** approved
**Date:** 2026-09-26

---

## D7 — Weights

**Question:** What does the AHP tool weight, and whose judgement goes in?

**Discrepancy found in PROMPT.md:** §5 D6 writes Priority as H^(1/3)·E^(1/3)·V^(1/3)
with fixed equal exponents, while D7 says AHP sets the dimension weights. Both can
only hold if the formula generalises to a weighted geometric mean,
H^wH · E^wE · V^wV with Σw = 1, which reduces to the cube root when weights are
equal. §7 of PROMPT.md should state this explicitly (queued for amendment).

**Recommendation (Claude), deviating from PROMPT.md:** use AHP for the six
**Vulnerability** weights only, and keep the three dimension exponents fixed at 1/3.
- In a multiplicative model an exponent is an elasticity ("a 1% rise in H raises
  Priority by w_H %"), not an importance. AHP elicits importance on Saaty's 1–9
  scale, and that does not map onto an elasticity.
- The question is also close to meaningless here: heat and people are not
  substitutes to be traded off, they are jointly required — which is precisely why
  the model is multiplicative.
- Within Vulnerability the six indicators combine as a weighted **arithmetic** mean,
  they genuinely do trade off, and "is distance to a clinic more important than the
  share of over-60s?" is a question a field coordinator has a real opinion about.
  That is AHP's proper domain: 15 comparisons, CR reported.
- The sensitivity analysis still varies the dimension exponents, so the report shows
  the ranking does not hinge on the equal-1/3 choice.

**Samraj's decisions:** D7a "Vulnerability indicators only; dimensions stay equal at
⅓". D7b "You now, a field coordinator later" — Samraj runs the AHP himself in Phase 2
(P2-02b); after the field visit it is re-run with a centre manager, and both weight
sets plus the resulting rank shift are reported (Phase 6).

**Until P2-02b:** equal weights within Vulnerability, labelled provisional in the
data and on the site.

**Status:** approved
**Date:** 2026-09-26

---

## D8 — Allocation settings

**Question:** What is distributed, how much per person, who counts as in need, what
is the maximum service distance, and is there a minimum share for top-priority cells?

**Provisional values (to be written to config/allocation.yaml):**
| Setting | Value | Reason |
|---|---|---|
| Commodity | one per scenario; v1 = drinking water (L/day) and ORS (sachets/day) | the LP solves one commodity at a time; "heat kits" is excluded until someone defines the contents, because need cannot be computed for an undefined unit |
| Units per person | water 3 L/day; ORS 1 sachet/day | Sphere's minimum survival allocation for drinking and food is roughly 2.5–3 L/person/day. **Recalled from memory, NOT verified** — P4-02 must check the Sphere Handbook before this figure is cited anywhere |
| In need | residents aged 60+ plus children under 5 | avoids circularity: Priority is already the LP's objective, so defining need from Priority too would count the model's own judgement twice and make the allocation look well-targeted by construction. Age shares are measured independently of the model |
| Max service distance D | 5 km road distance (straight-line × 1.3 circuity), sensitivity at 3 km and 8 km | plausible delivery-van radius in Karachi traffic; a centre manager will have the real figure |
| Minimum share | yes — top priority quintile receives ≥ 25% of allocated supply, as a soft constraint with a penalty | without it a remote high-priority cell can be starved purely by distance from stock, and the ε tie-break will not prevent it. Better to state the equity commitment than to discover it was missing |

**Samraj's decision:** "Accept as provisional."

**Status:** **provisional** — every value is revisited after the field visit. Until
then the site labels allocation scenarios as illustrative.
**Date:** 2026-09-26

---

## D9 — Languages

**Question:** Which languages does the site ship in?

**Recommendation (Claude):** English and Urdu, per PROMPT.md §9. Half of the stated
audience — field coordinators — read Urdu more comfortably than English.

**Samraj's decision:** "English only for v1."

**Consequences, recorded rather than argued:**
- P3-07 (Urdu string set) and P3-07b (Urdu reviewed) are **dropped for v1**. This
  also removes the release blocker, so v1.0.0 no longer waits on a string review.
- The §10 Playwright check "Urdu flips to RTL and key strings change" leaves the
  gate list. It is removed because the feature was dropped by decision, **not**
  because it failed (§2.2).
- P5-01 field briefs and P5-03 the NGO one-pager become English only.
- config/indicators.yaml keeps its `name_ur` and `reason_ur` fields, left empty.

**Mitigation applied anyway (no cost):** all UI strings live in `site/i18n/en.json`
rather than hard-coded in HTML, and `dir` is driven by the language setting. Adding
Urdu later is then a translation task, not a rewrite.

**Status:** approved
**Date:** 2026-09-26

---

## D10 — Licences

**Question:** What licences apply?

**Decision:** three licences.
- **Code:** MIT (`LICENSE`).
- **Docs and site text:** CC BY 4.0 (`LICENSE-docs`).
- **data/processed:** **ODbL 1.0** (`LICENSE-data`) with OpenStreetMap attribution.

**Reason for the third one, which PROMPT.md does not mention:** two indicators
(distance to nearest health facility, and OSM building footprints if used as the
fallback) are derived from OpenStreetMap, which is ODbL 1.0. ODbL's share-alike
clause covers *derived databases*, so `indicators.parquet` is arguably a derived
database and releasing it under CC BY 4.0 would be a licence breach rather than an
etiquette lapse. Each dataset additionally keeps its own licence, documented in
`data/SOURCES.md`.

**Samraj's decision:** "MIT code, CC BY 4.0 docs, ODbL data".

**Status:** approved
**Date:** 2026-09-26

---

## D11 — Public identity

**Question:** Repository name, visibility, how Samraj's name appears, and what
contact the site shows.

**Samraj's decisions:**
- **D11a:** repository `karachi-heat-map`, **public** from the start. Descriptive,
  not locked to Landhi, and the public commit history is itself evidence of
  sustained work.
- **D11b:** **full name, school not named** — "Samraj Lal Ukrani" on the About page,
  in the README and in `CITATION.cff`. Nixor College is deliberately **not** named:
  it adds nothing for an NGO reader and publishes a minor's weekday location
  permanently and searchably.
- **D11c:** **no contact shown at all.** Consistent with handing the tool over in
  person rather than online.

**Consequence of D11c:** there is no online entry point for feedback from anyone
Samraj has not met. P5-03's one-pager therefore leaves a blank line for him to write
a contact by hand when he hands it to a centre, and the About page must not imply a
channel that does not exist.

**Related caution (raised in the D2 discussion):** access may come via a political
contact. The framing stays "decision support for relief teams" throughout; the tool
never ranks neighbourhoods as good or bad (§2.5), and no political affiliation
appears anywhere in the repo or on the site.

**Status:** approved
**Date:** 2026-09-26

---

## D12 — AI-assistance disclosure

**Question:** How is the use of an AI coding assistant disclosed?

**Samraj's decision:** "README and About page."

**Wording to use in both:** "Built with Claude Code as a coding assistant. Research
question, modelling decisions, weights and fieldwork by Samraj Lal Ukrani."

**Reason:** research programmes and competitions increasingly require the
disclosure, and stating it plainly is a far stronger position than being asked about
it later.

**Status:** approved
**Date:** 2026-09-26

---

## D2 — correction to the evidence (2026-09-26)

The relief-centre finding recorded under D2 was produced by an OSM query matching only
the spellings `Edhi` and `Saylani`. A widened re-run (all spelling variants, Urdu forms,
plus welfare, charity and ambulance-station tags, over a bounding box extending about
12 km around Landhi) found a Saylani branch that OSM records as **"Silani Welfare -
Korangi 4"** — a spelling the original pattern could not have matched.

**The conclusion is unchanged:** zero relief facilities inside the Landhi Town boundary,
now established across 133 candidate objects rather than a narrow name match. **The
method was weaker than first stated**, and this entry records that rather than quietly
re-running it. D2 itself does not change; Landhi remains the pilot area.

Candidates found near Landhi are in `data/manual/centre_candidates.csv`, all
`UNVERIFIED`. None enters the model (PROMPT.md §6).

---

## D13 — Which organisations count as a relief centre (2026-09-26)

**Question:** PROMPT.md §1 scopes the tool to "a local Edhi Foundation centre or Saylani
Welfare". Should `centres.csv` accept other relief organisations?

**Evidence:** on 24 June 2024, Chhipa volunteers moved 12 of the 15 bodies recovered
from Karachi streets; Edhi moved 3 (Express Tribune, text supplied by Samraj — see
QUESTIONS.md Q1). OSM places a Chhipa ambulance point about 100 m from an Edhi one on
Landhi's eastern edge; nothing from Edhi or Saylani lies inside the Landhi boundary.

**Recommendation (Claude):** widen the list, and record what each facility can do.
- The decisive argument is measurement validity, not convenience. `dist_centre` is meant
  to measure *how far this area is from organised help*. Restricting it by organisation
  makes it measure "distance to a facility run by one of two particular charities",
  which is not a property of the neighbourhood. A household 200 m from a Chhipa
  ambulance is not vulnerable because of the logo on the door.
- But the index and the allocation planner want **different lists**, which is the real
  content of PROMPT.md §6's note about `dist_centre` being used twice:
  - the **index** asks "how far is help?" — an ambulance standby point counts fully;
  - the **allocation LP** treats each centre as holding stock s_j — an ambulance standby
    point holds none, and feeding it in would allocate litres of water to a kerbside.

**Decision:** `centres.csv` accepts any verified relief facility regardless of
organisation, and gains two columns:
- `role`: one of `ambulance_standby`, `distribution_point`, `clinic`, `morgue`,
  `office`, `other`
- `can_hold_stock`: `yes` / `no` / `unknown`

The vulnerability indicator (P1-09) uses every verified facility. The allocation planner
(P4-01) draws stock only from `can_hold_stock = yes`, proved by a test.

**Objection considered and resolved:** a one-pager written for Edhi's specific workflow
lands harder than a generic one. But P5-03 is a Phase 5 feature — by then Samraj will
know who said yes, and it gets written for them. Widening the data model now does not
commit him to a generic pitch later.

**Samraj's decision:** "Any relief org, plus a role column."

**Status:** approved
**Date:** 2026-09-26

---

## D14 — Face validity for Landhi (2026-09-26)

**Question:** §7 validation (b) checks the model against cited June 2024 reporting. Of
roughly 13 localities named across the Dawn and Express Tribune reports, exactly **one**
is inside Landhi (near Landhi Hospital's Chowrangi). How should P2-05 handle that?

**Recommendation (Claude):** report the single mention honestly, label the check weak,
and let the expert-ranking protocol (§7c) carry the validation weight.

**Why not the city-scale alternative** (extend the model over Karachi's towns and
correlate rank against reported deaths) — three reasons, recorded so the argument is not
re-made from scratch later:
1. **Near-circular.** Priority already contains Exposure. More people means more deaths,
   so a correlation with raw counts would largely re-discover population on both sides.
   The non-circular form compares incidents **per capita** against **Intensity** =
   √(H·V), which is why Intensity is computed at all.
2. **The sample cannot carry a statistic.** About 20 located incidents across 25 towns
   leaves most towns at zero or one. Bootstrap CIs on Spearman ρ would almost certainly
   span zero. Reporting a ρ from that would be noise presented as evidence (§2.1).
3. **The sample is biased by the response itself.** Street-death reports depend on where
   ambulances operate and where bodies are found in public, so Orangi's prominence may
   partly reflect Chhipa and Edhi coverage rather than heat. Validating against a sample
   shaped by the organisations being helped is a confound that does not go away.

A workable city-scale version would need Samraj to compile a geolocated incident list
from the full 20–26 June 2024 reporting (perhaps 50–100 incidents). That is his reading
to do, not Claude's — several of those sites block automated fetching — and it belongs
after v1.

**What P2-05 does instead:** geocode the one reported Landhi incident to a cell and
report that cell's priority rank. Top quintile is mild support; **bottom quintile is a
genuine warning sign**. A check that can only confirm is not a check.

**Samraj's decision:** "Honest weak check; expert ranking is the real test."

**Status:** approved
**Date:** 2026-09-26

---

## D15 — Grid inclusion rule (2026-09-26, PROVISIONAL)

**Question:** Which H3 cells belong to the grid, given that a hexagon on the edge is
partly inside Landhi and partly in a neighbouring town?

**The conflict found in P1-02.** Two statements written in Phase 0 cannot both hold:
- `config/area.yaml`: include a cell when its centre is inside, **or** when ≥ 50% of its
  area is inside;
- PROMPT.md §12 P1-02: the cells must cover **≥ 99%** of the boundary.

Measured over the real boundary:

| rule | cells | coverage | hexagon area | overhang |
|---|---|---|---|---|
| centre inside only | 248 | 96.552% | 25.343 km² | −0.027 |
| centre **or ≥50% area** | 248 | 96.552% | 25.343 km² | −0.027 |
| centre or ≥25% area | 265 | **99.115%** | 27.080 km² | +1.710 |
| centre or ≥10% area | 276 | 99.826% | 28.204 km² | +2.834 |
| any intersection | 290 | 100.000% | 29.634 km² | +4.264 |

Two things fall out of that table. First, **the 50% clause was dead code**: not one cell
qualified under it. For a boundary that is locally a straight line, a hexagon has ≥ 50%
of its area inside exactly when its centre is inside, so the "OR" could never add
anything. Second, the centre rule tops out at 96.55%, so it could never meet the 99%
criterion.

**Decision:** the 99% criterion is from PROMPT.md and is not negotiable (§2.2), so the
inclusion rule changes instead:
1. `min_area_fraction` drops from 0.50 to **0.25** — 265 cells, 99.115% coverage, the
   least overhang of any option that clears the bar.
2. **Every indicator is computed over the clipped geometry** (cell ∩ boundary), never
   the whole hexagon. The 1.935 km² of hexagon lying outside Landhi is therefore
   excluded from every measurement, so no cell can report a neighbouring town's heat or
   population. `clipped_area_km2` is stored per cell and `pipeline.grid.clip()` is the
   shared helper.

**Why 0.25 and not a smaller threshold that would cover more.** It is not only the
minimum that clears the criterion; it also has an independent justification. A quarter
of a res-9 hexagon is about 0.026 km², which at Landhi's density is on the order of 700
people and about 28 Meta population pixels (30 m). At a 3% threshold an edge cell would
hold roughly 3 pixels, and its indicator values would be noise dressed as a measurement.
The threshold is a floor on how much real evidence a cell must contain.

**Cost, stated honestly:** 0.885% of Landhi — thin slivers along the edge — is not
covered by any cell. This belongs in the model report's limitations.

**Samraj's decision (2026-09-26):** "confirmed, keep the 0.25 inclusion threshold (265
cells, 99.115% coverage)."

**Status: approved.**
**Date:** 2026-09-26

---

## D16 — Population source, and a serious undercount (2026-09-26, PROVISIONAL)

**Question:** Meta or WorldPop for the Exposure indicator, and does either agree with an
independent figure?

**Comparison, measured:**

| Source | Resolution | Pixels/cell | Landhi total | vs census |
|---|---|---|---|---|
| Meta HRSL v1.5 (2020) | ~31 m | median 119 | 295,132 | **0.43×** |
| WorldPop constrained (2020) | ~93 m | median 13 | 308,105 | **0.45×** |
| **2023 census, Landhi Town** | — | — | **681,293** | 1.00 |

Per-cell agreement between the two sources: **Spearman ρ = 0.834**, Pearson r = 0.866.

**Source chosen: Meta.** At H3 resolution 9 a cell is 0.105 km². Meta gives a median of
119 pixels per cell; WorldPop gives 13, and reports 47 cells as empty against Meta's 21.
WorldPop's 93 m pixels are simply too coarse to describe a cell this size. The two totals
differ by only 4.4%, so resolution is the deciding factor, not level.

**The undercount, and what it does and does not mean.**

Both sources fall far outside the documented 25% tolerance, so P1-06 takes the "or the
gap explained" branch of its acceptance criterion. The gap was diagnosed rather than
assumed:

| Region | Meta | WorldPop | 2023 census | ratio |
|---|---|---|---|---|
| Landhi Town (25.37 km²) | 297,527 | 310,338 | 681,293 | 0.44 / 0.46 |
| Korangi District (114.5 km²) | 1,806,408 | 1,928,437 | 3,128,971 | 0.58 / 0.62 |

The shortfall is **systematic across the whole district**, so it is not an artefact of
our boundary — the pilot area is the right shape, and both models undercount. Likely
causes: both are anchored to pre-2023 census baselines, and both infer population from
building footprint *area*, which understates multi-storey and dense informal housing.

**Why this does not invalidate the index.** Priority ranks cells *within* Landhi, and
normalisation (D5) is relative. A uniform scale factor cancels exactly: multiply every
cell by 2.3 and the ranking is unchanged.

**Why it still matters, in two specific ways.**
1. **The bias is not uniform.** Landhi is undercounted worse (0.44) than the district
   average (0.58), which suggests denser and more informal areas are undercounted more.
   If that pattern also holds *within* Landhi, the densest cells are under-ranked —
   precisely the wrong direction for a tool meant to find where support is needed first.
   The ρ = 0.834 agreement between two models sharing the same methodology is **not**
   evidence against this: they would agree while both being wrong the same way.
2. **Absolute supply quantities are underestimates.** D8 defines need from
   age-vulnerable population, which inherits this undercount. A centre planning water for
   300,000 people in a town of 681,000 under-supplies by more than half. The allocation
   planner must therefore present **shares and priorities**, and state the undercount
   wherever an absolute quantity appears.

**What is explicitly not done:** the data is not rescaled to match the census (§2.1
forbids adjusting data to hit a figure), and a uniform rescale would not fix a
non-uniform bias anyway.

**Samraj's decision (2026-09-26):** "yes, keep Meta as the population source. Use shares
and relative priorities only — never absolute litre or supply totals — and state the
undercount wherever a total appears." The presentation rule is recorded as **D21**.

**Status: approved.**
**Date:** 2026-09-26

---

## D17 — Meta's age shares carry no within-Landhi signal (2026-09-26, PROVISIONAL)

**What was found.** P1-07 produced `share_over60` and `share_under5` as specified. On
inspection they are not spatial demography at all:

| Check | Result |
|---|---|
| Correlation between the two shares | **−1.0000** |
| Cells at the modal `share_over60` value | 132 of 244 (54%); a second value holds 77 more |
| Distinct values (4 dp) | 28 for over-60, 31 for under-5, but 86% of cells sit on two |
| Sum of the two shares | 0.15291 to 0.15441 — a range of **0.0015** |
| Coefficient of variation of that sum | **0.0045** (LST 0.028, population 0.994) |

Meta's age layers apply an **administrative-unit age profile** to the population raster.
Over Landhi that means essentially two zones, each with a fixed age structure. The two
shares are therefore the same binary variable with opposite signs, and their sum is
constant.

**Why this matters to the model, concretely.** Both indicators have direction +1 (higher
= more risk) and would sit in the same weighted arithmetic mean for Vulnerability. Being
exactly anti-correlated, a cell high in one is proportionally low in the other, so
together they contribute a near-constant amount to V — while still consuming two of the
six weights and diluting the four indicators that do carry information. A combined
dependency ratio does not rescue them, because the sum is the thing that is constant.

**This is the same failure mode D4 already ruled on** for night-time LST and the Relative
Wealth Index: a source too coarse to vary within a 25 km² pilot area. The difference is
that this one could not be predicted from the resolution — it had to be measured.

**Claude's recommendation:** drop `share_over60` and `share_under5` from the index for
v1, leaving Vulnerability with four indicators (built fraction, lack of green cover,
distance to health facility, distance to relief centre). AHP then asks 6 pairwise
comparisons instead of 15, which also makes CR < 0.10 easier to achieve.

**Important distinction — the counts survive.** Only the *shares* are uninformative. The
**counts** (`people_over60`, `people_under5`) vary with population and are exactly what
D8's need definition uses, so Phase 4 is unaffected. They are written to
`data/processed/age_cells.csv` and retained.

**What the report must say.** Age is among the strongest individual risk factors in heat
mortality, and this project cannot map it within Landhi. That is a real limitation, not a
tidy simplification. Partial compensation: the expert-ranking protocol (§7c) lets field
staff bring knowledge the data lacks.

**Samraj's decision (2026-09-26):** "drop both age shares". Applied: both removed from
`config/indicators.yaml` (moved to `dropped` with the reason), Vulnerability's weights in
`config/weights.yaml` rebalanced to four indicators at 0.25 each, and the D4 indicator-count
test updated from 8 to 6 with this decision cited.

**Status: approved.** P1-07 itself passes: it produced the shares, in [0, 1], with the
zero-population rule implemented and tested, exactly as specified.
**Date:** 2026-09-26

---

## D18 — Built-up surface from WorldCover, not building footprints (2026-09-26, PROVISIONAL)

**Question:** PROMPT.md §6 names Google Open Buildings or Microsoft Global ML Building
Footprints for the built indicator, with OSM as the fallback. Which is used?

**What was tried.** Microsoft Building Footprints is on the Planetary Computer
(`ms-buildings`, ODbL 1.0) and covers Pakistan. Its asset is an `abfs://` Azure path,
which needs `adlfs` → `azure-storage-blob` → `cryptography`. `cryptography` 50.0.1 ships
**no x86_64 macOS wheel** and falls back to building from source with a Rust toolchain —
the same abandonment of Intel Macs that forced the `h3 < 4.4` pin. Installing Rust is a
system-wide install, which §2.7 says to ask about, and pinning a security library
backwards to read a building dataset is a poor trade.

**Decision:** use **ESA WorldCover 10 m (2021, v200)** for both indicators — green cover
and built-up surface — read directly from the Planetary Computer with no extra
dependency. Median 1,314 pixels per cell, so the fractions are well resolved.

**An honest naming point.** WorldCover class 50 is *built-up surface*, which includes
roads, yards and paving, not only building roofs. This is a different quantity from a
building footprint fraction. For heat vulnerability it is arguably the better one —
impervious surface drives heat retention — but it is not what §6 asked for, so the
indicator is named "Built-up surface" in `config/indicators.yaml` and the model report
must not describe it as building footprints.

**Result:** built fraction min 0.000, median 0.692, max 0.991; green fraction min 0.000,
median 0.131, max 1.000.

**Cross-validation, unplanned and reassuring.** P1-04b flagged five unexplained cool
cells for P1-08 to explain. They turn out to be **93–100% green** against a pilot median
of 13.1%. Landsat thermal infrared (2022–2026) and ESA land classification (2021) are
entirely independent datasets, and they agree on where Landhi's vegetation is.

**A number that reframes an earlier finding.** OSM building polygons cover **6.01%** of
Landhi against WorldCover's 54.7% built-up — OSM captures roughly **11%** as much built
area as exists. Only 711 building polygons are mapped in a town of several hundred
thousand people. This is recorded because it changes how the Phase 0 relief-centre result
should be read: OSM listing no Edhi or Saylani facility in Landhi is **not evidence they
are absent**, it is evidence that OSM barely describes Landhi at all. P1-09 must carry
the same caveat for health facilities.

**Status: PROVISIONAL** — a source substitution, which §6 says to log as provisional.
**Date:** 2026-09-26

---

## D19 — Drop `built_fraction` (2026-09-26)

**Question:** After D17 left Vulnerability with four indicators, `built_fraction` and
`lack_green` were measured at about **+0.93** correlation (built vs green r = −0.929),
because ESA WorldCover assigns each 10 m pixel exactly one class. Keep both?

**Recommendation (Claude):** drop `built_fraction`, keep `lack_green`.
1. They are redundant **by construction**, not by coincidence — in a dense town, "not
   green" and "built" are nearly the same pixel set.
2. "Little greenery or shade" is more actionable and legible to a field coordinator than
   "densely built".
3. The decisive reason: **built-up surface is a cause of the high land surface
   temperature that the Hazard dimension already measures directly.** Keeping it in
   Vulnerability counts the same physical fact twice — once as cause, once as effect —
   and inflates the weight of a single underlying phenomenon.

**Samraj's decision:** "drop built_fraction".

**Result:** the model has **five** indicators — `lst_day_mean` (Hazard), `population`
(Exposure), and `lack_green`, `dist_health`, `dist_centre` (Vulnerability). AHP asks
**3** pairwise comparisons, down from 15 as originally designed, so a consistency ratio
below 0.10 is very achievable.

**Still computed, just not indexed:** `built_fraction` remains in
`data/processed/landcover_cells.csv` and will appear in the cell panel as context, in
exactly the way the LST 90th percentile is computed and shown but not indexed (D4).

**Status:** approved
**Date:** 2026-09-26

---

## D20 — Drop the load-shedding indicator for v1 (2026-09-26)

**Question:** P1-10's feasibility study is written. Build the indicator or drop it?

**What the study found.** K-Electric's published schedule was fetched, cached, manifested
and parsed directly rather than described second-hand: **620 feeder rows** across **58
grid stations**, **26 on the LANDHI grid**, with daily outage from **4.0 to 10.0 hours**
(median 7.5). The quantity exists and varies by six hours between feeders — plausibly
more consequential than some indicators that *are* in the model.

**Why it cannot be built anyway.**
1. The schedule publishes a feeder name and a grid station. No coordinates, no boundaries,
   no street lists.
2. K-Electric's own route from place to feeder is a 13-digit account number in their app —
   a lookup from *account* to feeder, not from *place* to feeder, and unusable for 265 cells.
3. Many feeder names are businesses or bare codes: `ZAFAR ICE`, `ROTI PLANT`, `NOOR BHAI`,
   `36 B RMU`. Geocoding them would be guesswork, and OSM covers ~11% of Landhi (D18).
4. Even with every feeder located as a point, spreading 26 feeders across 265 cells means
   **inventing a service boundary K-Electric has not published** — forbidden by §2.1.
5. The document found is the **Ramadan 2026** schedule, not April–June.
6. `ke.com.pk` presents a **self-signed certificate**; TLS verification fails and plain
   HTTP times out. Disabling certificate verification to scrape a utility's site is not
   something this project will do, so there is no reproducible automated source.

**Samraj's decision:** "agreed, drop load-shedding for v1."

**Required in the model report:** state plainly that **the mechanism Faisal Edhi named in
June 2024 — long power cuts in poorer workers' neighbourhoods — is the one this model
cannot see.** That absence is a limitation of the data, not evidence that power cuts do
not matter.

**The v2 route, recorded in the study:** feeder names are printed on K-Electric bills.
Ten to fifteen bills from different parts of Landhi would tie feeder names to real
addresses, which is exactly the link the published schedule omits. Fieldwork, not scraping.

**Status:** approved
**Date:** 2026-09-26

---

## D21 — Shares and relative priorities only; never absolute supply totals (2026-09-26)

**Why this exists.** D16 established that the population layer undercounts Landhi by
roughly a factor of 2.3 against the 2023 census (295,132 modelled against 681,293
counted). Relative ranking survives a uniform factor because normalisation is relative.
**Absolute quantities do not.** D8 defines need from age-vulnerable population, so every
litre and every sachet computed from this data inherits the undercount: a centre planning
water for 300,000 people in a town of 681,000 under-supplies by more than half.

**Samraj's decision:** "Use shares and relative priorities only — never absolute litre or
supply totals — and state the undercount wherever a total appears on the site or in the
report."

**What this binds, concretely:**
- **Phase 4 (P4-02, P4-03).** The allocation planner reports **shares of available
  supply** and the **order** in which cells should be served. It does not publish
  "this cell needs N litres" as a standalone figure. The LP still computes quantities
  internally — it must, to allocate — but what is *presented* is the split of whatever
  stock the user enters, not an independent estimate of need.
- **The site.** The cell panel and the planner page show priority class, rank and share.
  Any figure that is an absolute count of people or units carries the undercount note.
- **The model report.** States the undercount, its measured size, and the reason absolute
  quantities are withheld.

**Why this is the right constraint rather than a cautious one.** A share is a ratio of two
quantities carrying the same bias, so the bias largely cancels. An absolute total carries
it in full. Publishing shares is not a softer claim — it is the claim the data can
actually support.

**Status:** approved
**Date:** 2026-09-26

---

## D22 — Use Saaty's graduated CR threshold, not a flat 0.10 (2026-09-26, PROVISIONAL)

**What the checker found.** PROMPT.md §7 specifies re-asking when CR ≥ 0.10. Saaty's own
published guidance is **graduated**: CR < 0.05 for n = 3, < 0.08 for n = 4, and 0.10 only
from n = 5. Vulnerability has exactly three indicators (D19), so **n = 3 is the case that
applies**, and a flat 0.10 is twice as permissive as the standard it cites.

**Decision:** use the graduated threshold. This is a **tightening**, never a loosening
(§2.2), and it costs nothing in practice — a realistic session came out at CR = 0.0332,
which passes either way.

**Why it matters more than it looks.** At n = 3 the whole inconsistency is one number:
κ = a₀₁·a₁₂/a₀₂, where 1 is perfect agreement. CR < 0.10 permits κ anywhere in
0.362–2.765 — the three judgements may fail to multiply through by a factor of **2.76**.
CR < 0.05 tightens that to 0.486–2.056. Calling a 2.76× transitivity violation
"acceptably consistent" is a claim that would be hard to defend.

**Also implemented from the same review:** the tool now reports κ directly, because at
n = 3 it *is* the inconsistency story and it is far more interpretable than CI.

**Status: PROVISIONAL** — it deviates from PROMPT.md §7's literal text, so it is Samraj's
to confirm. Raised as QUESTIONS.md Q10. Nothing is blocked: his answers would have to be
unusually contradictory for the two thresholds to differ in practice.
**Date:** 2026-09-26

---

## D23 — A count of zero is a structural zero, not a low percentile (2026-09-27)

**The bug.** D6b guarantees that a cell with no residents scores Priority exactly 0,
because Exposure is deliberately left unfloored. Measured, that guarantee held under
**robust min–max only**. Under percentile rank the 21 empty cells share the minimum rank,
whose average maps to **0.0379**, not 0 — so they received non-zero Priority. Since the
sensitivity analysis swaps normalisation method, **500 of its 1,000 draws were violating a
design invariant**, and the empty cells were being given 21 distinct ranks in half the runs.

**The fix.** `config/indicators.yaml` now declares `structural_zero: true` on
`population`, and normalisation forces a raw value of exactly zero to normalise to exactly
zero whatever the method. A count of zero people is a real absence, not a low percentile.

**Why in config rather than in code:** it is a statement about what the indicator *means*,
so it belongs where it can be audited, and it generalises to any future count indicator.

**Found by:** the P2-04 checker subagent, which noticed the 21 cells were being ranked
inconsistently between methods and pointed out that their published rank intervals were
therefore a methodological artefact.

**Status:** approved — this restores an invariant Samraj already approved in D6b rather
than creating a new rule.
**Date:** 2026-09-27

---

## D24 — Basemap: Esri World Light Gray Canvas, not CARTO (2026-09-27)

**What happened.** §9 requires "a light raster basemap that needs no API key". CARTO's
`light_all` was the obvious choice and was implemented first. It returned **HTTP 200 with
`naturalWidth > 0`** — so every check passed — while actually serving **"API KEY REQUIRED"
watermark tiles**. The map looked broken only when a screenshot was inspected by eye.

**Measured at z=13 over Landhi:**

| Provider | Size | Distinct colours |
|---|---|---|
| CARTO `light_all` | 2.0 kB | **16** (a watermark on flat grey) |
| Esri World Light Gray Canvas | 12.3 kB | 161 |
| OSM standard | 35.7 kB | 256 |

**Decision: Esri World Light Gray Canvas.** Free, no API key, and genuinely *light*, so the
priority ramp reads on top of it rather than competing. OSM standard tiles are darker and
busier, and their usage policy is stricter about non-trivial traffic. Attribution is
"Tiles © Esri — Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user
community", shown on the map.

**The test that should have caught it, and now does.** "Tiles load" was never the right
assertion — a watermark is a perfectly valid image. The end-to-end test now draws a tile
to a canvas and counts distinct colours, requiring more than 40. A watermark has 16.

**Status:** approved — a source substitution forced by an upstream change, logged per §6.
**Date:** 2026-09-27

---

## D25 — The site's Confidence layer uses the directional three-way call (2026-09-27)

**The problem.** §7 defines confidence classes as high ≥ 0.8, medium 0.5–0.8, low < 0.5,
applied to P(top 20%). Read literally that labels **215 of 265 cells "low confidence"**,
and **155 of those have P below 0.01** — cells the model is *certain* are not in the top
20%. On a page a coordinator acts from, printing "low confidence" next to a cell the model
is sure about is not imprecise, it is **false**.

**Decision.** The site's Confidence layer and panel use:

| Label | Rule | Cells |
|---|---|---|
| confidently in | P(top 20%) ≥ 0.8 | 28 |
| uncertain | 0.2 < P < 0.8 | 48 |
| confidently out | P(top 20%) ≤ 0.2 | 189 |

The middle band is the point: **those 48 cells are the list worth a human's attention**,
and the literal scheme buries them among 214 others.

**Nothing is hidden.** `data/processed/confidence.csv` keeps all three columns —
`stability` (used by the site), `confidence` (§7's thresholds applied to certainty) and
`confidence_literal` (§7 read straight) — so the choice is visible and reversible by
changing one mapping.

**Status:** approved in practice, pending Samraj's confirmation (QUESTIONS.md Q13).
**Date:** 2026-09-27

---

## D26 — The allocation tiebreak is scaled by the service distance

**Context.** PROMPT.md §8 sets the LP objective as

> maximise Σ p_i·x_ij − ε·Σ d_ij·x_ij … a small ε breaks ties in favour of closer cells

with `epsilon_distance_tiebreak: 0.001` in `config/allocation.yaml`.

**The problem.** Read literally, with `d_ij` in metres, that term is not small. At the
service limit of 5,000 m it contributes 0.001 × 5000 = **5.0 per unit**, while `p_i` is
a normalised score that never exceeds **1.0**. The "tiebreak" would be five times larger
than the quantity it is supposed to break ties in. The solver would in effect be
minimising travel distance, treating priority as a rounding error — while every comment,
document and variable name in the project said the opposite. It would have produced
plausible-looking allocations that were optimising the wrong thing.

**Decision.** The distance term is divided by the service distance D:

$$\varepsilon \sum_{ij} \frac{d_{ij}}{D} x_{ij}$$

`d/D` lies in [0, 1] within the service area, so the whole term is bounded by ε and can
only ever decide between plans that are otherwise equal — which is what a tiebreak means.
ε keeps its configured value of 0.001; only the units change.

**Alternative considered.** Set ε to 2×10⁻⁷ instead, so that ε·d at 5,000 m comes to
0.001. Rejected: it hides a units problem inside a magic number, and it silently breaks
again the moment D changes. Dividing by D is scale-free and states the intent.

**Consequence worth knowing.** A cell whose priority is below ε is not worth serving at
all, so the solver leaves it empty even with unlimited stock. With the real data no such
cell has any need — priority is exactly zero where population is zero (D6b) — but if that
stops being true, this is where it will show up. Documented in `docs/allocation.md` §2.

**Status:** adopted in P4-01, verified by an independent checker.
**Date:** 2026-09-27

---

## D27 — The equity floor is a fixed quantity, not a share of the allocation

**Context.** D8 sets `min_share_top_quintile: 0.25` — the top 20% of cells by priority
should receive at least a quarter of the supply — and PROMPT.md §8 says to add it "as a
soft constraint with a penalty".

**The problem, found by the independent checker.** Written the obvious way, as
$\sum_{i \in T} x \ge \alpha \sum x - u$, the floor is a share of *what the solver
chooses to allocate*. The solver can therefore satisfy it by allocating **less**. A unit
sent to an ordinary cell raises $\alpha \sum x$ by $\alpha$, so the shortfall and its
penalty grow by $\lambda\alpha$, and the unit nets $p_i - \lambda\alpha = p_i - 0.25$.

**Every cell with Priority below 0.25 became worth not serving.** In the checker's
repro — one high-priority cell needing 5 units, four ordinary cells needing 100 each,
one centre with 300 units, everything 1,000 m apart — the solver shipped **20 units and
left 280 in the warehouse**, and reported `equity_shortfall = 0.0` with no notes, because
by its own definition there was no shortfall. It happened in 15% of random test problems.
Priority is a geometric mean on [0, 1], so sub-0.25 cells are entirely ordinary.

A relief plan that withholds most of the supply in order to look equitable is the worst
failure this project could ship, and it would have looked completely normal on the map.

**Decision.** The floor is an absolute quantity, fixed before the solve:

$$F = \alpha \cdot \min\left(\textstyle\sum_j s_j,\ \sum_i n_i\right), \qquad \sum_{i \in T} x \ge F - u$$

$F$ is anchored to the most that could ever be delivered, which the solver cannot
influence. Sending a unit to an ordinary cell leaves $F$ untouched, so it stays worth
sending; sending one to a top-quintile cell reduces $u$ and earns $\lambda$ on top of
$p_i$ until the floor is met. A test now asserts that turning equity on never reduces
the total delivered, on the checker's repro and on 40 random problems.

**Alternatives considered.**
- *Share of total need* rather than min(stock, need). Rejected as the default: when
  stock is far below need the floor becomes unreachable and $u$ is always positive,
  which makes every plan report a shortfall and trains the reader to ignore it.
- *Keep the share form and add a withholding guard* — solve twice and warn if the
  equity version delivers less. Rejected: it detects the symptom, leaves the incentive
  in place, and doubles the solve time.
- *Hard constraint.* Rejected for the reason §8 gives: it can be infeasible, and an
  infeasible solver returns nothing at all.

**Status:** adopted in P4-01. **Samraj should confirm the interpretation** — QUESTIONS.md
Q15. The old behaviour is not an option, but which denominator to anchor to is his call.
**Date:** 2026-09-27

---

## D28 — The allocation is solved in whole units, not rounded to them

**Context.** The LP works in real numbers; a van carries whole units. PROMPT.md §8 says
to "round to whole units with a largest-remainder method that never exceeds stock".

**What went wrong.** The rounding method is correct on its own terms — it never exceeds
stock or need — but it can only add units to pairs the fractional plan already used. It
must: it cannot see distances, so a pair left at exactly zero may be one the 5 km service
limit forbids, and putting a unit there would break a constraint the function has no way
to check.

The price of that caution is **stranded supply**. The second independent checker measured
it on the real 265-cell Landhi grid: 44, 81 and 99 units left undelivered across three
scenarios, and in all three the rounded LP delivered *fewer units than the greedy
baseline*. On random problems it lost to greedy on objective in 5.1% of cases. The
module's headline claim — "the LP can never do worse than greedy" — was false at default
settings, and the 346-test suite did not catch it because the guarantee was only ever
tested on the continuous relaxation.

**Decision.** Solve the integer problem exactly. `scipy.optimize.linprog` accepts an
`integrality` mask, which puts HiGHS into MILP mode; every shipment is marked integer and
the equity slack stays continuous. The full 265-cell instance solves in under 0.1 s, so
there is no trade-off to weigh. The checker's repro now returns the true optimum of 202
instead of 201, and across 1,500 random problems the LP loses to greedy 0 times on
objective and 0 times on units delivered — against 76 and 62 before.

`exact_integers=False` keeps the rounding path, because it documents honestly what a
browser-side port without a solver can and cannot do (P4-03's "quick estimate").

**The general lesson, recorded because it will recur:** *round the problem, not the
answer.* Rounding an optimum gives a feasible point near the optimum, which is not the
same thing as the best feasible point.

**Status:** adopted in P4-01, confirmed by an independent checker.
**Date:** 2026-09-27

**D28 addendum (third review).** Declaring the variables integer was not sufficient.
An integer variable bounded above by 42.56 is bounded by 42, but HiGHS has to be *told*
that: given a fractional bound it can return a suboptimal incumbent **while reporting a
MIP gap of 0.0**, which is indistinguishable from a proven optimum. A two-cell,
one-centre problem returned 50 units where 51 was feasible and optimal — losing both to
greedy and to the rounding path the exact solve was written to replace. The variable
bounds, and the two constraint rows whose variables are all integers, are now floored
before the solve; that is an exact reformulation, not an approximation. The equity row
is untouched because it carries the continuous slack. Verified against exhaustive
integer enumeration on 120 small problems (0 suboptimal) and against an independent MILP
on 3,000 targeted and 1,600 general problems (0 suboptimal, 0 losses to greedy).

The wider lesson, which is the reason this is written down rather than just fixed: **a
solver reporting success is not evidence that the answer is optimal.** `status=0` and
`mip_gap=0.0` were both present and both misleading. The only check that caught it was
comparing against an independently written solver and, on small cases, against brute
force.

**D27 addendum (fourth review) — the equity rule barely does anything, and that is
structural.** An independent check measured how often turning the floor on actually
changes the allocation. Verified separately here: **6 of 24,000** (problem, share) pairs
on synthetic data — 0.025% — and **0 of 12** scenarios on the real 265-cell Landhi grid.
For greedy the answer is exactly zero, provably and in every case.

The reason is not a bug, it is the definition. The top quintile *is* the set of
highest-priority cells, and the objective already maximises priority-weighted delivery,
so the solver prefers those cells before any equity rule is added. The only thing the
floor can overturn is a choice the ε tiebreak made, and ε is at most 0.001. For greedy
it is stronger still: greedy works in priority order with the whole stock untouched, so
the top-quintile cells are served first anyway — if the floor can be met, that order
meets it, and if it cannot, no order can. The "equity first" pass written for greedy was
removed after it was shown to change nothing in 200,000 comparisons.

**What this means in practice: the floor shapes the *report*, not the *plan*.** Its real
value is the shortfall it surfaces — "the top-priority cells are N units short of what
they are owed, because X" — which is a genuine finding about where the stock is sitting.
That is worth keeping. But `min_share_top_quintile: 0.25` reads like a rule that
redistributes supply, and it is not one, so this is recorded rather than left for someone
to discover from the code.

It would only start to bite if the protected set were defined *independently* of
priority — by age, say, or by a ward boundary, or by cells a field team names. That is a
different rule, and Samraj's to choose: QUESTIONS.md Q15.

## D29 — A contradictory centre row is refused, not guessed (2026-09-27)

**Context.** D13 says the allocation draws stock only from centres marked
`can_hold_stock: yes`, and P4-01 requires a test proving an `ambulance_standby` centre is
never given stock. Until this turn the only thing enforcing D13 was one line inside
`main()`, which no test touched, and it read the flag alone: a standby point typed in as
`yes` would have been handed stock, and a typo such as `y` would silently have become
`no`, removing that centre's supply with nothing on screen to say so.

**What is implemented.** `stock_holding_centres()` in `pipeline/allocate.py` is now the
only route from `centres.csv` to either solver.
- `yes` → can be given stock. `no` and `unknown` → cannot; "unknown" means nobody checked.
- An `ambulance_standby` row is never a stock holder, whatever its flag says.
- **An `ambulance_standby` row marked `yes` is refused with the row named**, as is any
  role or flag outside the vocabulary that `tests/test_centres.py` checks.

**Recommendation: refuse.** One of that row's two fields is wrong, and either guess
changes the plan: trusting the flag adds supply that is probably not there; trusting the
role removes supply that might be. `centres.csv` is short and filled in by hand after a
visit, so an error that stops the run and names the row costs a minute to fix. A silent
guess costs a wrong plan.

**Main alternative: trust the role and exclude silently.** The run never stops, and the
test that an ambulance point gets no stock still passes. Rejected because it hides a data
error in the one file the project says must be verified in person.

**Samraj to decide.** Nothing downstream depends on which you pick yet — `centres.csv`
has no rows (Q2). Changing it is one `raise` in `stock_holding_centres()` and one test.

**Samraj's decision (2026-09-27):** go with the recommendation — "if a centre is listed
as an ambulance standby point but also marked 'can hold stock: yes', stop the run and
flag that exact row as an error, rather than silently excluding it."

**What this binds.** `stock_holding_centres()` raises `ValueError` naming the centre;
the run stops and no plan is produced until the row is corrected. The same applies to
any role or flag outside the vocabulary. Tests in `tests/test_allocate.py` pin the
refusal, and P4-02's scenario builder reaches centres only through this function, so
it cannot be bypassed by a later feature.

**Status:** approved
**Date:** 2026-09-27

---

## D30 — The planner's quick estimate lets the user place their own stock points (2026-09-27, PROVISIONAL)

**Context.** P4-03 asks for a planner where a coordinator can "pick centres and stock".
No relief centre has been verified in person (Q2), so there is no list of real centres to
pick from, and the unverified candidates may not be used (§6).

**Implemented.** The quick estimate asks the *user* to place up to five stock points —
by tapping the map, or with a keyboard-accessible "add at the map centre" button — and
to enter how much each holds. The page labels them "your own what-ifs, not verified
relief centres". Nothing about them is stored or published; they exist only in that
browser tab. The exact precomputed scenarios still come only from `centres.csv`
through `stock_holding_centres()` (D13, D29), and that section says honestly that there
are none yet.

**Why this is not inventing data.** §2.1 forbids the project asserting a location or
figure it cannot support. A point the user places is their own input, like the stock
figure they type, and the page says so. Nothing the project publishes changes.

**The per-cell table shows units of the user's own stock** (as well as the share), because
D21 permits "the split of whatever stock the user enters". It never shows the model's
own estimate of need as a quantity; "need met" is a percentage, labelled as the model's
estimate, with the 2.3× undercount stated beside it.

**Main alternative:** disable the quick estimate until a centre is verified. Rejected as
the default because it leaves the planner with nothing to try for months, and a
coordinator who knows where their own stock sits gets no use from the page.

**Samraj to confirm** (QUESTIONS.md Q16). Reversing it removes the map-click handler
and the add-point button; the exact-scenario section is unaffected.
