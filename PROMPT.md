# Karachi Heat Priority Map: master prompt for Claude Code

This file drives a loop-based build in Claude Code. Section 0 is for Samraj. Everything after it is for Claude.

---

## 0. For Samraj: how to run it

1. Open the Claude desktop app, go to the **Code** tab, and start a new session. Environment: **Local**. Model: **Opus 5.5**. Permission mode: **Auto**. Folder: an empty folder that contains only this file (for example `karachi-heat-map`).
2. Send this as your first message. Phase 0 is a conversation, not a loop:
   > Read PROMPT.md in full and run Phase 0 with me — check my setup first, then ask me the decisions one at a time. Don't start Phase 1.
3. At the end of Phase 0, Claude prints one `/goal` command per phase, filled in with your decisions. Paste the Phase 1 goal and let it run.
   - `/goal` on its own shows turns, time, token spend, and the evaluator's latest reason. `/goal clear` stops the loop.
   - You can type a message at any time. Claude reads it once its current action finishes.
   - If you hit your usage limit, the goal pauses and continues when the limit resets. Keep the laptop plugged in and awake.
4. Between phases: ask Claude for a code review of that phase's changes (`/code-review`), read the new entries in `LEARNING_LOG.md`, answer anything in `QUESTIONS.md`, then paste the next goal.
5. If checks fail and keep failing, use the fix-it goal at the end of §13.

---

## 1. Mission and context

You are the engineering partner of **Samraj**. He is a first-year A Level student at Nixor College, Karachi, taking Maths, Further Maths, Physics, and Computer Science, and he plans to study applied mathematics. Together you are building a free, public, mobile-first website. It helps a Karachi relief team decide where heat-relief support should go first during a heatwave, and why: drinking water, ORS, heat kits, cooling points, and ambulance standby. It is designed first for a local Edhi Foundation centre or for Saylani Welfare.

Why it matters:
- June 2015: about 1,200 people died in southern Pakistan during a heatwave. Source: AFP, reported by Newsweek Pakistan, https://www.newsweekpakistan.com/?p=867013
- June 2024: Edhi Foundation said it received 568 bodies in Karachi in the five days to 25 June, against a usual ~40 a day. Faisal Edhi said most came from poorer workers' neighbourhoods hit by long power cuts. The Sindh health department disputed that the deaths were heat-related. Sources:
  - Bloomberg: https://bnnbloomberg.ca/karachi-sees-a-surge-in-deaths-as-heat-wave-sears-pakistan-1.2090293
  - Express Tribune: https://tribune.com.pk/story/2473712/heatwave-wreaks-havoc-15-found-dead-on-streets
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
9. **Windows and macOS.** Write scripts in Python (no bash-only tooling), use `pathlib` everywhere, and don't hard-code absolute paths.

---

## 3. Loop protocol: every turn

1. **Orient.**
   - Read the last three entries of `PROGRESS.md`.
   - Run `python scripts/features.py`.
   - Skim `DECISIONS.md` and `QUESTIONS.md` for new answers.
   - Check `git status` and `git log --oneline -10`.
2. **Health check.** Run `python scripts/check.py --quick`. If anything that used to pass now fails, fixing it becomes this turn's feature.
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
Turns this goal: 7 (limit 30)
```

---

## 4. Repository layout

```
karachi-heat-map/
  CLAUDE.md             condensed rules, commands, file map (written in Phase 0)
  PROMPT.md             this file
  features.json         backlog and source of truth for progress
  PROGRESS.md           append-only turn log
  DECISIONS.md          judgement calls: proposed, approved, provisional, deferred
  QUESTIONS.md          things only Samraj can answer
  LEARNING_LOG.md       plain-language explanations and practice questions
  DESIGN.md             site design plan (Phase 3)
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
- **D2 Pilot area.** One locality of roughly 10–60 km² where Samraj can visit a relief centre in person. Before he chooses, compare three to five candidates on:
  - area
  - modelled population
  - known relief centres
  - whether credible June 2024 reporting mentions it (Orangi Town appears in the Express Tribune report above)
