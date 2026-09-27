# Model report — Karachi Heat Priority Map

**Pilot area:** Landhi Town, Karachi · **Grid:** H3 resolution 9, 265 cells · **Version:** v1 draft
**Generated:** 2026-09-27 from the committed outputs — every number below is read from `data/processed/`, not retyped.

> **Status: provisional.** The weights are placeholders, not Samraj's judgement (P2-02b), and one of the five indicators has no data (P1-09b). Both are stated wherever they matter.

---

## 1. What this model says, in plain words

Landhi is divided into 265 hexagons of about 0.105 km². For each one the model asks three questions and multiplies the answers together:

- **Hazard** — how hot does the ground get on a typical hot-season afternoon?
- **Exposure** — how many people live there?
- **Vulnerability** — what makes heat more dangerous here: little greenery, distance from a clinic, distance from a relief centre?

The result, **Priority**, ranges from 0.000 to 0.853. It is a **ranking within Landhi**, not a measurement of risk on any absolute scale, and not a prediction of deaths.

**What it is not:** an official warning system (follow the Pakistan Meteorological Department and PDMA Sindh), a mortality model, or a verdict on any neighbourhood.

## 2. The headline result, including the uncomfortable part

- **53 cells** fall in the top 20% under the headline model.
- Of those, **only 28 stay there in at least 80% of 1000 draws** when the weights, the dimension exponents and the normalisation method are varied.
- **12 of the 53 are on the wrong side of a coin flip.**

In other words: **roughly half the priority list is robust and roughly half is not.** The very top and the bottom of the ranking are stable; the middle churns. For a triage tool that is the right shape — you act on the top — but it must not be read as a settled ordering of 265 places.

The three-way stability call: **28 confidently in**, **48 uncertain**, **189 confidently out**. The uncertain list is the one worth a human's attention.

## 3. Limitations — read this before the results

### 3.1 The population layer undercounts by roughly a factor of 2.3

The 2023 census records **681,293** people in Landhi Town. The modelled sources give about **300,000**. Summing the same rasters over all of Korangi District gives 1.81M and 1.93M against a census 3,128,971, so the shortfall is **systematic across the district** and is not an artefact of our boundary. Both sources predate the 2023 census and both infer population from building footprint area, which understates dense multi-storey housing.

Relative ranking survives a *uniform* factor, because normalisation is relative. The danger is that the undercount is **not** uniform: Landhi is undercounted worse (0.44) than the district average (0.58), which suggests the densest, most informal areas are undercounted most — under-ranking exactly the places this tool exists to find. **The data was not rescaled to match the census** (§2.1), and a test enforces that.

### 3.2 The mechanism Edhi actually named is the one this model cannot see

In June 2024 Faisal Edhi said the deaths came mostly from poorer workers' neighbourhoods **hit by long power cuts**. K-Electric's published schedule shows the quantity exists and varies — 26 feeders serve the Landhi grid, with daily outage from **4.0 to 10.0 hours** — but it publishes feeder names and grid stations, never geography. Placing 26 feeders across 265 cells would require inventing a service boundary K-Electric has not published, so the indicator was dropped (D20). This absence is a limitation of the data, **not** evidence that power cuts do not matter.

### 3.3 Land surface temperature is not air temperature — and it does not behave as expected

Landsat measures the temperature of the **ground**, not the air, and carries no humidity information, which matters enormously in Karachi. Surface readings of 43–48 °C are normal when air temperature is nearer 35–40 °C.

More surprising, and worth stating before anyone else finds it: **surface temperature is rank-uncorrelated with every other layer in this model** — Spearman +0.048 with lack of greenery, +0.004 with built-up surface, −0.005 with population. Cells that are at least 90% green average **42.48 °C** against **43.31 °C** for cells under 10% green: a difference of just **0.83 °C**. The relationship even flips sign between the green minority (−0.275) and the built majority (+0.382). The 7 °C spread across Landhi is real and spatially coherent, but **it is not explained by land cover**, so this report does not claim the textbook urban-heat-island story.

