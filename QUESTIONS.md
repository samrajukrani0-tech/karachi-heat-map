# Questions for Samraj

Open questions only Samraj can answer. Answer inline under each question; Claude
clears answered items into DECISIONS.md or the relevant doc.

---

## Q1 — Express Tribune June 2024 article — ANSWERED 2026-09-26

`https://tribune.com.pk/story/2473712/heatwave-wreaks-havoc-15-found-dead-on-streets`
returns HTTP 403 to Claude, so Claude has not read it directly. **Samraj opened it and
supplied the text on 2026-09-26.** The article text is NOT stored in this repo (it is
copyrighted); only the facts extracted from it are recorded below and in
`data/SOURCES.md`.

**Localities named in it, with bodies recovered on 24 June 2024:**
Orangi Town (three separate incidents, incl. Faqir Colony and Qatar Hospital),
MA Jinnah Road signal, Karimabad (Magnet Mall), Super Highway (Faqira Goth Chowk),
Old Golimar (Double PMT Street), Gulistan-e-Johar (Block 11, Munawar Chowrangi),
**Landhi (near Landhi Hospital's Chowrangi — 40-year-old Sultan)**, New Karachi
(Sector 11-D Market), Surgical Market, Civil Lines (Frere Hall), Mahmoodabad Model
Park, North Karachi (UP Mor), Shah Faisal Colony / Green Town.

**Organisations:** Chhipa volunteers moved 12 of the 15 bodies that day; Edhi moved 3.
**Edhi figures:** 526 bodies to three Karachi morgues in the week; typically 30–40 a
day, risen to 100–140. Faisal Edhi said some deaths may be heat-related but this was
unconfirmed. Police Surgeon Dr Summaiya Syed confirmed 4 heatstroke deaths on 24 June.
**Named Edhi facilities:** the three Edhi cold storages are at **Moosa Line, Sohrab
Goth and Korangi**.

**Caveat that now applies to P2-05 face validity:** of the ~13 localities named, exactly
**one** is inside the pilot area. The reporting clusters in Orangi, central and north
Karachi. A face-validity check for Landhi therefore rests on a single cited incident,
which is weak evidence — it must be described as such in the model report and must not
be presented as confirmation that the model is right. See Q4.

---

## Q2 — Verify a relief centre in person (OPEN, on the critical path)

`data/manual/centres.csv` is still empty and P1-09b stays blocked until at least one
centre is verified. OSM contains **no** Edhi, Saylani, Chhipa or Al-Khidmat facility
inside the Landhi Town boundary — re-checked on 2026-09-26 across every spelling
variant (Edhi/Edhee/Aidhi, Saylani/Silani/Sailani, Chhipa/Chipa/Chippa, Al-Khidmat,
and the Urdu forms). 133 such objects exist across the wider Karachi bounding box;
zero fall inside Landhi.

`data/manual/centre_candidates.csv` now holds **11 unverified candidates** within 7 km
of Landhi's centroid, for Samraj to ask about. Nothing from that file enters the model.

**Asked of Samraj:** through Nadeem Ghani or your uncle, confirm any centre and record
name, org, lat, lon, source, verified_by, verified_on in `centres.csv`. Highest-value
targets, in order: Saylani Korangi No. 4 (2.9 km); the Edhi and Chhipa ambulance points
at Majeed Colony / Labour Colony (4.5 km, on Landhi's eastern edge); the Edhi Korangi
cold storage named in the Tribune report.

**Answer:**

---

## Q3 — Should Chhipa Welfare Association be in scope? — ANSWERED 2026-09-26

PROMPT.md §1 names Edhi and Saylani. The Tribune report shows **Chhipa moved 12 of the
15 bodies on 24 June 2024, against Edhi's 3** — so in this specific event Chhipa was
the larger street-response operation, and OSM shows Chhipa ambulance points nearer to
Landhi than any Edhi or Saylani facility.

**Claude's recommendation:** widen the phrasing from "Edhi or Saylani" to "a relief
organisation operating in the pilot area", and treat Chhipa and Al-Khidmat as equally
valid hosts. It costs nothing in the model — `centres.csv` already carries an `org`
column — and it roughly triples the chance of getting one door opened. The alternative
is to stay narrow so the pitch stays focused on two well-known names.

**Samraj's answer:** "Any relief org, plus a role column." Recorded as **D13**.
`centres.csv` now carries `role` and `can_hold_stock`; the index counts every verified
facility, the allocation planner only those holding stock. Guarded by tests/test_centres.py.

---

## Q4 — How should weak face validity for Landhi be handled? — ANSWERED 2026-09-26

Following Q1: only one of ~13 localities named in the June 2024 street-death reporting
falls inside Landhi. Options for P2-05, to decide before Phase 2 builds it:
(a) report the single Landhi mention honestly and label the check as weak — recommended;
(b) run the face-validity check at city scale instead, comparing modelled priority
across several towns, which needs the model extended beyond the pilot area;
(c) rely on the expert-ranking protocol (§7c) instead, which needs field staff.

**Samraj's answer:** "Honest weak check; expert ranking is the real test." Recorded as
**D14**, with the three reasons the city-scale alternative was rejected (near-circular,
sample too small, sample biased by the response itself) written out so the argument is
not re-made later. P2-05 geocodes the single Landhi incident and reports its cell's rank.

---

## Q5 — Confirm the grid inclusion rule — ANSWERED 2026-09-26

P1-02 found that two Phase 0 statements contradicted each other: the "centre inside OR
≥50% of area" rule tops out at 96.55% coverage, but the P1-02 acceptance criterion
requires ≥99%. The 50% clause turned out to be dead code — no cell ever qualified under
it, because a hexagon has ≥50% inside exactly when its centre is inside.

Claude changed the threshold to **0.25** (265 cells, 99.115% coverage) and made every
indicator use the clipped geometry, so the 1.935 km² of hexagon outside Landhi is
excluded from all measurements. Recorded as **D15, provisional**. Full table in
DECISIONS.md.

**Asked of Samraj:** confirm 0.25, or choose 0.10 (276 cells, 99.83%) or any-intersection
(290 cells, 100%). Lower thresholds cover more of Landhi but admit edge cells holding
very little real evidence — at 3% inside, a cell contains about three population pixels.
0.885% of Landhi is currently uncovered and is recorded as a limitation.

**Samraj's answer:** "confirmed, keep the 0.25 inclusion threshold (265 cells, 99.115%
coverage)." D15 moves from provisional to approved.

---

## Q6 — Population undercount: how should the model handle it? — ANSWERED 2026-09-26

Both modelled population sources put Landhi at about **300,000 people**. The 2023 census
says **681,293**. The same shortfall appears across all of Korangi District (models 1.81–1.93M
against a census 3.13M), so it is the models, not our boundary. Recorded as **D16**.

The ranking inside Landhi is probably safe, because normalisation is relative and a
uniform factor cancels. The worry is that the undercount is **not** uniform: Landhi is
undercounted worse than the district average, which hints that the densest, most informal
areas are undercounted most — under-ranking exactly the places that need support first.

**Asked of Samraj, two decisions:**
1. **Keep Meta as the source?** It is 31 m against WorldPop's 93 m, giving 119 pixels per
   cell against 13, which matters at this cell size. Claude recommends Meta.
2. **How should absolute numbers be presented?** Options: (a) report shares and priorities
   only, never absolute people or litres, and state the undercount wherever a total
   appears — Claude's recommendation; (b) publish absolute numbers with a prominent
   "these are modelled and known to be roughly half the census figure" caveat; (c) apply
   a documented uniform correction factor to totals only — which Claude advises against,
   because it would dress a non-uniform bias as a fixed one and §2.1 forbids adjusting
   data to match a figure.

This is worth asking a centre manager too: they will know whether 300,000 or 681,000
matches what they see on the ground in Landhi.

**Samraj's answer:** "yes, keep Meta as the population source. Use shares and relative
priorities only — never absolute litre or supply totals — and state the undercount
wherever a total appears on the site or in the report." D16 moves to approved, and the
presentation rule is recorded separately as **D21** because it binds Phase 4 and the site.

---

## Q7 — Drop the two age-share indicators? — ANSWERED 2026-09-26

P1-07 built `share_over60` and `share_under5` as D4 specified. Measured, they turn out to
be **the same binary variable with opposite signs**: correlation exactly −1.0000, 86% of
cells on just two values, and their sum constant to within 0.0015. Meta applies an
administrative age profile rather than modelling age spatially, and Landhi spans two such
zones. Recorded as **D17**.

Because both have direction +1 and sit in the same weighted mean, they would largely
cancel while still consuming two of Vulnerability's six weights.

**Claude's recommendation:** drop both from the index for v1. Vulnerability keeps four
indicators; AHP drops from 15 pairwise questions to 6, which also makes consistency
easier to reach.

**Alternatives:** (a) keep one, accepting it splits Landhi into two administrative zones
rather than measuring anything real; (b) look for Union-Council-level age data from the
2023 census and match it to cells — a real piece of work, and probably a v2 task;
(c) keep both and let §7's "a constant indicator becomes 0, with a warning" handle them,
which is honest but leaves two dead weights in the AHP.

**Unaffected either way:** the age **counts** (`people_over60`, `people_under5`) do vary
across cells and are what D8's need definition uses. Phase 4 does not depend on this.

**Worth telling a centre manager:** the tool cannot see where older residents are
concentrated. They may know.

**Samraj's answer:** "drop both age shares". Applied across config, weights, tests and
CLAUDE.md; D17 is now approved. Vulnerability has four indicators, and AHP will ask 6
pairwise questions instead of 15.

---

## Q8 — `built_fraction` and `lack_green` are 0.93 correlated — ANSWERED 2026-09-26

P1-08 measured both from ESA WorldCover, where each 10 m pixel gets exactly one class.
In a dense town that makes them near-complements: **r = −0.929** between built and green,
so `built_fraction` and `lack_green` (= 1 − green) correlate at about **+0.93**.

With Vulnerability down to four indicators after D17, two of them being near-duplicates
means V is effectively three things, and "how built up is it" silently carries half the
weight.

**Claude's recommendation: drop `built_fraction`, keep `lack_green`.** Three reasons:
1. They are redundant by construction, not by coincidence.
2. "Little greenery or shade" is the more actionable and legible phrase for a field
   coordinator than "densely built".
3. **Built-up surface is a cause of high land surface temperature, which the Hazard
   dimension already measures directly.** Keeping it in Vulnerability partly double-counts
   Hazard — the model would count the same physical fact twice, once as a cause and once
   as an effect.

**Alternatives:** (a) keep both and let the AHP weights absorb it — but AHP asks about
*importance*, and people do not naturally discount for redundancy when answering;
(b) keep `built_fraction` and drop `lack_green` — defensible, but loses the more
interpretable of the two and keeps the one that double-counts Hazard; (c) combine them
into a single "hard surface, little shade" indicator.

If both are dropped in favour of one, Vulnerability has three indicators and AHP asks
just 3 pairwise questions.

**Samraj's answer:** "drop built_fraction". Applied; recorded as **D19**. Vulnerability
has three indicators (`lack_green`, `dist_health`, `dist_centre`) and AHP will ask 3
pairwise questions. `built_fraction` is still computed and stored as panel context.

---

## Q9 — Load-shedding indicator: approve dropping it? — ANSWERED 2026-09-26

`docs/load-shedding-feasibility.md` is written. Summary of what was found:

**The data exists and varies.** K-Electric's published schedule has 620 feeder rows
across 58 grid stations, 26 of them on the LANDHI grid, with daily outage ranging from
**4.0 to 10.0 hours** (median 7.5). That spread is large enough to matter.

**But it cannot be mapped honestly.** The schedule publishes a feeder name and a grid
station — no coordinates, no boundaries, no street lists. K-Electric's own route from
place to feeder is a 13-digit account number in their app, which cannot be run for 265
cells. Many feeder names are businesses or bare codes (`ZAFAR ICE`, `ROTI PLANT`,
`36 B RMU`). And even with every feeder located as a point, spreading 26 feeders over 265
cells would mean inventing a service boundary K-Electric has not published — which §2.1
forbids. The schedule found is also the Ramadan 2026 one, not the April–June hot season,
and `ke.com.pk` presents a self-signed certificate so it cannot be fetched automatically.

**Claude's recommendation: approve dropping the indicator for v1**, and state in the model
report that the mechanism Edhi actually named is the one this model cannot see.

**The v2 route is fieldwork, not scraping:** collect feeder names from 10–15 K-Electric
bills across different parts of Landhi. A bill ties a feeder name to a real address, which
is exactly the link the published schedule omits. Ask a centre manager too — people know
precisely where power goes longest, because it structures their day.

**Asked of Samraj:** approve dropping P1-10's indicator for v1 (Claude's recommendation),
or ask for one of the alternatives in the study to be attempted anyway.