- **D3 Grid.** Recommend H3 resolution 9, about 0.105 km² per cell. Landsat's thermal sensor has a native resolution of about 100 m (delivered at 30 m), so much smaller cells would claim precision the heat data doesn't have. Alternative: resolution 8, about 0.74 km² per cell.
- **D4 Indicators.** Approve or edit the list in §6, including the optional ones.
- **D5 Normalisation.** Recommend robust min–max: clip at the 5th and 95th percentiles, then scale to 0–1. Alternative: percentile rank.
- **D6 Combining dimensions.** Recommend geometric: Priority = H^(1/3) × E^(1/3) × V^(1/3). With this, high values in two dimensions can't hide a near-zero third. Alternative: weighted arithmetic mean.
- **D7 Weights.** Samraj sets them with the AHP tool (§7). Until then, use equal weights and flag them as "provisional" in the data and on the site.
- **D8 Allocation.** Decide:
  - what is distributed (water, ORS, heat kits)
  - units per person in need
  - who counts as in need
  - maximum service distance
  - whether a minimum share goes to the highest-priority cells
- **D9 Languages.** Recommend English and Urdu. Samraj reviews every Urdu string before it counts as final.
- **D10 Licences.** Recommend MIT for code and CC BY 4.0 for docs and site text. Each dataset keeps its own licence.
- **D11 Public identity.** Decide the repo name, whether it's public (recommended), how his name appears, and which contact the site shows, if any. A project-only email is safer than a personal one.
- **D12 AI-assistance disclosure.** Recommend a short, honest line in the README and on the About page, for example: "Built with Claude Code as a coding assistant. Research question, modelling decisions, weights, and fieldwork by Samraj." Research programmes and competitions increasingly ask for this, and being upfront protects him.

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
| Hot-season daytime land surface temperature, °C (per-cell mean and 90th percentile) | Hazard | Landsat 8/9 Collection 2 Level-2 via the Microsoft Planetary Computer STAC API (`landsat-c2-l2`, surface-temperature asset such as `lwir11`). Use April–June across several recent years, mask cloud and shadow with `qa_pixel`, and take a median composite. Check the USGS scale and offset (documented as 0.00341802 × DN + 149.0 = kelvin). | AWS Earth Search (Element 84) STAC. Use Google Earth Engine only if Samraj has set it up. |
| Night-time land surface temperature, °C (optional) | Hazard | MODIS LST night band (daily or 8-day) via Planetary Computer, same season | 1 km resolution, so area-weight to cells and label it coarse. Nights that don't cool down matter for health. |
| People per cell | Exposure | Meta (Data for Good) high-resolution population density for Pakistan on HDX (about 30 m), and WorldPop constrained 100 m | Compute both, compare, and choose per D4. Sanity-check the pilot total against an independent figure (e.g. Pakistan Bureau of Statistics 2023 census for a matching unit), using a documented tolerance. Never adjust data to hit that figure. |
| Share aged 60+; share under 5 | Vulnerability | Meta demographic layers on HDX | Handle zero-population cells explicitly. |
| Building footprint fraction | Vulnerability | Google Open Buildings or Microsoft Global ML Building Footprints (check Karachi coverage) | OSM buildings, with a completeness caveat. |
| Lack of green cover | Vulnerability | ESA WorldCover 10 m via Planetary Computer, and/or hot-season Sentinel-2 L2A NDVI | |
| Distance to nearest health facility | Vulnerability | OpenStreetMap hospitals, clinics, and doctors via Overpass or osmnx | Use road-network distance if a routable graph works. Otherwise use straight-line distance × a documented circuity factor (e.g. 1.3). Measure and report gaps in OSM coverage. |
| Distance to nearest verified relief centre | Vulnerability and allocation | `data/manual/centres.csv` (name, org, lat, lon, source, verified_by, verified_on), confirmed by Samraj | OSM can suggest candidates, but exclude them until he verifies them. This indicator is used in both the index and the allocation; note that double use in the model report. |
| Relative wealth (optional) | Vulnerability | Meta Relative Wealth Index for Pakistan on HDX, about 2.4 km tiles | Coarse: area-weight and label it. |
| Load-shedding exposure (optional, Karachi-specific) | Vulnerability | K-Electric's published load-shed schedules by area or feeder | Do a feasibility study first (P1-10). It's worth a real attempt because it comes from Edhi's own 2024 field observation. It never blocks other work, and it is built only if Samraj approves. |

Housekeeping:
- Raw downloads live in `data/raw/` (gitignored), with `manifest.json` recording URL, sha256, bytes, date, and licence.
- `python -m pipeline.run --all` rebuilds everything from the cache.
- Record exactly which scenes and years were used and the population data's reference year. Note any mismatch in the model report.

---

## 7. Model

