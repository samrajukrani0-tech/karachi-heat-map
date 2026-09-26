# Karachi Heat Priority Map — working rules

Full detail is in **PROMPT.md**. This file is the condensed version that loads
every session. When the two disagree, PROMPT.md wins.

**What this is:** a free, mobile-first site that helps a Karachi relief team decide
where heat-relief support (water, ORS, cooling points, ambulance standby) should go
first during a heatwave, and why. Pilot area: **Landhi Town** (25.37 km²).
**What it is not:** an official warning system, a mortality model, or a verdict on
any neighbourhood. Point people to the PMD and PDMA Sindh for warnings.

Samraj is a first-year A Level student (Maths, Further Maths, Physics, CS). Two jobs
of equal weight: build excellent working software, and make sure he understands and
owns every modelling decision.

## Non-negotiables

1. **Never invent** data, coordinates, sources, citations, scores, screenshots or
   validation results. If something is unavailable, say so in QUESTIONS.md and use a
   documented fallback, or mark the feature blocked. Non-real fixtures are labelled
   `SYNTHETIC` in the filename and contents and never reach the live site.
2. **Tests are sacred.** Never delete, skip or loosen a test, threshold or acceptance
   criterion to get checks passing. If one is genuinely wrong, propose the change in
   DECISIONS.md and wait for Samraj.
3. **Evidence or it didn't happen.** A feature passes only if you ran its checks in
   the same turn and they passed. Record that evidence in features.json.
4. **Samraj owns the judgement calls.** D1–D12 are settled in DECISIONS.md; anything
   new gets a recommendation, reasons and the main alternative, then he decides.
5. **Aggregated, respectful data.** No individual-level or personal data. No scraping
   of social media or of sites whose terms forbid it (e.g. Google Maps). Say "higher
   priority for support" — never "dangerous", "bad" or "unsafe".
6. **No outside actions.** Never email, message, post, submit forms or contact any
   organisation. Write drafts; Samraj sends them.
7. **Credentials.** Never ask for, type or store a password or token. If a tool needs
   a login, ask Samraj to run it in the terminal pane. No force-pushing, no history
   rewriting, nothing outside this folder. Ask before installing anything system-wide.
8. **Good open-data citizen.** Honour every licence and attribution. Be gentle with
   Overpass. Follow basemap tile policies. Cache downloads. Read cloud-optimised
   rasters in windows, never whole scenes.
9. **Cross-platform.** Python only (no bash-only tooling), `pathlib` everywhere, no
   hard-coded absolute paths.

## Settled decisions (DECISIONS.md has the reasoning)

- **D2** pilot area: Landhi Town, OSM relation 16350631, 25.37 km².
- **D3** grid: H3 resolution 9 (~0.105 km², ~242 cells).
- **D4/D17/D19** 5 indicators: `lst_day_mean` (H), `population` (E), and `lack_green`,
  `dist_health`, `dist_centre` (V). Dropped: night LST and RWI (too coarse for 25 km²);
  the two age **shares** (correlate at exactly −1.0 — one administrative zone variable);
  `built_fraction` (≈ +0.93 with `lack_green`, and double-counts Hazard). Age **counts**
  and `built_fraction` are still computed as panel context, like the LST p90.
- **D20** load-shedding dropped for v1: K-Electric publishes feeder names, not geography,
  so a per-cell value would mean inventing a service boundary. The report must say the
  mechanism Edhi named is the one the model cannot see.
- **D5** robust min–max, clipped at the 5th/95th percentile.
- **D6** Priority = weighted geometric mean of H, E, V; H and V floored at 0.01,
  **E deliberately not floored** (E = 0 means nobody lives there).
- **D7** AHP weights the six vulnerability indicators only; dimension exponents stay
  fixed at ⅓. Weights are provisional until Samraj runs the tool (P2-02b).
- **D8** allocation settings are **provisional** until the field visit.
- **D9** English only for v1; strings still externalised in `site/i18n/en.json`.
- **D10** MIT code, CC BY 4.0 docs, **ODbL 1.0 for `data/processed`** (OSM-derived).
- **D11** public repo `karachi-heat-map`; full name, no school named; no contact.
- **D12** AI assistance disclosed in the README and on the About page.
- **D13** any verified relief org counts (Edhi, Saylani, Chhipa, Al-Khidmat…).
  `centres.csv` carries `role` + `can_hold_stock`: the index counts every facility,
  the allocation LP draws stock only from `can_hold_stock: yes`.
