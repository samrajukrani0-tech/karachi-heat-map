# Karachi Heat Priority Map: master prompt for Claude Code

This file drives a loop-based build in Claude Code. Section 0 is for Samraj. Everything after it is for Claude.

---

## 0. For Samraj: how to run it

1. Open the Claude desktop app, go to the **Code** tab, and start a new session. Environment: **Local**. Model: **Opus 5**. Permission mode: **Auto**. Folder: an empty folder that contains only this file (for example `karachi-heat-map`).
2. Send this as your first message. Phase 0 is a conversation, not a loop:
   > Read PROMPT.md in full and run Phase 0 with me — check my setup first, then ask me the decisions one at a time. Don't start Phase 1.
3. At the end of Phase 0, Claude prints one instruction per phase, filled in with your decisions (§13). Paste the Phase 1 instruction and send it as an ordinary message; Claude works through the phase across turns on its own until the finish line is met.
   - Ask for the STATUS block at any point to see progress: which feature is in flight, turns used against the phase's cap, and anything blocked on you.
   - To stop early, tell it to stop after the current feature.
   - You can type a message at any time. Claude reads it once its current action finishes.
   - If you hit your usage limit, the session pauses; once it resumes, resend the same phase instruction so Claude picks up where it left off. Keep the laptop plugged in and awake.
4. Between phases: ask Claude for a code review of that phase's changes (`/code-review`), read the new entries in `LEARNING_LOG.md`, answer anything in `QUESTIONS.md`, then paste the next goal.
5. If checks fail and keep failing, use the fix-it goal at the end of §13.

---

## 1. Mission and context

You are the engineering partner of **Samraj**. He is a first-year A Level student at Nixor College, Karachi, taking Maths, Further Maths, Physics, and Computer Science, and he plans to study applied mathematics. Together you are building a free, public, mobile-first website. It helps a Karachi relief team decide where heat-relief support should go first during a heatwave, and why: drinking water, ORS, heat kits, cooling points, and ambulance standby. It is designed for whichever relief organisation agrees to pilot it — Edhi Foundation, Saylani Welfare, Chhipa, Al-Khidmat, Aman, or another verified provider (D13).

Why it matters:
- June 2015: about 1,200 people died in southern Pakistan during a heatwave. Source: AFP, reported by Newsweek Pakistan, https://www.newsweekpakistan.com/?p=867013
- June 2024: Edhi Foundation said it received 568 bodies in Karachi in the five days to 25 June, against a usual ~40 a day. Faisal Edhi said most came from poorer workers' neighbourhoods hit by long power cuts. The Sindh health department disputed that the deaths were heat-related. Sources:
  - Bloomberg: https://bnnbloomberg.ca/karachi-sees-a-surge-in-deaths-as-heat-wave-sears-pakistan-1.2090293
  - Dawn, 25 June 2024: https://www.dawn.com/news/1841754 — names Landhi and records Edhi's Korangi mortuary receiving 10 bodies against a normal 5–6
  - Express Tribune: https://tribune.com.pk/story/2473712/heatwave-wreaks-havoc-15-found-dead-on-streets — blocks automated fetching (HTTP 403); read directly and its text supplied on 2026-09-26. Extracted facts are recorded in `QUESTIONS.md` Q1 and `data/SOURCES.md`; the article text itself is not stored in the repo. It names Landhi (near Landhi Hospital's Chowrangi), records Chhipa moving 12 of the 15 bodies that day against Edhi's 3, and places Edhi's three Karachi cold storages at Moosa Line, Sohrab Goth, and Korangi.
- Causes of death are disputed, so this tool never estimates deaths or assigns causes. Instead it maps three things so field teams can plan ahead:
  - conditions: heat
  - people: exposure
  - circumstances that make heat more dangerous: vulnerability

What it is: decision support for field teams.

What it isn't:
- an official warning system (point people to the Pakistan Meteorological Department and PDMA Sindh)
- a mortality model
- a verdict on any neighbourhood

Samraj will explain this project to NGO staff, mentors, and interviewers. You have two jobs of equal weight:
1. Build excellent, working software.
2. Make sure he understands and owns every modelling decision.

He makes the judgement calls (§5); your job is to make them easy to make well. Explain things plainly, at A Level standard, and connect them to what he's studying where that genuinely fits.

---

## 2. Non-negotiables

1. **Truth over appearance.**
   - Never invent data, coordinates, sources, citations, scores, screenshots, or validation results.
   - If something isn't available, say so in `QUESTIONS.md`, then use a documented fallback or mark the feature blocked.
   - Test fixtures that aren't real data are labelled `SYNTHETIC` in the file name and contents, and never reach the live site.
2. **Tests are sacred.** Never delete, skip, or loosen a test, threshold, or acceptance criterion to get checks passing. If one is genuinely wrong, propose the change in `DECISIONS.md` and wait for Samraj.
3. **Evidence or it didn't happen.** A feature passes only if you ran its checks in the same turn and they passed. Store that evidence in `features.json`.
4. **Samraj owns the judgement calls (§5).**
   - For each one, give a recommendation, your reasons, and the main alternative. He decides.
   - For reversible decisions you may continue on a provisional default, clearly marked as provisional, but never finalise it yourself.
5. **Aggregated, respectful data.**
   - Use no individual-level or personal data.
   - Don't scrape social media, or any site whose terms forbid scraping (e.g. Google Maps).
   - Use official or common place names.
   - Say "higher priority for support". Never call an area "dangerous", "bad", or "unsafe".
6. **No outside actions.** Don't email, message, post, submit forms, or contact any organisation. Write drafts only; Samraj sends them.
7. **Credentials and safety.**
   - Never ask for, type, or store passwords or tokens. If a tool needs a login (e.g. `gh auth login`), ask Samraj to run it himself in the terminal pane.
   - Keep secrets out of the repo.
   - Don't force-push, rewrite history, or change anything outside the project folder.
   - Ask before installing anything system-wide.
8. **Be a good open-data citizen.**
   - Follow every licence and attribution requirement.
   - Respect rate limits; be gentle with Overpass.
   - Follow basemap tile usage policies.
   - Cache downloads.
   - Read cloud-optimised rasters in windows rather than downloading whole scenes.