**Samraj's answer:** "agreed, drop load-shedding for v1." Recorded as **D20**. P1-10 is
marked `dropped` in features.json with the study as its evidence, so it counts as
resolved. The feasibility study stays in `docs/` as the record of why, and as the method
for the v2 fieldwork route.

---

## Q10 — Confirm the stricter AHP consistency threshold (OPEN, not blocking)

PROMPT.md §7 says re-ask when CR ≥ 0.10. Saaty's own published guidance is graduated:
**0.05 for three items**, 0.08 for four, 0.10 only from five. Vulnerability has exactly
three indicators, so the stricter figure is the one that applies to you.

Claude implemented the graduated threshold (**D22, provisional**). It is a tightening, not
a loosening, and it costs nothing: a trial session scored CR = 0.0332, which passes either
way.

**Why it is worth the stricter bar.** With three items the entire inconsistency is one
number, κ = a₀₁·a₁₂/a₀₂, where 1 means your answers multiply through perfectly. A CR of
0.10 allows κ to be off by a factor of **2.76**; 0.05 allows **2.06**. If an examiner asks
"what does your consistency check actually rule out?", 2.06 is a much easier answer.

**Asked of Samraj:** confirm the graduated threshold, or revert to PROMPT.md's flat 0.10.

**Answer:**