- **D14** face validity for Landhi rests on one reported incident and is labelled weak;
  the expert ranking (§7c) is the real validation. Don't rebuild the city-scale check.

## Loop protocol: every turn

1. **Orient** — read the last three PROGRESS.md entries, run `features.py`, skim
   DECISIONS.md and QUESTIONS.md for new answers, check `git status` and `git log`.
2. **Health check** — `check.py --quick`. A regression becomes this turn's feature.
3. **Pick** the lowest-numbered unresolved feature in the current phase that is not
   blocked and whose dependencies pass. Split it if it is too big (`P1-04a`/`b`).
   Splitting and adding features is fine; deleting or loosening is not.
4. **Plan** in three to six lines.
5. **Build** the smallest complete version; write or extend tests first where practical.
6. **Verify** — the feature's own checks, then `check.py --quick`. For anything
   visible, screenshot at 375×812 and 1280×800 and confirm the console is clean. For
   P2-01…P2-05 and P4-01, use a fresh checker subagent: give it the spec and data but
   not your conclusions, ask it to re-derive three spot values, record its verdict.
7. **Record** — features.json (`passes` + evidence, only if verified this turn),
   PROGRESS.md, a LEARNING_LOG.md entry, DECISIONS.md and QUESTIONS.md as needed.
8. **Commit** — e.g. `feat(P1-04): hot-season daytime LST per cell`. Push when checks pass.
9. **Report** the STATUS block. Nothing comes after it.

One feature per turn. If the same problem defeats you twice, write a short diagnosis
in PROGRESS.md, add it to QUESTIONS.md if Samraj can unblock it, and move on. Keep the
transcript short; long logs go in `artifacts/logs/`.

## LEARNING_LOG.md entries

After each feature: **what and why** in three to six plain sentences; **the key idea
in A Level terms** (only where the link is genuine — eigenvectors for AHP weights,
thermal radiation for how satellites measure surface temperature, correlation for
validation); and **two or three questions** Samraj should be able to answer, with
answers inside a `<details>` block.

## Commands

```
uv run python scripts/check.py --quick        # quality gates, ends in one CHECK: line
uv run python scripts/check.py --lighthouse   # adds Lighthouse (Phase 3 onward)
uv run python scripts/features.py [--phase N] # progress
uv run python -m pipeline.run --all           # rebuild everything from the cache
uv run python -m pipeline.ahp                 # Samraj runs this himself (P2-02b)
uv run pytest -m "not raw"                    # what CI runs
```

`raw`-marked tests need `data/raw/` and run locally only. That split is fixed and must
never be used to hide a failure.

## File map

```
config/      area, indicators, weights, model, allocation (YAML) — the decisions
pipeline/    fetch, grid, indicators, model, ahp, sensitivity, validate, allocate, export
scripts/     check.py, features.py, build_site_data.py, field_briefs.py
data/raw/    gitignored download cache + manifest.json
data/manual/ centres.csv — verified in person, the only source for relief centres
data/processed/  small outputs, under 5 MB total (ODbL)
data/SOURCES.md  every dataset: URL, licence, access date, resolution, caveats
site/        static HTML/CSS/vanilla JS, no build step, deployed to GitHub Pages
tests/       pytest; tests/e2e for Playwright
docs/        model-report.md, allocation.md, data-dictionary.md, pitch/
artifacts/   gitignored screenshots, logs, Lighthouse reports
```

Python is 3.12 via uv (`.venv`). `h3` is pinned below 4.4: this is an Intel Mac and
4.4+ ships no x86_64 macOS wheel.

## STATUS block — ends every turn

```
STATUS
Feature: P1-04 Daytime heat per cell: PASS
Evidence: pytest 38 passed; check.py --quick CHECK: PASS; LST 31.2 to 52.8 °C (inside documented range)
Progress: Phase 1 6 of 11 resolved; overall 11 of 42
Blocked on Samraj: 1 (Q2: verify a relief centre)
Next: P1-06 People per cell
Explain it: hotter ground on summer afternoons is the "heat" part of the score.
Turns this goal: 7 (limit 30)
```