9. **Windows and macOS.** Write scripts in Python (no bash-only tooling), use `pathlib` everywhere, and don't hard-code absolute paths. Python itself comes from `uv python install 3.12` into a project-local `.venv`, never the system interpreter; 3.12 is chosen for geospatial wheel support (rasterio, h3, pyproj) on Intel macOS. Pin `h3` to `>=4.3,<4.4` in `pyproject.toml`: 4.4 and later ship no x86_64 macOS wheel, which breaks this machine. Run every repo command through `uv run` (e.g. `uv run python scripts/check.py`), and add dependencies with `uv add` so `pyproject.toml` and `uv.lock` stay the source of truth for the environment.

---

## 3. Loop protocol: every turn

1. **Orient.**
   - Read the last three entries of `PROGRESS.md`.
   - Run `uv run python scripts/features.py`.
   - Skim `DECISIONS.md` and `QUESTIONS.md` for new answers.
   - Check `git status` and `git log --oneline -10`.
2. **Health check.** Run `uv run python scripts/check.py --quick`. If anything that used to pass now fails, fixing it becomes this turn's feature.
3. **Pick** the lowest-numbered unresolved feature in the current phase that isn't blocked and whose dependencies pass. If it's too big for one turn, split it (`P1-04a`, `P1-04b`). Splitting and adding features is fine; deleting features or loosening acceptance criteria is not.
4. **Plan** in three to six lines in the transcript.
5. **Build** the smallest complete version. Write or extend tests first where practical.
6. **Verify.**
   - Run the feature's own checks, then `check.py --quick`.
   - For anything visible, look at it: take screenshots at 375×812 and 1280×800 (Browser pane or Playwright) and confirm the console is clean.
   - For maths features, use the checker subagent (§3.1).
7. **Record.**
   - In `features.json`, set `passes: true` with an evidence string (commands and results), and only if you verified it this turn.
   - Append to `PROGRESS.md`: date, feature, what changed, evidence, next step.
   - Add a `LEARNING_LOG.md` entry (§3.2).
   - Update `DECISIONS.md` and `QUESTIONS.md` as needed.
8. **Commit** with a clear message, e.g. `feat(P1-04): hot-season daytime LST per cell`. Push when the remote exists and checks pass.
9. **Report.** End the turn with the STATUS block (§3.3). Nothing comes after it.

Working rules:
- One feature per turn.
- If the same problem defeats you twice, stop and write a short diagnosis in `PROGRESS.md`. Add it to `QUESTIONS.md` as well if Samraj can unblock it. Then move to another feature.
- Keep the transcript short; long logs go in `artifacts/logs/`.
- Collect questions for Samraj in `QUESTIONS.md` rather than interrupting him over small things.

### 3.1 Maker–checker for the maths
This applies to P2-01 to P2-05 and to P4-01.
1. After building the feature, spawn a fresh subagent as an independent checker.
2. Give it the spec and the data, but not your conclusions.
3. Ask it to re-derive three spot values independently and to look for errors in the formulation.
4. Record its verdict in `PROGRESS.md`.
5. Resolve any disagreement before marking the feature passing.

### 3.2 LEARNING_LOG.md entries
Add an entry after each feature. Each entry has:
- **What and why:** three to six plain sentences on what was built and why.
- **The key idea in A Level terms:** link it to Maths, Further Maths, or Physics topics where the link is genuine. Examples: eigenvectors for AHP weights, thermal radiation for how satellites measure surface temperature, correlation for validation.
- **Questions:** two or three that Samraj should be able to answer, with the answers inside a `<details>` block.

### 3.3 STATUS block
```
STATUS
Feature: P1-04 Daytime heat per cell: PASS
Evidence: pytest 38 passed; check.py --quick CHECK: PASS; LST 31.2 to 52.8 °C (inside documented range)
Progress: Phase 1 6 of 11 resolved; overall 11 of 42
Blocked on Samraj: 1 (Q2: approve pilot boundary)
Next: P1-05 Night heat
Explain it: hotter ground on summer afternoons is the "heat" part of the score.
Turns this phase: 7 (limit 30)
```

---

## 4. Repository layout

```
karachi-heat-map/
  CLAUDE.md             condensed rules, commands, file map (written in Phase 0)
  PROMPT.md             this file
  pyproject.toml        project metadata and dependencies (managed with uv)
  uv.lock               locked dependency versions
  features.json         backlog and source of truth for progress
  PROGRESS.md           append-only turn log
  DECISIONS.md          judgement calls: proposed, approved, provisional, deferred
  QUESTIONS.md          things only Samraj can answer
  LEARNING_LOG.md       plain-language explanations and practice questions
  DESIGN.md             site design plan (Phase 3)
  LICENSE               MIT, for code (D10)
  LICENSE-docs          CC BY 4.0, for docs and site text (D10)
  LICENSE-data          ODbL 1.0, for data/processed (D10)
  .claude/launch.json   preview server for the desktop Browser pane
  config/               area, indicators, weights, allocation settings (YAML)
  pipeline/             Python package: fetch, grid, indicators, model, ahp,
                        sensitivity, validate, allocate, export
  scripts/              check.py, features.py, build_site_data.py, field_briefs.py
  data/raw/             gitignored download cache + manifest.json
  data/manual/          small hand-made files with a source column (centres.csv, etc.)
  data/processed/       small outputs, under 5 MB in total
  data/SOURCES.md       every dataset: URL, licence, access date, resolution, caveats
  site/                 static website, no build step, deployed to GitHub Pages
  tests/                pytest for the pipeline; tests/e2e for Playwright
  docs/                 model-report.md, allocation.md, data-dictionary.md, pitch/
  artifacts/            gitignored screenshots, logs, Lighthouse reports
  .github/workflows/    CI checks and Pages deploy
```

---

## 5. Decisions Samraj makes

Record each decision in `DECISIONS.md` with:
- the question
- the options
- your recommendation and why
- Samraj's decision, in his words
- status: approved, provisional, or deferred
- date

- **D1 Hazard.** Recommend heat first, with monsoon flooding as a later version. Reasons:
  - Heat risk can be mapped credibly from open satellite and population data.
  - Credible flood modelling needs drainage and hydrology data that isn't openly available for Karachi.
  - Edhi was on the front line in 2024.
  - The May–June heat season gives a natural pilot window.
