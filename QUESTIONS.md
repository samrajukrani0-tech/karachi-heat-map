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

## Q3 — Should Chhipa Welfare Association be in scope? (OPEN)

PROMPT.md §1 names Edhi and Saylani. The Tribune report shows **Chhipa moved 12 of the
15 bodies on 24 June 2024, against Edhi's 3** — so in this specific event Chhipa was
the larger street-response operation, and OSM shows Chhipa ambulance points nearer to
Landhi than any Edhi or Saylani facility.

**Claude's recommendation:** widen the phrasing from "Edhi or Saylani" to "a relief
organisation operating in the pilot area", and treat Chhipa and Al-Khidmat as equally
valid hosts. It costs nothing in the model — `centres.csv` already carries an `org`
column — and it roughly triples the chance of getting one door opened. The alternative
is to stay narrow so the pitch stays focused on two well-known names.

**This is a judgement call (D-series), so it is Samraj's to make.**

**Answer:**

---

## Q4 — How should weak face validity for Landhi be handled? (OPEN, Phase 2)

Following Q1: only one of ~13 localities named in the June 2024 street-death reporting
falls inside Landhi. Options for P2-05, to decide before Phase 2 builds it:
(a) report the single Landhi mention honestly and label the check as weak — recommended;
(b) run the face-validity check at city scale instead, comparing modelled priority
across several towns, which needs the model extended beyond the pilot area;
(c) rely on the expert-ranking protocol (§7c) instead, which needs field staff.

**Answer:**
