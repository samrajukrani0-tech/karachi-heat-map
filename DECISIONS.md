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

**Status: PROVISIONAL.** Claude changed its own Phase 0 config default to satisfy a
PROMPT.md criterion, and the choice of 0.25 is a modelling judgement that belongs to
Samraj (§2.4). Raised as QUESTIONS.md Q5. Nothing downstream is blocked meanwhile.
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

**Status: PROVISIONAL** — the source choice is a judgement call belonging to Samraj, and
the undercount has consequences he should decide on. Raised as QUESTIONS.md Q6.
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