- **D2 Pilot area.** Resolved: **Landhi Town** (OSM relation 16350631), 25.37 km² measured in EPSG:32642, about 242 cells at H3 resolution 9. Chosen after comparing candidates on area, modelled population, known relief centres, and whether credible June 2024 reporting mentions them — Landhi is directly named in the Dawn report cited in §1, and it's a realistic distance for Samraj to visit in person. Korangi Town has Edhi's own named mortuary but exceeds the 10–60 km² band and includes industrial and creek land with near-zero population; it stayed the alternative rather than the pick.
- **D3 Grid.** Recommend H3 resolution 9, about 0.105 km² per cell. Landsat's thermal sensor has a native resolution of about 100 m (delivered at 30 m), so much smaller cells would claim precision the heat data doesn't have. Alternative: resolution 8, about 0.74 km² per cell. Resolved: resolution 9, about 242 cells across Landhi Town.
- **D4 Indicators.** Approve or edit the list in §6, including the optional ones. Resolved: night-time LST and the Relative Wealth Index are dropped for v1 — at Landhi's 25 km², MODIS's 1 km night-LST pixels give only ~25 samples and Meta's 2.4 km RWI tiles give only ~5, both close to constant across the area and not worth building on. Both move to the "v2 candidates" note in §6. The hot-season daytime LST 90th percentile (P90) is computed and shown in the cell panel, but it is **not** an index indicator: it correlates strongly with the mean, so including both would double-count hazard (see the indicator table in §6).
- **D5 Normalisation.** Recommend robust min–max: clip at the 5th and 95th percentiles, then scale to 0–1. Alternative: percentile rank.
- **D6 Combining dimensions.** Priority = H^wH × E^wE × V^wV, with wH + wE + wV = 1. Resolved: the three dimension exponents stay fixed at 1/3 each; AHP (D7) sets weights within Vulnerability's six indicators only, not across H/E/V. Reason: in a multiplicative model an exponent is an elasticity, not an importance weight, and Saaty's 1–9 pairwise scale doesn't map onto an elasticity the way it maps onto a weighted mean. The sensitivity analysis (§7) varies these exponents directly. With any weighting, high values in two dimensions still can't hide a near-zero third.
  - **D5/D6 interaction.** Robust min–max produces exact zeros for the bottom 5% of any indicator, which under multiplication would force Priority to 0 for that cell. Hazard and Vulnerability are floored at 0.01 after normalisation to prevent this; Exposure is deliberately **not** floored, because E = 0 genuinely means nobody lives there.
- **D7 Weights.** Samraj sets the six Vulnerability-indicator weights with the AHP tool (§7); the H/E/V dimension exponents are fixed by D6, not by AHP. Until D7 is resolved, use equal weights within Vulnerability and flag them as "provisional" in the data and on the site.
- **D8 Allocation.** Decide:
  - what is distributed (water, ORS, heat kits)
  - units per person in need
  - who counts as in need
  - maximum service distance
  - whether a minimum share goes to the highest-priority cells

  Resolved, provisional: need is defined as residents aged 60+ plus children under 5 — deliberately **not** taken from Priority, which is already the allocation LP's objective, to avoid counting the model's own judgement twice. The Sphere Handbook litres-per-person figure in `config/allocation.yaml` is marked `UNVERIFIED` until P4-02 checks it against the Handbook directly.
- **D9 Languages.** Resolved: **English only for v1.** The Urdu string set, the RTL/Nastaliq typography work, and the Urdu Playwright check are dropped from this version (§9, §10, §12); P3-07 and P3-07b are marked dropped. UI strings still live in `site/i18n/en.json`, externalised rather than inline, so Urdu can be added later without a rewrite.
- **D10 Licences.** Three licences, not two: MIT for code; CC BY 4.0 for docs and site text; **ODbL 1.0** for `data/processed/`, because OSM-derived indicator values make it a derivative database under ODbL's share-alike clause. `LICENSE-data` sits alongside `LICENSE` and `LICENSE-docs` in the repo root (§4). Each raw dataset keeps its own upstream licence, recorded in `data/SOURCES.md`.
- **D11 Public identity.** Decide the repo name, whether it's public (recommended), how his name appears, and which contact the site shows, if any. A project-only email is safer than a personal one. Resolved (D11c): the site shows no contact at all for v1, so P5-03's one-pager leaves a blank line for a handwritten contact, and the About page must not imply a channel that doesn't exist.
- **D12 AI-assistance disclosure.** Recommend a short, honest line in the README and on the About page, for example: "Built with Claude Code as a coding assistant. Research question, modelling decisions, weights, and fieldwork by Samraj." Research programmes and competitions increasingly ask for this, and being upfront protects him.
- **D13 Relief-organisation scope.** Resolved: any verified relief facility counts, whatever the organisation — Edhi, Saylani, Chhipa, Al-Khidmat, Aman, or another. `dist_centre` is meant to measure how far an area is from organised help; restricting it to two named charities would instead measure distance to those two charities specifically, which isn't a property of the neighbourhood. `data/manual/centres.csv` carries `role` (`ambulance_standby`, `distribution_point`, `clinic`, `morgue`, `office`, `other`) and `can_hold_stock` (`yes`/`no`/`unknown`): the index counts every verified facility, while the allocation planner (§8) draws stock only where `can_hold_stock` is `yes`, since an ambulance standby point holds none. This makes the double use already flagged in §6 explicit and testable.
- **D14 Face validity for Landhi.** Resolved: of roughly 13 localities named across the Dawn and Express Tribune June 2024 reports, exactly one falls inside Landhi, near Landhi Hospital's Chowrangi. P2-05 geocodes that single incident and reports its cell's priority rank — bottom quintile would be a genuine warning — and the model report labels the check weak evidence, not a validated correlation. A city-scale rank correlation is rejected and must not be built: Priority already contains population, so correlating it with raw death counts is near-circular; ~20 located incidents across 25 towns can't carry a rank statistic; and street-death reports are biased by where ambulances patrol and where bodies are found in public rather than where heat harm actually occurs. A defensible city-scale version would need a geolocated incident list compiled from the full 20–26 June 2024 reporting — that's a v2 task, not v1. The expert-ranking protocol (§7c) is the real validation.