- **Framework.** IPCC-style risk with three dimensions: Hazard (H), Exposure (E), and Vulnerability (V).
- **Indicator config.** `config/indicators.yaml` holds, for each indicator:
  - id
  - English and Urdu names
  - dimension
  - unit
  - direction (+1 means higher = more risk)
  - source
  - transform (e.g. `log1p` for people)
  - a short plain-language phrase in both languages for the "top reasons" list
- **Normalise** each indicator to 0–1 per D5, where 1 means more risk. A constant indicator becomes 0, with a warning.
- **Within a dimension**, take a weighted mean using the weights in `config/weights.yaml`.
- **Across dimensions**, combine per D6 to get **Priority**, which accounts for how many people live in the cell. Also compute **Intensity** = √(H × V), the per-person view, for the equity discussion in the report.
- **Top reasons.** For each cell, list the three indicators that push its score furthest above the pilot-area median, as short phrases in both languages.
- **AHP tool** (`python -m pipeline.ahp`). Samraj runs it himself in the terminal pane.
  1. It asks pairwise questions in plain English on Saaty's 1–9 scale, e.g. "For heat harm in this area, how much more important is X than Y?"
  2. It computes the weights as the principal eigenvector, using power iteration.
  3. It reports λmax, CI = (λmax − n) / (n − 1), and CR = CI / RI, using Saaty's random-index table.
  4. If CR ≥ 0.10, it shows which answers conflict and asks those again.
  5. It saves the answers, weights, CR, `decided_by: Samraj`, and the date.
  - Tests: a published textbook example is reproduced within tolerance; a perfectly consistent matrix gives CR ≈ 0; an inconsistent matrix is caught.
- **Sensitivity analysis** (fixed seed, N ≥ 1000).
  - Perturb the weights with a Dirichlet distribution centred on the chosen weights; document the concentration parameter.
  - Swap between the normalisation choices and between the aggregation choices.
  - Report, per cell: median rank, 90% rank interval, and probability of being in the top 20%.
  - Confidence classes: high (≥ 0.8), medium (0.5–0.8), low (< 0.5), unless Samraj decides otherwise.
- **Validation**, honest and clearly labelled:
  - (a) Agreement with an equal-weights baseline (Spearman ρ).
  - (b) Face validity at locality level against credible, cited reporting on the June 2024 heatwave. No invented locations.
  - (c) An expert-ranking protocol: a bilingual one-page form on which field staff rank 10–15 named localities, plus an analysis script (Spearman ρ, Kendall τ, bootstrap confidence intervals). Test the script only on SYNTHETIC data until Samraj brings real rankings.
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
1. Field coordinators on phones, often outdoors in bright sun. Many of them read Urdu more comfortably than English.
2. NGO leadership, donors, and mentors on laptops, deciding whether to trust the tool.

**Primary job:** within ten seconds, a visitor can see which parts of the pilot area need heat support first, and why.

**Pages:** Map (home), Plan supplies, Field briefs, How it works, Data and credits, About.

**Tech:**
- Static HTML, CSS, and vanilla JavaScript, with no framework and no build step.
- Leaflet pinned to an exact version, either vendored in `site/vendor/` or loaded from a pinned CDN URL with SRI.
- `scripts/build_site_data.py` writes the site's data into `site/data/`.
- Serve locally with `python -m http.server`, configured in `.claude/launch.json` (for the Browser pane) and in the Playwright config.
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

**Urdu:**
- Every UI string lives in `site/i18n/en.json` and `site/i18n/ur.json`.
- Use `dir="rtl"`, and Noto Nastaliq Urdu with sensible fallbacks.
- Remember the language choice in localStorage, wrapped in try/catch.
- Put draft Urdu strings in a review queue in `QUESTIONS.md`. Until Samraj approves them, show a small "translation under review" note.

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
  - type roles: one Latin typeface, one Nastaliq typeface
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

`python scripts/check.py [--quick] [--lighthouse]` runs, in order:
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
   - Urdu flips to RTL and key strings change
   - no horizontal overflow
   - everything reachable by keyboard
7. axe-core: zero serious or critical violations
8. with `--lighthouse`: mobile performance ≥ 85, accessibility ≥ 95, best practices ≥ 90, SEO ≥ 90, with reports saved to `artifacts/`

It ends with exactly one line: `CHECK: PASS (n checks)` or `CHECK: FAIL (k of n failed: names)`.