### 3.4 Two indicators were dropped after measurement, not before

- **Age shares.** Meta's 60+ and under-5 layers correlate at exactly **−1.0000** over Landhi, with 86% of cells on just two values and their sum constant to within 0.0015. They encode an administrative zone, not spatial demography (D17). The **counts** do vary and are retained for the supply calculation.
- **Built-up surface.** Correlates ≈ +0.93 with lack of greenery (D19).

Age is among the strongest individual risk factors in heat mortality, and **this model cannot map it within Landhi.** That is a real gap, not a simplification.

### 3.5 OpenStreetMap barely describes Landhi

OSM building polygons cover **6.01%** of Landhi's area against 54.7% built-up measured from satellite — about **11%** as much built area as exists, from 711 mapped buildings in a town of several hundred thousand people. Every missing clinic can only make the true distance **shorter**, so the distance-to-care indicator **overstates** isolation. Note this runs opposite to the population undercount, which understates exposure: the two biases act on different dimensions and do not cancel.

### 3.6 Coverage, ties and one missing indicator

- The grid covers **99.115%** of Landhi; the missing 0.885% is thin slivers along the boundary.
- **81 of 265 cells (31%)** are tied at a clipped extreme on at least one indicator, so the very hottest cell is not identifiable — the top of the heat scale is a 14-way tie.
- **`dist_centre` has no data at all.** Vulnerability is currently a two-indicator mean with weights renormalised to {'lack_green': 0.5, 'dist_health': 0.5}. No relief centre has been verified in person, and OSM offers no fallback.
- Results describe **areas, not individuals**.

## 4. Validation, and what each check is worth

**(a) Equal-weights baseline — not available yet.** The configured weights *are* equal weights pending P2-02b, so this comparison correlates a vector with itself and is 1.0 by construction. What it was meant to answer — does the weighting choice matter? — is answered by the sensitivity analysis in §2. Alternative weightings give Spearman 0.957 (hazard-led), 0.9651 (exposure-led), 0.966 (vulnerability-led).

**(b) The June 2024 incident — illustrative context only, carrying no evidentiary weight.** One body was reported inside Landhi, 'near Landhi Hospital's Chowrangi'. That phrase resolves to four plausible locations, ranking **[106, 112, 156, 160] of 245** — all mid-distribution, which is exactly what a randomly drawn cell would give.

This is **neither support nor refutation**, and the reasons matter:
- It is a single incident. There is no denominator: we observe one place where an event happened and no sample of places where it did not, so nothing distinguishes the model from chance in either direction.
- The location is a phrase, not a coordinate. 'Landhi Hospital's Chowrangi' resolves to several plausible points, and they rank differently.
- Street-death reports depend on where ambulances patrol and where bodies are found in public, so they sample reporting infrastructure, not heat harm. A body located by reference to a landmark is selected for landmark density.
- The observed ranks sit mid-distribution -- which is exactly what a randomly drawn cell would give. This is neither support nor refutation.

**(c) Expert ranking — the real test, not yet run.** A one-page form lists 12 named localities taken from OpenStreetMap, with blank rows because that list is certainly incomplete. The analysis script reports Spearman's ρ, Kendall's τ, a bootstrap interval, a Bonett–Wright Fisher interval and a permutation p-value, and has been tested on **SYNTHETIC rankings only**. With 12 localities the one-sided 5% permutation threshold sits near **ρ = 0.50**, so only very strong agreement is detectable; about **25** localities are needed to tell a genuinely useful model from guesswork.

## 5. Maths appendix

### 5.1 Normalisation (D5)

Each indicator is clipped at its 5th and 95th percentile and scaled linearly to 0–1, with 1 always meaning more risk:

$$ x' = \frac{\min(\max(x,\;q_{5}),\;q_{95}) - q_{5}}{q_{95} - q_{5}} $$

Clipping keeps a single extreme cell from compressing everything else, while the linear scaling preserves *spacing* — a cell twice as far from a clinic reads as twice as far. Percentile rank is implemented as the alternative and is used in the sensitivity analysis. A constant indicator becomes 0 with a warning.