---

## 6. Data plan

Rules for every data source:
- Verify it at fetch time; collection IDs, band names, licences, and URLs change.
- Document each dataset in `data/SOURCES.md`.
- If a source is gone, choose an equivalent and log it in `DECISIONS.md` as provisional.
- If a source requires an account or login, stop and ask Samraj. Don't work around it.

Store and export data in EPSG:4326. Measure distances and areas in UTM zone 42N (EPSG:32642).

| Indicator | Dimension | Primary source | Fallback and notes |
|---|---|---|---|
| Hot-season daytime land surface temperature, °C (per-cell mean enters the index; the 90th percentile is computed and shown in the panel only — see D4) | Hazard | Landsat 8/9 Collection 2 Level-2 via the Microsoft Planetary Computer STAC API (`landsat-c2-l2`, surface-temperature asset such as `lwir11`). Use April–June across several recent years, mask cloud and shadow with `qa_pixel`, and take a median composite. Check the USGS scale and offset (documented as 0.00341802 × DN + 149.0 = kelvin). | AWS Earth Search (Element 84) STAC. Use Google Earth Engine only if Samraj has set it up. |
| People per cell | Exposure | Meta (Data for Good) high-resolution population density for Pakistan on HDX (about 30 m), and WorldPop constrained 100 m | Compute both, compare, and choose per D4. Sanity-check the pilot total against an independent figure (e.g. Pakistan Bureau of Statistics 2023 census for a matching unit), using a documented tolerance. Never adjust data to hit that figure. |
| Share aged 60+; share under 5 | Vulnerability | Meta demographic layers on HDX | Handle zero-population cells explicitly. |
| Building footprint fraction | Vulnerability | Google Open Buildings or Microsoft Global ML Building Footprints (check Karachi coverage) | OSM buildings, with a completeness caveat. |
| Lack of green cover | Vulnerability | ESA WorldCover 10 m via Planetary Computer, and/or hot-season Sentinel-2 L2A NDVI | |
| Distance to nearest health facility | Vulnerability | OpenStreetMap hospitals, clinics, and doctors via Overpass or osmnx | Use road-network distance if a routable graph works. Otherwise use straight-line distance × a documented circuity factor (e.g. 1.3). Measure and report gaps in OSM coverage. |
| Distance to nearest verified relief facility | Vulnerability and allocation | `data/manual/centres.csv` (name, org, role, can_hold_stock, lat, lon, source, verified_by, verified_on), confirmed by Samraj | Any verified organisation counts (D13) — not restricted to Edhi/Saylani. OSM can suggest candidates, but exclude them until he verifies them. This indicator is used in both the index and the allocation; the allocation planner draws stock only from rows where `can_hold_stock` is `yes`. Note the double use in the model report. |
| Load-shedding exposure (optional, Karachi-specific) | Vulnerability | K-Electric's published load-shed schedules by area or feeder | Do a feasibility study first (P1-10). It's worth a real attempt because it comes from Edhi's own 2024 field observation. It never blocks other work, and it is built only if Samraj approves. |

**v2 candidates (dropped for v1 by D4):**
- **Night-time heat.** MODIS LST night band is 1 km resolution — over Landhi's 25 km² that's only ~25 pixels, too coarse to differentiate cells. ECOSTRESS (~70 m) is the v2 route if a future pilot area is large enough, or temperature-diverse enough, for night heat to earn its place in the index.
- **Relative wealth.** Meta's Relative Wealth Index tiles are about 2.4 km — only ~5 tiles across Landhi, effectively constant at this scale.

Housekeeping:
- Raw downloads live in `data/raw/` (gitignored), with `manifest.json` recording URL, sha256, bytes, date, and licence.
- `uv run python -m pipeline.run --all` rebuilds everything from the cache.
- Record exactly which scenes and years were used and the population data's reference year. Note any mismatch in the model report.

---

## 7. Model

- **Framework.** IPCC-style risk with three dimensions: Hazard (H), Exposure (E), and Vulnerability (V).
- **Indicator config.** `config/indicators.yaml` holds, for each indicator:
  - id
  - English name (v1 is English-only per D9; leave room to add a `name_ur` field later without a schema change)
  - dimension
  - unit
  - direction (+1 means higher = more risk)
  - source
  - transform (e.g. `log1p` for people)
  - a short plain-language phrase in English for the "top reasons" list
- **Normalise** each indicator to 0–1 per D5, where 1 means more risk. A constant indicator becomes 0, with a warning. After normalising, floor Hazard's and Vulnerability's per-indicator values at 0.01 (D5/D6 interaction, §5) so an exact zero from clipping can't force Priority to zero by itself; leave Exposure unfloored, since E = 0 means the cell is genuinely unpopulated.
- **Within a dimension**, Vulnerability's six indicators take a weighted mean using the weights in `config/weights.yaml`, set by AHP (D7). Hazard and Exposure currently have one core indicator each, so no within-dimension weighting applies to them yet.
- **Across dimensions**, combine as Priority = H^wH × E^wE × V^wV (D6), with wH + wE + wV = 1 and, for v1, each fixed at 1/3. Also compute **Intensity** = √(H × V), the per-person view, for the equity discussion in the report.
- **Top reasons.** For each cell, list the three indicators that push its score furthest above the pilot-area median, as short phrases in English.
- **AHP tool** (`uv run python -m pipeline.ahp`). Samraj runs it himself in the terminal pane. It sets the weights **within Vulnerability's six indicators only** — the H/E/V dimension exponents are fixed by D6 and are not part of this tool's scope.
  1. It asks pairwise questions in plain English on Saaty's 1–9 scale, e.g. "For heat harm in this area, how much more important is X than Y?"
  2. It computes the weights as the principal eigenvector, using power iteration.
  3. It reports λmax, CI = (λmax − n) / (n − 1), and CR = CI / RI, using Saaty's random-index table.
  4. If CR ≥ 0.10, it shows which answers conflict and asks those again.
  5. It saves the answers, weights, CR, `decided_by: Samraj`, and the date.
  - Tests: a published textbook example is reproduced within tolerance; a perfectly consistent matrix gives CR ≈ 0; an inconsistent matrix is caught.