Tests that need the raw-data cache are marked `raw` and run locally; CI runs everything else. Define this split once, in Phase 0, and never use it to hide a failure.

`python scripts/features.py [--phase N]` prints `Phase N: a of b resolved, c blocked` for each phase, then lists anything unresolved along with its blocker. A feature counts as resolved when either:
- it passes, or
- Samraj has approved dropping it, recorded in `DECISIONS.md` and in the feature's `dropped` field.

CI (GitHub Actions) runs the quick checks on every push. The site deploys to GitHub Pages from `main` only when those checks pass.

---

## 11. Phase 0: setup, with Samraj

1. **Check the machine:**
   - OS
   - git
   - `gh auth status` (if he isn't logged in, ask Samraj to run `gh auth login` himself)
   - Python ≥ 3.11
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
6. **Hand over the goals.** Print the `/goal` commands for Phases 1–5 from §13, filled in with his decisions. Then stop.

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
- **P1-05 Night heat (optional).** Per-cell night LST, area-weighted and labelled coarse. If the data can't be obtained, record why and ask Samraj to approve dropping this feature.
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
  - Cited face-validity check.
  - Bilingual expert-ranking form, plus an analysis script tested on SYNTHETIC data.
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
- **P3-07 Urdu.** Full string set, RTL layout, Nastaliq font, and a remembered language toggle, with the review queue in `QUESTIONS.md`.
- **P3-07b Urdu reviewed.** Samraj has approved every string. Blocked on Samraj until then.
- **P3-08 Quality gates.** Playwright, axe, the page-weight budget, and the §10 Lighthouse thresholds all pass.
- **P3-09 Deploy.** Pages deploys from CI, the live URL returns 200, and the Playwright smoke suite passes against the live URL.

### Phase 4: allocation
- **P4-01 Solver.**
  - LP and greedy in `pipeline/allocate.py`.
  - `docs/allocation.md` with the formulation and a hand-solvable example.
  - All §8 tests pass.
  - Checker subagent's verdict recorded.
- **P4-02 Scenarios.** Precomputed scenarios per D8, exported for the site with plain-language summaries.
- **P4-03 Planner page.**
  - Pick centres and stock, then see the allocation on the map and in a table.
  - Approximate mode is labelled.
  - Totals never exceed stock (end-to-end tests).

### Phase 5: field kit and release
- **P5-01 Field briefs.**
  - One A4 page per named locality inside the pilot area, in English and Urdu.
  - Rendered from HTML with Playwright, because the browser shapes Nastaliq correctly and matplotlib doesn't.
  - PDF and PNG each under 1 MB, so they send easily on WhatsApp.
- **P5-02 Offline.**
  - A service worker caches the app shell and the data.
  - The offline view uses a simplified road outline instead of basemap tiles.
  - Tested offline in Playwright.
- **P5-03 NGO one-pager.**
  - `docs/pitch/one-pager.md` and a PDF.
  - Covers: what it is, what it isn't, how to read the map in two minutes, and what feedback is wanted.
  - Written for a local Edhi centre manager and for Saylani, including its SMIT IT-training team.
  - A draft for Samraj to edit. Claude never sends it.
- **P5-04 README.** Overview, screenshots, reproduce steps, credits, licences, AI disclosure, and `CITATION.cff`.
- **P5-05 Release.**
  - The full check, including Lighthouse, passes.
  - P2-02b and P3-07b are resolved.
  - `CHANGELOG.md` is written.
  - `v1.0.0` is tagged and pushed.

### Phase 6: after fieldwork (not a goal until Samraj has real data)
- **P6-01 Expert agreement.** Import real rankings, compute agreement with confidence intervals, and write it up. Samraj decides any model changes.

---

## 13. Goal templates

Each goal is its own finish line, so don't combine phases. The evaluator sees only the transcript, which means the evidence has to be printed there.

**Phase 1**
```
/goal Phase 1 of PROMPT.md is complete, or you have printed "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md, or 30 turns have passed. Complete means that in a single turn you ran `python scripts/features.py --phase 1` and it printed "Phase 1: N of N resolved, 0 blocked", and `python scripts/check.py --quick` printed "CHECK: PASS". While working, follow the loop protocol in CLAUDE.md: one feature per turn, verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate data or evidence; never delete, skip, or loosen a test or acceptance criterion; document every dataset in data/SOURCES.md. Print "BLOCKED ON SAMRAJ" only when every unresolved Phase 1 feature is blocked on him.
```

**Phase 2**
```
/goal Phase 2 of PROMPT.md is complete, or you have printed "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md, or 30 turns have passed. Complete means that in a single turn you ran `python scripts/features.py --phase 2` and it showed every Phase 2 feature resolved, except that P2-02b may remain as the only unresolved feature, blocked on Samraj (the model then runs on provisional equal weights, labelled as provisional), and `python scripts/check.py --quick` printed "CHECK: PASS". For P2-01 to P2-05, use the checker subagent from PROMPT.md section 3.1 and record its verdict before marking a feature passing. While working, follow the loop protocol in CLAUDE.md: one feature per turn, verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate data, results, or validation; never delete, skip, or loosen a test or acceptance criterion. Print "BLOCKED ON SAMRAJ" only when every unresolved Phase 2 feature is blocked on him.
```

**Phase 3**
```
/goal Phase 3 of PROMPT.md is complete, or you have printed "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md, or 35 turns have passed. Complete means that in a single turn: `python scripts/features.py --phase 3` showed every Phase 3 feature resolved, except that P3-07b may remain as the only unresolved feature, blocked on Samraj; `python scripts/check.py --lighthouse` printed "CHECK: PASS"; and you printed the live GitHub Pages URL with its HTTP status (200) and the result of the Playwright smoke suite run against that live URL. Write DESIGN.md before any styling, and review screenshots at 375 px and 1280 px after every UI feature. While working, follow the loop protocol in CLAUDE.md: one feature per turn, verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate evidence; never delete, skip, or loosen a test, threshold, or acceptance criterion. Print "BLOCKED ON SAMRAJ" only when every unresolved Phase 3 feature is blocked on him.
```

**Phase 4**
```
/goal Phase 4 of PROMPT.md is complete, or you have printed "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md, or 20 turns have passed. Complete means that in a single turn you ran `python scripts/features.py --phase 4` and it printed "Phase 4: N of N resolved, 0 blocked", `python scripts/check.py --quick` printed "CHECK: PASS", and the allocation test output you printed shows the LP objective is at least the greedy objective on every test instance. Use the checker subagent for P4-01 and record its verdict. While working, follow the loop protocol in CLAUDE.md: one feature per turn, verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate results; never delete, skip, or loosen a test or acceptance criterion. Print "BLOCKED ON SAMRAJ" only when every unresolved Phase 4 feature is blocked on him.
```

**Phase 5**
```
/goal Phase 5 of PROMPT.md is complete, or you have printed "BLOCKED ON SAMRAJ" followed by every open question from QUESTIONS.md, or 25 turns have passed. Complete means that in a single turn: `python scripts/features.py` showed every feature in Phases 0 to 5 resolved, including P2-02b and P3-07b; `python scripts/check.py --lighthouse` printed "CHECK: PASS"; and `git ls-remote --tags origin` showed v1.0.0. Never send, post, or submit the NGO one-pager or anything else on Samraj's behalf. While working, follow the loop protocol in CLAUDE.md: one feature per turn, verify before marking anything passing, commit after each feature, and end every turn with the STATUS block. Never fabricate evidence; never delete, skip, or loosen a test, threshold, or acceptance criterion. Print "BLOCKED ON SAMRAJ" only when every unresolved feature is blocked on him.
```

**Fix-it (whenever checks fail and keep failing)**
```
/goal First print the current commit hash as the start point. The goal is met when `python scripts/check.py --quick` prints "CHECK: PASS" and you have printed `git diff --stat <start-hash> -- tests/` with a short explanation showing no test was deleted, skipped, or loosened; or when you have printed "BLOCKED ON SAMRAJ" with a diagnosis in PROGRESS.md and QUESTIONS.md; or when 10 turns have passed. Fix causes, not symptoms. If the same failure defeats you twice, write the diagnosis and print "BLOCKED ON SAMRAJ".
```

---

## 14. What "done" means for v1

- The site is live on GitHub Pages, every check passes (including Lighthouse), and `v1.0.0` is tagged.
- The weights are Samraj's own, set with the AHP tool, or he has recorded a decision to ship equal weights. He has also reviewed every Urdu string.
- A mentor could check the model report and the allocation doc line by line.
- The README explains how to reproduce everything, credits every source, and discloses the AI assistance.
- Samraj has a field brief and a one-pager he can take into a relief centre and explain in his own words.