**A declared exception (D23):** a raw count of exactly zero people normalises to exactly zero under *either* method. A count of zero is a real absence, not a low percentile — without this, percentile rank mapped the 21 empty cells to 0.0379 and the guarantee in §5.3 held under one method and failed under the other.

### 5.2 Within a dimension

$$ D = \sum_i w_i x'_i, \qquad \sum_i w_i = 1 $$

Hazard and Exposure have one indicator each. Vulnerability's weights come from pairwise comparison (§5.5).

### 5.3 Across dimensions (D6)

$$ \text{Priority} = H^{w_H} \cdot E^{w_E} \cdot V^{w_V}, \qquad w_H = w_E = w_V = \tfrac{1}{3} $$

A **geometric** mean, not an arithmetic one. The difference is substitutability: an arithmetic mean lets a high value in one dimension compensate for a near-zero value in another, so a scorching but empty industrial yard (H ≈ 1, V ≈ 0.8, E ≈ 0) would score 0.6 and rank near the top. The geometric mean gives it (1 × 0 × 0.8)^⅓ = 0. For risk, where all three must be present for harm to occur, that is the honest model. By AM–GM the geometric mean never exceeds the arithmetic one, so it is also the more cautious.

**The floor, and why it is asymmetric (D6b).** Clipping produces exact zeros for the bottom 5% of each indicator, and anything multiplied by zero is zero. Hazard and Vulnerability are therefore floored at 0.01: a zero there is an artefact, since Landhi's coolest cells are still around 40 °C in June. **Exposure is deliberately not floored**, because E = 0 means nobody lives there, which is a fact rather than an artefact. Consequently 21 cells score Priority exactly 0 by construction.

*Measured consequence:* the Vulnerability floor **never fires** — the minimum Vulnerability across all cells is 0.1344, far above 0.01. It is retained because the indicator set may change, but at present it is inert.

### 5.4 Intensity

$$ \text{Intensity} = \sqrt{H \cdot V} $$

PROMPT.md calls this 'the per-person view'. Strictly it is **exposure-blind**: no population term appears in it. It is Priority with the Exposure dimension removed, and it does useful work — on populated cells it correlates with Priority at about ρ 0.93 while moving some cells more than 50 ranks, surfacing small-population hotspots that Priority buries. It is **undefined where nobody lives**: 'how bad is it for a person here' has no answer when there is no person here.

### 5.5 Weights by pairwise comparison (AHP)

Vulnerability's weights come from the principal eigenvector of a pairwise comparison matrix $A$, where $a_{ij}$ is how much more important indicator $i$ is than $j$ on Saaty's 1–9 scale. If judgements were perfect, $a_{ij} = w_i/w_j$ and $Aw = nw$. Real judgements give $Aw = \lambda_{\max} w$ with $\lambda_{\max} > n$, and the excess measures self-contradiction:

$$ CI = \frac{\lambda_{\max} - n}{n - 1}, \qquad CR = \frac{CI}{RI_n} $$

**At n = 3 the whole inconsistency is one number.** A 3×3 reciprocal matrix has trace 3 and zero principal 2×2 minors, so its characteristic polynomial collapses to $\lambda^3 - 3\lambda^2 - \det A = 0$ with $\det A = (\sqrt{\kappa} - 1/\sqrt{\kappa})^2$ and $\kappa = a_{12}a_{23}/a_{13}$. Everything — $\lambda_{\max}$, CI, CR — is a function of κ alone, where κ = 1 is perfect agreement. In log space the three residuals are exactly $+d/3, +d/3, -d/3$: the contradiction is **shared equally**, so no single answer can be blamed, and the tool re-asks all three rather than pretending otherwise.

**Threshold (D22).** Saaty published a graduated limit — CR < 0.05 for three items, 0.08 for four, 0.10 from five — rather than a flat 0.10. With three indicators the stricter figure applies. CR < 0.10 would permit κ to be wrong by a factor of 2.76; CR < 0.05 tightens that to 2.06.

### 5.6 Sensitivity