---

## Q11 — "Intensity" is not a per-person view (OPEN, decide before P2-06)

PROMPT.md §7 says: *"Also compute **Intensity** = √(H × V), the per-person view."* The
checker subagent objected to that wording, and measurement backs it up.

The formula contains **no population term**. It is Priority with the Exposure dimension
deleted — *exposure-blind*, which is not the same as per-person. A genuinely per-person
figure would be a rate: risk divided by people. The evidence: before it was masked,
**21 cells with nobody living in them scored up to 0.740 on Intensity, one ranking 24th
of 265** — on a measure labelled "per-person".

**Already fixed:** Intensity is now undefined (blank) where a cell has no residents.
"How bad is it for a person here" has no answer when there is no person here.

**Still open — the name and the description.** Claude recommends keeping the formula, which
is specified and genuinely useful, but describing it accurately: something like
**"Severity — how bad conditions are in this area, regardless of how many people live
there"**. It does real work: on populated cells it correlates with Priority at Spearman
0.93 but moves some cells by more than 50 ranks, which is exactly the equity function
§7 wants — surfacing small-population hotspots that Priority buries.

**Asked of Samraj:** keep the name "Intensity" with a corrected description, rename it to
"Severity", or defend "per-person" as intended. This changes wording in the model report
and on the site, not the maths.

