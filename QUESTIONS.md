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

## Q5 — Confirm the grid inclusion rule (OPEN, not blocking)

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

**Answer:**

---

## Q6 — Population undercount: how should the model handle it? (OPEN, not blocking)

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

**Answer:**