1000 seeded draws (seed 20260926), jittering the Vulnerability weights and the dimension exponents with a Dirichlet of concentration 50, and swapping the normalisation method. The two method arms are run and reported **separately**: pooled, they produce bimodal rank distributions whose median lands in the trough — a value no draw favours.

- Median 90% **rank** interval: **53 places**; median 90% **priority** interval: **0.190** on a 0–0.85 scale. *(Corrected 2026-09-27 from 0.193: the sensitivity draws were not applying the D23 structural zero to empty cells under percentile rank. Fixing it moved 36 cells' rank intervals by at most 19 places and changed no stability class.)*
- Mean |P(top 20%) under one normalisation − the other| = **0.144**. The normalisation choice is not a detail.

Rank intervals look alarming next to priority intervals because **rank is competitive** — a cell moves when *other* cells move — and the priority curve is nearly flat through the middle of the ranking. Both are published.

α = 50 implies a marginal standard deviation of about 0.066 on each exponent, so this measures robustness to *small* perturbation, not to a genuinely different weighting. And the weights are still placeholders, so the uncertainty from 'these are not yet Samraj's judgement' exceeds anything sampled here.

## 6. Figures

- `artifacts/lst_cells_map.png` — Hot-season daytime surface temperature per cell
- `artifacts/population_cells_map.png` — Modelled people per cell (log scale)
- `artifacts/landcover_cells_map.png` — Built-up surface and green cover
- `artifacts/access_cells_map.png` — Distance to the nearest health facility
- `artifacts/indicators_qa.png` — Indicator distributions
- `artifacts/sensitivity.png` — How far each cell's rank moves under jittered assumptions

*(Figures live in `artifacts/`, which is gitignored and rebuilt by the pipeline. P5-04 embeds the ones the README needs.)*

## 7. Independent checks

Every mathematical feature was re-derived by a **fresh checker subagent** given the written specification and the data, but neither the implementation nor the expected answers (§3.1). Verdicts:

| Feature | Verdict | What the checker changed |
|---|---|---|
| P2-01 Normalisation | **Agrees** — 18/18 spot values to 6 dp | relative constant tolerance; flat-core warning; the constant/direction ambiguity pinned; log1p shown rank-invariant |
| P2-02 AHP | **Agrees** — 3 matrices by 4 independent routes | graduated CR threshold; κ reported; CI clamped; Collatz–Wielandt bracket; input validation |
| P2-03 Scores | **Agrees** on arithmetic, disputed the formulation | Intensity masked where nobody lives; 'per-person' wording challenged; D19's second reason shown false |
| P2-04 Sensitivity | **Agrees** on every headline number | **found a real bug** — D6b's zero-Priority guarantee held under one normalisation only; method arms separated; P reported to 2 dp with its standard error |
| P2-05 Validation | **Agrees** — ranks 106/156/160 exact | ranks quoted against 245 positions; face validity downgraded; permutation test added; Bonett–Wright SE |

The most valuable single finding was P2-04's: **half the sensitivity draws were violating a design invariant** because a count of zero people was being treated as a low percentile rather than a real absence.

## 8. Open questions

Recorded in `QUESTIONS.md`. The ones that bear on this report:

- **Q2** — no relief centre verified in person, so `dist_centre` is empty. On the critical path.
- **Q11** — 'Intensity' is described as a per-person view but contains no population term.
- **Q12** — D19's second justification does not survive measurement.
- **Q13** — §7's confidence classes, read literally, label 215 of 265 cells 'low confidence' precisely because the model is *certain* they are not in the top 20%.

## 9. Provenance

Every dataset, licence, access date and caveat is in `data/SOURCES.md`; raw downloads are checksummed in `data/raw/manifest.json`; every judgement call is in `DECISIONS.md` (24 entries). Code is MIT, this document CC BY 4.0, and `data/processed/` is ODbL 1.0 because it derives from OpenStreetMap.

Built with Claude Code as a coding assistant. Research question, modelling decisions, weights and fieldwork by Samraj Lal Ukrani.