**Answer:**

---

## Q12 — D19's reasoning does not survive measurement (OPEN, not blocking)

When you approved dropping `built_fraction` (D19), Claude gave two reasons:
1. it correlates ~0.93 with `lack_green`, so the two are near-duplicates; **and**
2. built-up surface is *a cause of* the high land surface temperature that Hazard already
   measures, so indexing it would count the same physical fact twice.

**Reason 2 does not hold.** Measured on the real data, `lst_mean_c` versus
`built_fraction` is Spearman **+0.004** — no relationship at all. There was no
double-counting to prevent. Reason 1 is solid and independently justifies the decision,
so **D19 stands**, but it was argued partly on a claim the data does not support, and you
should know that.

**What this implies for `lack_green`.** The checker argued `lack_green` belongs in Hazard
rather than Vulnerability, since absence of vegetation drives surface heat. But by the
same measurement it correlates with `lst_mean_c` at Spearman **+0.048** — so in Landhi it
is *not* a proxy for the measured hazard, and keeping it in Vulnerability adds information
rather than duplicating heat. Claude therefore recommends **no change**.

**The finding worth carrying into the report either way.** Vegetation buys Landhi very
little: cells ≥90% green average **42.48 °C**, cells <10% green average **43.31 °C** — a
difference of just **0.83 °C**. The relationship even flips sign between the green minority
(Spearman −0.275) and the built majority (+0.382), which is why the overall correlation is
near zero. The hazard layer's 7 °C spread is real and spatially coherent, but it is **not**
explained by land cover, and the report should not imply the usual urban-heat-island story.

**Asked of Samraj:** confirm no change to `lack_green`'s dimension (Claude's
recommendation), or move it to Hazard.

**Answer:**

---

## Q13 — "Confidence" as §7 defines it labels most of the map wrongly (OPEN, decide before P3-05)

PROMPT.md §7 says: *"Report, per cell: median rank, 90% rank interval, and probability of
being in the top 20%. Confidence classes: high (≥ 0.8), medium (0.5–0.8), low (< 0.5)."*

Read literally — thresholds applied to P(top 20%) — **215 of 265 cells come out "low
confidence", and 155 of those have P below 0.01.** Those are cells the model is almost
maximally confident about: it is certain they are *not* in the top 20%. Labelling them
"low confidence" on a map tells a coordinator the opposite of the truth. The checker
subagent reached this conclusion independently.

**What Claude implemented instead**, keeping both so the difference is visible:
- `stability`: **confidently in** (P ≥ 0.8) — 28 cells · **uncertain** (0.2–0.8) — 48 ·
  **confidently out** (P ≤ 0.2) — 189. The 48 "uncertain" cells are an actionable list.
- `confidence`: the same §7 thresholds applied to *certainty* = max(P, 1−P), giving high
  216 / medium 49 / low 0.
- `confidence_literal`: §7 read straight, kept so nothing is hidden.

**Asked of Samraj:** which does the site's Confidence layer use? Claude recommends the
three-way **confidently in / uncertain / confidently out**, because it is directional and
the middle band is the list worth a human's attention.

**Answer:**