- **Sensitivity analysis** (fixed seed, N ≥ 1000).
  - Perturb the Vulnerability weights with a Dirichlet distribution centred on the chosen weights; document the concentration parameter.
  - Also perturb the three dimension exponents (wH, wE, wV) around their fixed 1/3 values, and swap between the normalisation choices.
  - Report, per cell: median rank, 90% rank interval, and probability of being in the top 20%.
  - Confidence classes: high (≥ 0.8), medium (0.5–0.8), low (< 0.5), unless Samraj decides otherwise.
- **Validation**, honest and clearly labelled:
  - (a) Agreement with an equal-weights baseline (Spearman ρ).
  - (b) Face validity for the one incident located inside Landhi (near Landhi Hospital's Chowrangi, from the Dawn/Tribune June 2024 reporting) — report that cell's priority rank; bottom quintile would be a genuine warning. Report this as weak evidence, not a validated correlation. Do not build a city-scale rank correlation between Priority and reported deaths (D14): Priority already contains population, so correlating it with raw death counts is near-circular; the located-incident count is too small to carry a rank statistic; and street-death reports are biased by where ambulances patrol and where bodies are found in public. No invented locations.
  - (c) An expert-ranking protocol: a one-page English-language form (per D9) on which field staff rank 10–15 named localities, plus an analysis script (Spearman ρ, Kendall τ, bootstrap confidence intervals). Test the script only on SYNTHETIC data until Samraj brings real rankings.
- **Limitations the report must state:**
  - Land surface temperature isn't air temperature or heat index, and humidity matters a lot in Karachi.
  - Modelled population has error.
  - Results describe areas, not individuals.
  - OSM is incomplete.
  - Night-time heat data is coarse.
  - This is not a mortality model.

---

## 8. Allocation planner

The question it answers: "We have this much supply at these centres. Which cells should get how much?"

The model:
- need_i = (people in need in cell i, as defined in D8) × units per person.
- Variables: x_ij ≥ 0, the units sent from centre j to cell i. Define them only where the distance d_ij ≤ D.
- Objective: maximise Σ p_i·x_ij − ε·Σ d_ij·x_ij. Here p_i is Priority, and a small ε breaks ties in favour of closer cells.
- Constraints:
  - Σ_i x_ij ≤ s_j (each centre's stock)
  - Σ_j x_ij ≤ need_i

Solving:
- Use `scipy.optimize.linprog(method="highs")`.
- If D8 asks for a minimum share for top-priority cells, add it as a soft constraint with a penalty.
- Round to whole units with a largest-remainder method that never exceeds stock.
- Baseline for comparison: greedy (highest priority first, served from the nearest centre that still has stock). Report both objective values.

Tests:
- Stock is never exceeded.
- Nothing is sent beyond D.
- The LP objective is at least the greedy objective.
- Unlimited stock meets all reachable need.
- Zero stock sends nothing.
- Results are deterministic.
- A tiny example matches a hand solution written out in `docs/allocation.md`, so Samraj can solve it on paper.

On the site, show precomputed exact scenarios. Also offer an interactive greedy "quick estimate", clearly labelled as approximate.

---

## 9. Website

**Audiences:**
1. Field coordinators on phones, often outdoors in bright sun.
2. NGO leadership, donors, and mentors on laptops, deciding whether to trust the tool.

**Primary job:** within ten seconds, a visitor can see which parts of the pilot area need heat support first, and why.

**Pages:** Map (home), Plan supplies, Field briefs, How it works, Data and credits, About.

**Tech:**
- Static HTML, CSS, and vanilla JavaScript, with no framework and no build step.
- Leaflet pinned to an exact version, either vendored in `site/vendor/` or loaded from a pinned CDN URL with SRI.
- `scripts/build_site_data.py` writes the site's data into `site/data/`.
- Serve locally with `uv run python -m http.server`, configured in `.claude/launch.json` (for the Browser pane) and in the Playwright config.
- Basemap: a light raster basemap that needs no API key, with correct attribution.
- Nothing on the site needs a secret.

**Map:**
- Colour cells by quintile, using a colour-blind-safe sequential palette.
- Legend in plain words, from "Highest priority" to "Lower priority". Never use "safe".
- Layers: Priority (default), Heat, People, Vulnerability, Confidence.
- Tapping or clicking a cell opens a panel (a bottom sheet on phones) showing:
  - the priority class and rank
  - the top three reasons, in plain words
  - raw values with units
  - confidence
  - "what this can't tell you"
- If the weights are provisional, the map says so.

**Strings:** English only for v1 (D9). Every UI string still lives in `site/i18n/en.json`, externalised rather than inline, so a future v2 can add `ur.json` and RTL/Nastaliq support without restructuring the site.

**Quality floor:**
- First load ≤ 1.5 MB, excluding basemap tiles.
- Usable on a mid-range Android phone on slow 3G.
- Tap targets ≥ 44 px.
- Text contrast ≥ 4.5:1; key map labels ≥ 7:1, because of sun glare.
- Everything reachable by keyboard, with visible focus.
- `prefers-reduced-motion` respected.
- No horizontal scrolling at 375 px.

**Design.** Write DESIGN.md before any styling.
- Base the look on Karachi's summer and on the plain, trustworthy practicality of relief work.
- The map is the one memorable element. Everything around it stays quiet and restrained.
- Write a compact plan containing:
  - four to six named hex colours
  - type roles: one Latin typeface for everything (English only for v1, per D9)
  - ASCII wireframes at 375 px and 1280 px
  - alignment rules
  - three principles specific to this project
- Review the plan against this brief. Revise anything that reads like a default you'd produce for any site.
- Avoid the following, unless the brief genuinely calls for it:
  - a warm cream background with a serif display and a terracotta accent
  - near-black with one acid-bright accent
  - broadsheet hairline columns
  - identical rounded cards with soft grey shadows and gradient washes
  - all-caps eyebrow labels
  - middle-dot metadata strings
  - arrows appended to button text
  - one highlighted word in a headline
  - numbered markers on content that isn't a sequence
- After each UI feature, take screenshots at both widths, critique them, fix what's wrong, and remove one unnecessary element.

**Copy:**
- Plain words, active voice, sentence case, written from the field coordinator's point of view.
- Buttons say exactly what happens when pressed.
- Error and empty states say what happened and what to do next.

---

## 10. Quality gates

`uv run python scripts/check.py [--quick] [--lighthouse]` runs, in order:
1. ruff (Python lint)
2. pytest (pipeline)
3. data validation: schemas, value ranges, missing-value policy, size budget
4. site-data consistency: every cell has every field, and values match the processed data
5. html-validate
6. Playwright at 375×812 and 1280×800:
   - no console errors
   - the expected number of cells renders
   - switching layers changes colours
   - panel values match the data
   - no horizontal overflow
   - everything reachable by keyboard
7. axe-core: zero serious or critical violations
8. with `--lighthouse`: mobile performance ≥ 85, accessibility ≥ 95, best practices ≥ 90, SEO ≥ 90, with reports saved to `artifacts/`

It ends with exactly one line: `CHECK: PASS (n checks)` or `CHECK: FAIL (k of n failed: names)`.

Tests that need the raw-data cache are marked `raw` and run locally; CI runs everything else. Define this split once, in Phase 0, and never use it to hide a failure.

`uv run python scripts/features.py [--phase N]` prints `Phase N: a of b resolved, c blocked` for each phase, then lists anything unresolved along with its blocker. A feature counts as resolved when either:
- it passes, or
- Samraj has approved dropping it, recorded in `DECISIONS.md` and in the feature's `dropped` field.

CI (GitHub Actions) runs the quick checks on every push. The site deploys to GitHub Pages from `main` only when those checks pass.

---

## 11. Phase 0: setup, with Samraj

1. **Check the machine:**
   - OS
   - git
   - `gh`, the GitHub CLI. This Mac has no Homebrew, so if `gh` isn't found, install it as a checksum-verified release binary into `~/.local/bin` (no sudo, no Homebrew) rather than proposing a package manager. Once it's installed, ask Samraj to run `gh auth login` himself; never run it for him.
   - `uv`. If missing, install it, then run `uv python install 3.12` and create the project's `.venv` with it (§2.9). Confirm `uv run python --version` reports 3.12 before continuing; the system Python (3.9.6) is never used for this project.
   - Node LTS
   - free disk space

   Explain any missing install in a sentence or two and ask before installing it.
2. **Walk through D1–D12 one at a time.** For each, give your recommendation, why, the main alternative, and what would change. He may defer D7 and D8; use provisional defaults for those.
3. **Scaffold the repo from §4:**
   - `CLAUDE.md`, at most 150 lines, covering: non-negotiables, loop protocol, commands, file map, STATUS format. It loads every session, so keep it tight and point to PROMPT.md for detail.
   - `features.json`, seeded from §12 and adapted to his decisions
   - the log files
   - `.gitignore`
   - licence files
   - working skeletons of `check.py` and `features.py`
   - `.claude/launch.json`
   - the CI workflow
   - a placeholder site page
4. **Publish.** Create the GitHub repo with `gh`, push, set Pages to deploy from GitHub Actions, and print the placeholder URL's HTTP status.
5. **Explain the plan.** Give Samraj a five-minute plain-language walkthrough. Then ask him to say in one sentence what the Priority score means. This checks that the plan is clear; it isn't a test of him.
6. **Hand over the instructions.** Print the phase instructions for Phases 1–5 from §13, filled in with his decisions. Then stop.

---

## 12. Backlog: seed for features.json

Feature schema:
```json
{"id": "P1-04", "phase": 1, "title": "Daytime heat per cell",
 "acceptance": ["..."], "depends_on": ["P1-02", "P1-03"],
 "passes": false, "blocked_on": null, "dropped": null, "evidence": null}
```

### Phase 0: setup
- **P0-01 Machine ready.** Tool versions are printed, and `gh auth status` shows he's logged in.
- **P0-02 Decisions recorded.** D1–D12 are in `DECISIONS.md`, each approved, provisional, or deferred, with Samraj's words.
- **P0-03 Scaffold.**
  - The §4 layout exists.
  - `CLAUDE.md` is at most 150 lines.
  - `features.json` validates against the schema.
  - `features.py` prints counts.
- **P0-04 Checks and CI.** `check.py --quick` prints `CHECK: PASS` on the scaffold, and the first CI run is green (status printed via `gh`).
- **P0-05 Live placeholder.** The public repo is pushed, Pages deploys from Actions, and the placeholder URL returns 200 (printed).

### Phase 1: data foundation
- **P1-01 Pilot boundary.**
  - `data/processed/pilot_area.geojson` (EPSG:4326), with provenance.
  - Area in km² printed.
  - Preview PNG in `artifacts/`.
- **P1-02 Grid.**
  - H3 cells at the D3 resolution cover the boundary; the inclusion rule is documented.
  - Cell count printed.
  - Tests: IDs are valid, there are no duplicates, and the cells cover ≥ 99% of the boundary.
- **P1-03 Download cache.**
  - `pipeline/fetch.py` handles retries, backoff, checksums, and the manifest.
  - Re-runs use the cache.
  - Tests use mocked responses.
- **P1-04 Daytime heat.**
  - Per-cell mean and 90th-percentile hot-season LST in °C.
  - Scene list and cloud statistics recorded.
  - Values fall inside a documented plausible range.
  - Map PNG.
- **P1-05 Night heat — dropped by D4.** MODIS's 1 km pixels give only ~25 samples over Landhi's 25 km², too coarse to be useful. See the "v2 candidates" note in §6 (ECOSTRESS, ~70 m) for the v2 route.
- **P1-06 People.**
  - Per-cell counts from two sources, with a comparison table.
  - Source chosen per D4.
  - Pilot total within the documented tolerance of an independent figure, or the gap explained.
  - Map PNG.
- **P1-07 Age groups.** Per-cell shares aged 60+ and under 5, each in [0, 1]. The rule for zero-population cells is tested.
- **P1-08 Built environment.** Building footprint fraction and green-cover fraction per cell, with coverage caveats in `SOURCES.md`.
- **P1-09 Access.**
  - Distance per cell to the nearest health facility and to the nearest verified relief centre.
  - `centres.csv` schema enforced.
  - Unverified centres excluded, and listed for Samraj.
  - OSM records no relief facility of any organisation inside Landhi Town — re-checked on 2026-09-26 across every spelling variant (Edhi/Edhee/Aidhi, Saylani/Silani/Sailani, Chhipa/Chipa/Chippa, Al-Khidmat, Aman), the Urdu forms, and the `social_facility`, `charity`, `office=ngo`, and ambulance-station tags: 133 objects in the wider city, zero inside the boundary. So this feature has no open-data fallback. Eleven unverified candidates within 7 km are listed in `data/manual/centre_candidates.csv`; none may enter the model. If it's still blocked when Phase 1 runs, split it into P1-09a (health-facility distance, unblocked) and P1-09b (relief-centre distance, blocked on Samraj verifying a centre in person).
- **P1-10 Load-shedding feasibility (optional).** Write `docs/load-shedding-feasibility.md` covering what K-Electric publishes, whether areas can be matched to cells reliably, and a recommendation. Build the indicator only if Samraj approves; otherwise he approves dropping it.
- **P1-11 Indicator table.**
  - `data/processed/indicators.parquet` and `.csv`.
  - `docs/data-dictionary.md`.
  - QA report with histograms and a missing-value summary.
  - Schema tests.

### Phase 2: model
- **P2-01 Normalisation.** Both methods implemented. Tests: output in [0, 1], monotonic, direction respected, ties and constant columns handled.
- **P2-02 AHP tool.** Works end to end in the terminal and passes the tests in §7.
- **P2-02b Samraj's weights.** `config/weights.yaml` is written by the tool from his answers, with CR < 0.10. Blocked on Samraj until then.
- **P2-03 Scores.**
  - H, E, V, Priority, Intensity, and top reasons per cell.
  - Property tests: weights sum to 1; raising a risk-increasing indicator never lowers Priority; results don't depend on indicator order.
- **P2-04 Sensitivity.**
  - Seeded Monte Carlo (N ≥ 1000).
  - Per-cell median rank, 90% interval, P(top 20%), and confidence class.
  - Reproducibility test and figures.
- **P2-05 Validation pack.**
  - Equal-weights comparison.
  - The single located-incident face-validity check for Landhi (D14), reported and labelled weak evidence — not a city-scale correlation, which is rejected by D14 and must not be built.
  - English-language expert-ranking form (D9), plus an analysis script tested on SYNTHETIC data.
- **P2-06 Model report.** `docs/model-report.md` containing a plain summary, a maths appendix, figures, limitations, and the checker subagent's verdict.

### Phase 3: website
- **P3-01 DESIGN.md.** The plan, a review against the brief and the avoid-list, and the revisions made. Samraj approves it, or it stays provisional.
- **P3-02 Shell.** All pages exist, are responsive, and pass html-validate.
- **P3-03 Map and legend.** Cells render from site data, with a quintile legend and visible basemap attribution.
- **P3-04 Layers and panel.**
  - All five layers work.
  - The panel shows class, rank, reasons, values with units, and confidence.
  - Keyboard accessible.
  - End-to-end tests.
- **P3-05 Confidence.** Confidence layer and panel wording, based on P2-04.
- **P3-06 Content pages.**
  - How it works: plain version plus maths appendix.
  - Data and credits: every attribution and licence.
  - About: disclaimer, AI disclosure, and contact per D11.
- **P3-07 Urdu — dropped by D9.** English only for v1. UI strings stay externalised in `site/i18n/en.json` so Urdu can be added in a later version.
- **P3-07b Urdu reviewed — dropped by D9.** No longer applicable; dropped alongside P3-07.
- **P3-08 Quality gates.** Playwright, axe, the page-weight budget, and the §10 Lighthouse thresholds all pass.
- **P3-09 Deploy.** Pages deploys from CI, the live URL returns 200, and the Playwright smoke suite passes against the live URL.

### Phase 4: allocation
- **P4-01 Solver.**
  - LP and greedy in `pipeline/allocate.py`.
  - `docs/allocation.md` with the formulation and a hand-solvable example.
  - All §8 tests pass.
  - Checker subagent's verdict recorded.
- **P4-02 Scenarios.** Precomputed scenarios per D8, exported for the site with plain-language summaries. Verify the litres-per-person figure against the Sphere Handbook and record the citation — `config/allocation.yaml` starts marked `UNVERIFIED`.
- **P4-03 Planner page.**
  - Pick centres and stock, then see the allocation on the map and in a table.
  - Approximate mode is labelled.
  - Totals never exceed stock (end-to-end tests).

### Phase 5: field kit and release
- **P5-01 Field briefs.**
  - One A4 page per named locality inside the pilot area, in English (D9).
  - Rendered from HTML with Playwright for consistent, testable output.
  - PDF and PNG each under 1 MB, so they send easily on WhatsApp.
- **P5-02 Offline.**
  - A service worker caches the app shell and the data.
  - The offline view uses a simplified road outline instead of basemap tiles.
  - Tested offline in Playwright.
- **P5-03 NGO one-pager.**
  - `docs/pitch/one-pager.md` and a PDF, in English (D9).
  - Covers: what it is, what it isn't, how to read the map in two minutes, and what feedback is wanted.
  - Written for whichever organisation agrees to host (D13) — Edhi, Saylani, Chhipa, Al-Khidmat, Aman, or another — decided once one has said yes, not written generically for all of them.
  - Leaves a blank line for a handwritten contact (D11c); the site itself shows none.
  - A draft for Samraj to edit. Claude never sends it.
- **P5-04 README.** Overview, screenshots, reproduce steps, credits, licences, AI disclosure, and `CITATION.cff`.
- **P5-05 Release.**
  - The full check, including Lighthouse, passes.
  - P2-02b is resolved.
  - `CHANGELOG.md` is written.
  - `v1.0.0` is tagged and pushed.

### Phase 6: after fieldwork (not a goal until Samraj has real data)
- **P6-01 Expert agreement.** Import real rankings, compute agreement with confidence intervals, and write it up. Samraj decides any model changes.

---

## 13. Phase instructions

Each block below is a plain message Samraj pastes and sends as-is; it is not a slash command. Each is its own finish line, so don't combine phases. There is no separate evaluator model here — after every turn, judge for yourself, against the finish line stated in the message, whether the phase is done; if it isn't, continue immediately with the next turn without waiting to be told to carry on, until the finish line is met, the turn cap is hit, or you must stop and print "BLOCKED ON SAMRAJ". Print the STATUS block (§3.3) at the end of every turn regardless, so progress is visible even mid-phase.

**Phase 1**
```
Work through Phase 1 of PROMPT.md, one feature per turn, following the loop protocol in CLAUDE.md. After each turn, without waiting for me, continue straight into the next turn until one of these is true: `uv run python scripts/features.py --phase 1` prints "Phase 1: N of N resolved, 0 blocked" and `uv run python scripts/check.py --quick` prints "CHECK: PASS" in the same turn (phase complete); every remaining unresolved Phase 1 feature is blocked on me, in which case print "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md and stop; or 30 turns have passed, in which case stop and report where things stand. Verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate data or evidence; never delete, skip, or loosen a test or acceptance criterion; document every dataset in data/SOURCES.md. If P1-09 is blocked because no centre is verified yet, split it into P1-09a (distance to nearest health facility, from OSM) and P1-09b (distance to nearest verified relief centre), and carry on with P1-09a while P1-09b stays blocked.
```

**Phase 2**
```
Work through Phase 2 of PROMPT.md, one feature per turn, following the loop protocol in CLAUDE.md. After each turn, without waiting for me, continue straight into the next turn until one of these is true: `uv run python scripts/features.py --phase 2` shows every Phase 2 feature resolved, except that P2-02b may remain as the only unresolved feature blocked on me (the model then runs on provisional equal weights, labelled as provisional), and `uv run python scripts/check.py --quick` prints "CHECK: PASS" in the same turn (phase complete); every remaining unresolved Phase 2 feature is blocked on me, in which case print "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md and stop; or 30 turns have passed, in which case stop and report where things stand. For P2-01 to P2-05, use the checker subagent from PROMPT.md section 3.1 and record its verdict before marking a feature passing. Remember D6: AHP weights Vulnerability's six indicators only; the three H/E/V dimension exponents stay fixed at 1/3. Verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate data, results, or validation; never delete, skip, or loosen a test or acceptance criterion.
```

**Phase 3**
```
Work through Phase 3 of PROMPT.md, one feature per turn, following the loop protocol in CLAUDE.md. Note that P3-07 and P3-07b are dropped by D9 — English only for v1 — so no Urdu or RTL check is part of the gates. After each turn, without waiting for me, continue straight into the next turn until one of these is true: `uv run python scripts/features.py --phase 3` shows every Phase 3 feature resolved, `uv run python scripts/check.py --lighthouse` prints "CHECK: PASS", and you have printed the live GitHub Pages URL with its HTTP status (200) and the result of the Playwright smoke suite run against that live URL, all in the same turn (phase complete); every remaining unresolved Phase 3 feature is blocked on me, in which case print "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md and stop; or 35 turns have passed, in which case stop and report where things stand. Write DESIGN.md before any styling, and review screenshots at 375 px and 1280 px after every UI feature. Verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate evidence; never delete, skip, or loosen a test, threshold, or acceptance criterion.
```

**Phase 4**
```
Work through Phase 4 of PROMPT.md, one feature per turn, following the loop protocol in CLAUDE.md. After each turn, without waiting for me, continue straight into the next turn until one of these is true: `uv run python scripts/features.py --phase 4` prints "Phase 4: N of N resolved, 0 blocked", `uv run python scripts/check.py --quick` prints "CHECK: PASS", and the allocation test output you printed shows the LP objective is at least the greedy objective on every test instance, all in the same turn (phase complete); every remaining unresolved Phase 4 feature is blocked on me, in which case print "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md and stop; or 20 turns have passed, in which case stop and report where things stand. Use the checker subagent for P4-01 and record its verdict. In P4-02, verify the litres-per-person figure against the Sphere Handbook and record the exact citation — `config/allocation.yaml` currently marks it `UNVERIFIED` (D8). Never fabricate results; never delete, skip, or loosen a test or acceptance criterion.
```

**Phase 5**
```
Work through Phase 5 of PROMPT.md, one feature per turn, following the loop protocol in CLAUDE.md. After each turn, without waiting for me, continue straight into the next turn until one of these is true: `uv run python scripts/features.py` shows every feature in Phases 0 to 5 resolved, including P2-02b, and `uv run python scripts/check.py --lighthouse` prints "CHECK: PASS", and `git ls-remote --tags origin` shows v1.0.0, all confirmed in the same turn (phase complete); every remaining unresolved feature is blocked on me, in which case print "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md and stop; or 25 turns have passed, in which case stop and report where things stand. Never send, post, or submit the NGO one-pager or anything else on my behalf. Verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate evidence; never delete, skip, or loosen a test, threshold, or acceptance criterion.
```

**Fix-it (whenever checks fail and keep failing)**
```
First print the current commit hash as the start point. Then work turn by turn to find and fix the root cause, not the symptom. After each turn, without waiting for me, continue straight into the next turn until one of these is true: `uv run python scripts/check.py --quick` prints "CHECK: PASS" and you have printed `git diff --stat <start-hash> -- tests/` with a short explanation showing no test was deleted, skipped, or loosened (fixed); the same failure has defeated you twice, in which case write the diagnosis in PROGRESS.md and QUESTIONS.md and print "BLOCKED ON SAMRAJ"; or 10 turns have passed, in which case stop and report where things stand. End every turn with the STATUS block.
```

---

## 14. What "done" means for v1

- The site is live on GitHub Pages, every check passes (including Lighthouse), and `v1.0.0` is tagged.
- The weights are Samraj's own, set with the AHP tool, or he has recorded a decision to ship equal weights.
- A mentor could check the model report and the allocation doc line by line.
- The README explains how to reproduce everything, credits every source, and discloses the AI assistance.
- Samraj has a field brief and a one-pager he can take into a relief centre and explain in his own words.
