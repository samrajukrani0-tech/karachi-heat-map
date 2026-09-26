# Progress log

Append-only. One entry per feature, newest at the bottom.

---

## 2026-09-26 — P0-01 Machine ready
**What changed:** checked the machine before any code. macOS 15.7.3 on Intel
(x86_64); git 2.39.5; Node v24.19.0 with npm 11.17.0; 140 GB free; Xcode command
line tools present. Two gaps found and fixed without touching the system: system
Python was 3.9.6, so Python 3.12.14 was installed with `uv python install 3.12`;
`gh` was absent with no Homebrew, so the official cli/cli release binary was
downloaded, SHA-256 verified against the published checksums file, and unpacked to
`~/.local/bin`. Samraj ran `gh auth login` himself.
**Evidence:** `gh auth status` -> logged in as samrajukrani0-tech, scopes gist,
read:org, repo, workflow. `gh --version` -> 2.101.0. `uv run python -V` -> 3.12.14.
**Also found:** the project folder was initially created inside `~/Documents`, which
is iCloud-synced on this machine (a firmlink into com~apple~CloudDocs). Moved to
`~/karachi-heat-map` so the raster cache, `.venv` and `.git` stay off iCloud.
**Next:** P0-02.

## 2026-09-26 — P0-02 Decisions recorded
**What changed:** walked D1–D12 with Samraj one at a time and recorded each in
DECISIONS.md with the options, the recommendation and its reasons, his decision in
his words, a status and the date. Two decisions went against the recommendation or
against PROMPT.md and are recorded as such: D9 (English only for v1) and D7a (AHP
weights vulnerability only, dimension exponents fixed at 1/3).
**Evidence:** DECISIONS.md, 12 entries, `grep -c '^## D'` -> 12.
**Research done for D2 rather than guessed:** candidate town areas computed from OSM
admin_level=7 relations reprojected to EPSG:32642 (Landhi 25.37, Shah Faisal 14.93,
Malir 16.71, Korangi 74.15, Bin Qasim 580.09 km²); 2023 census district populations;
OSM health-facility counts per town; and a direct read of the Dawn report of
25 June 2024. Notable finding: OSM contains **zero** Edhi or Saylani facilities inside
any candidate town, though 55 such objects exist city-wide — so the relief-centre
indicator has no open-data fallback at all.
**Next:** P0-03.

## 2026-09-26 — P0-03/P0-04 Scaffold, checks and CI
**What changed:** repository scaffolded per PROMPT.md §4, adapted for the decisions:
five config files encoding D2–D8, features.json seeded with 42 features from §12 (with
P1-05, P3-07 and P3-07b marked dropped with reasons), `scripts/features.py`,
`scripts/check.py`, a 22-test scaffold suite, three licence files, the CI workflow, and
a placeholder site.
**Evidence:** `uv run python scripts/check.py --quick` -> `CHECK: PASS (3 checks)`;
`uv run pytest` -> 22 passed. CLAUDE.md is 135 lines (limit 150).
**Caught by the tests, not by me:** the first run failed because P3-07b's dropped
reason was 36 characters and `test_dropped_features_state_a_reason` requires more than
40. Fixed by writing a real reason, not by lowering the threshold (§2.2).
**Dependency constraint found:** `h3` 4.4+ publishes no x86_64 macOS wheel, so `uv sync`
tried to compile it from source. Pinned to `>=4.3,<4.4` (4.3.1 is the last cp312
Intel-macOS build). CI runs on Linux and is unaffected, but the pin keeps both
environments identical.
**Next:** P0-05, then Phase 1.

## 2026-09-26 — P0-05 Live placeholder
**What changed:** public repo created and pushed, GitHub Pages switched to deploy from
Actions, placeholder page live. Bumped `actions/checkout` to v5 and `astral-sh/setup-uv`
to v6 after CI warned they were being forced onto Node 24.
**Evidence:** https://github.com/samrajukrani0-tech/karachi-heat-map ; Actions runs
36238295986 and 36238570299 both completed success (check: success, deploy: success);
https://samrajukrani0-tech.github.io/karachi-heat-map/ returns HTTP 200.
**Phase 0 complete:** `uv run python scripts/features.py --phase 0` -> "Phase 0: 5 of 5
resolved, 0 blocked".
**On the critical path for Phase 1:** P1-09 needs at least one relief centre verified in
person (QUESTIONS.md Q2). OSM has no Edhi or Saylani facility inside Landhi Town, so
there is no fallback. Expect to split P1-09 into P1-09a (distance to health facility,
from OSM) and P1-09b (distance to verified relief centre, blocked on Samraj).
**Next:** P1-01 Pilot boundary.

## 2026-09-26 — Pre-Phase-1 side task: relief-centre candidates
**Why:** P1-09b is blocked with nothing to act on. Samraj asked for real named places
near Landhi to ask his contacts about, and supplied the Express Tribune text that Q1
was waiting for.
**What changed:** PROMPT.md replaced with the revised version from Samraj; widened OSM
search; `data/manual/centre_candidates.csv` created with 11 unverified candidates;
QUESTIONS.md Q1 answered and Q3/Q4 opened; SOURCES.md corrected; DECISIONS.md D2
correction appended.
**Evidence:** widened Overpass query over bbox 24.74,67.03,25.00,67.42 returned 133
distinct objects, **0 inside the Landhi boundary**; nearest candidate "Silani Welfare -
Korangi 4" at 24.8278,67.1587, 2.94 km from the Landhi centroid (24.84449, 67.18136),
corroborated by a directory listing giving "Sector 48-E, near Mobile Market, Korangi
No. 4". 37 named health facilities found inside Landhi. `check.py --quick` ->
`CHECK: PASS (3 checks)`.
**Correction recorded, not hidden:** the original "zero Edhi/Saylani" query matched only
two spellings and would have missed "Silani" even inside Landhi. The conclusion stands;
the method did not. Logged in DECISIONS.md and data/SOURCES.md.
**Two findings that change later phases:**
1. Chhipa Welfare moved 12 of the 15 bodies on 24 June 2024 against Edhi's 3, and has
   ambulance points nearer Landhi than any Edhi or Saylani facility. PROMPT.md §1 names
   only Edhi and Saylani. Raised as QUESTIONS.md Q3.
2. Only 1 of ~13 localities named in that reporting is inside the pilot area, so P2-05's
   face-validity check for Landhi rests on a single incident. Raised as QUESTIONS.md Q4
   before Phase 2 builds it.
**Next:** Phase 1, P1-01 Pilot boundary.

## 2026-09-26 — D13 and D14 decided (pre-Phase-1)
**What changed:** the two questions raised by the centre-candidate research were put to
Samraj in full and decided.
- **D13:** any verified relief organisation counts. `centres.csv` gains `role` and
  `can_hold_stock`; the vulnerability indicator counts every verified facility, the
  allocation LP draws stock only from `can_hold_stock: yes`. Prevents Phase 4 allocating
  litres of water to an ambulance standby kerb.
- **D14:** face validity for Landhi rests on the one reported incident, is geocoded to a
  cell and reported as a rank, and is labelled weak. The city-scale correlation is
  rejected, with the reasons recorded so the argument is not re-made.
**Files touched:** DECISIONS.md (D13, D14), QUESTIONS.md (Q3, Q4 closed), CLAUDE.md,
PROMPT.md (§1, §5, §6, §7, §12 P5-03), centres.csv schema, centre_candidates.csv role
guesses, features.json acceptance criteria for P1-09, P2-05 and P4-01, and a new
tests/test_centres.py.
**Evidence:** `uv run pytest` -> 28 passed (was 22); `uv run python scripts/check.py
--quick` -> `CHECK: PASS (3 checks)`; `wc -l CLAUDE.md` -> 140 (limit 150).
**Acceptance criteria were added, never removed or loosened** (§2.2): P1-09 gains the
role-schema requirements, P2-05 the D14 wording, P4-01 the stock-filter test.
**Next:** Phase 1, P1-01 Pilot boundary — nothing now blocks it.

## 2026-09-26 — P1-01 Pilot boundary
**What changed:** `pipeline/config.py` (repo-relative paths, YAML loading),
`pipeline/overpass.py` (polite client with retries, two endpoints and an on-disk raw
cache), `pipeline/boundary.py` (assemble relation 16350631 into a polygon, measure it,
write GeoJSON plus a preview PNG). Added `tests/test_boundary.py`, 11 tests.
**Evidence:** `uv run python -m pipeline.boundary` -> "Area: 25.370 km2 (config expects
25.37 +/- 0.75)", 1 ring, 0 interior holes. Wrote `data/processed/pilot_area.geojson`
(4.4 kB, EPSG:4326) and `artifacts/pilot_area_preview.png` (56 kB). The PNG was viewed:
one closed polygon spanning 67.148–67.219 E, 24.815–24.870 N, centroid 24.84449,
67.18136 — the same centroid computed independently in Phase 0. `uv run pytest` -> 39
passed. `check.py --quick` -> `CHECK: PASS (3 checks)`.
**Design choice worth noting:** the build **refuses to write** the boundary if the
measured area falls outside the documented tolerance, rather than overwriting it and
letting the change pass silently. A future upstream edit to the OSM relation will fail
the build and demand a DECISIONS.md entry, which is the behaviour D2 deserves.
**Two things fixed at the cause, not the symptom:**
1. `ruff` rejected `lru_cache(maxsize=None)`; switched to `functools.cache`.
2. `pytest` could not import `pipeline` because the project has no build backend. Added
   `pythonpath = ["."]` to `[tool.pytest.ini_options]` rather than hacking `sys.path`
   inside the tests.
**Untested branch covered deliberately:** Landhi has no interior holes, so the
inner-ring subtraction never runs on real data. Four unit tests exercise it with
hand-made SYNTHETIC squares, which never reach the site (§2.1).
**Next:** P1-02 Grid.

## 2026-09-26 — P1-02 Grid
**What changed:** `pipeline/grid.py` covers the pilot boundary with H3 resolution-9
cells, applies the documented inclusion rule, checks coverage, and writes
`data/processed/grid.geojson` (130 kB) plus a preview PNG. Added `tests/test_grid.py`,
12 tests. `config/area.yaml` gains `min_area_fraction`.
**Evidence:** `uv run python -m pipeline.grid` -> 265 cells (248 by centre, 17 by the
>=25% rule); "Coverage of the boundary: 99.115% (minimum 99%)"; hexagons 27.080 km2,
clipped 25.145 km2, boundary 25.370 km2, overhang 1.935 km2 excluded by clipping. PNG
viewed: gapless tiling, edge cells exactly where the boundary bulges past a cell centre.
`uv run pytest` -> 51 passed. `check.py --quick` -> `CHECK: PASS (3 checks)`.
**A contradiction in the Phase 0 spec, found and resolved, not papered over.** The
config said "centre inside OR >=50% of area"; PROMPT.md §12 said cells must cover >=99%
of the boundary. Measured, the centre rule reaches only 96.552%, so the two could never
both hold. Worse, **the 50% clause was dead code**: zero cells ever qualified under it,
because for a locally straight boundary a hexagon has >=50% of its area inside exactly
when its centre is inside. The 99% criterion is PROMPT.md's and was left untouched
(§2.2); the threshold Claude itself wrote in Phase 0 moved to 0.25 instead, and every
indicator now uses the clipped geometry so no cell can carry a neighbouring town's
values. Recorded as **D15, provisional**, with the full measured table, and raised as
QUESTIONS.md Q5 because the threshold is Samraj's judgement to confirm (§2.4).
**Limitation to carry into the model report:** 0.885% of Landhi, thin slivers along the
edge, is covered by no cell.
**Tests deliberately recompute rather than trust:** coverage, the inclusion rule, each
clipped area, and contiguity are all re-derived from the stored geometry, so a wrong
number in the file's own metadata fails the suite.
**Next:** P1-03 Download cache.

## 2026-09-26 — P1-03 Download cache
**What changed:** `pipeline/fetch.py` — streaming download with a `.part` file and an
atomic rename, sha256 computed while streaming, exponential backoff capped at 120 s,
`Retry-After` honoured, and `data/raw/manifest.json` recording url, sha256, bytes, date
and licence for every file. `pipeline/overpass.py` now registers its cached responses in
the same manifest, so the manifest accounts for every byte downloaded. Added
`tests/test_fetch.py`, 17 tests, all on a mocked transport with SYNTHETIC payloads.
**Evidence:** a second `uv run python -m pipeline.boundary` printed the same
"Area: 25.370 km2" with no download line; `uv run python -m pipeline.fetch --verify` ->
"Verified 1 cached file(s): all match the manifest". `uv run pytest` -> 68 passed.
`check.py --quick` -> `CHECK: PASS (3 checks)`.
**Latent Phase 0 bug found and fixed:** `data/raw/.gitignore` contained a bare `*`,
which overrides the root negation, so `data/raw/manifest.json` **would never have been
committable** — the provenance record PROMPT.md §6 requires would have stayed on this
laptop only. The nested ignore file now reads `*`, `!.gitignore`, `!manifest.json`, and
`git check-ignore` confirms the manifest is tracked.
**An honest limit on what a hash proves:** re-downloading the same Overpass query
produced a different sha256 while the geometry stayed byte-identical, because Overpass
embeds a timestamp in every response. The boundary file now carries
`raw_response_sha256_note` saying so explicitly: that hash fingerprints one download, it
is not a content hash of the geometry, and reproducibility is checked by re-measuring
the area (25.370 km2 both times) rather than by comparing hashes.
**Design choice:** the cache is trusted only when the file on disk still hashes to what
the manifest says. A truncated, edited or unmanifested file is re-downloaded rather than
silently used — tested both ways.
**A test corrected, not loosened:** `test_verify_cache_detects_tampering` asserted
exactly one problem; tampering correctly reports two (hash *and* size). The assertion
was tightened to require both rather than relaxed to accept either.
**Next:** P1-04 Daytime heat per cell.

## 2026-09-26 — P1-04 split into P1-04a and P1-04b; P1-04a Hot-season LST composite
**Why split:** P1-04 covered scene search, windowed reads, cloud masking, scaling,
compositing, zonal statistics and a map. That is two features, so it was split per the
loop protocol: P1-04a builds the composite, P1-04b turns it into per-cell values.
**What changed:** `config/heat.yaml` (season, cloud limit, QA bits, USGS scaling,
plausible range, minimum clear looks — every parameter auditable), `pipeline/lst.py`,
`tests/test_lst.py` (20 tests). `scripts/check.py` now validates the sixth config file.
**Evidence:** `uv run python -m pipeline.lst` -> 48 scenes, April–June 2022–2026, all
WRS 152/043. Composite 278x244 px at 30 m. Clear looks per pixel: min 33, median 42,
max 47; 0 of 67,832 pixels dropped. "LST degC: min 31.25, median 43.16, max 48.11",
inside the documented 20–65 range. `uv run pytest` -> 88 passed;
`CI=true pytest -m "not raw"` -> 84 passed, 4 deselected. `check.py --quick` ->
`CHECK: PASS (3 checks)`.
**The `raw` split is now real, and defined once (§10):** the composite GeoTIFF is
gitignored and rebuildable, so the 4 tests that open it are marked `raw` and run locally
only. The 84 tests CI runs include every unit test of the masking and scaling logic, so
the split hides no failure — it only defers tests whose input CI does not have.
**Tests check the bit order against Landsat's documentation, not against our code:** each
of bits 0–4 is asserted to carry the name config claims (fill, dilated cloud, cirrus,
cloud, cloud shadow), and bits 6+ (confidence levels, not defects) are asserted *not* to
mask, since masking them would throw away good data.
**Licence discrepancy recorded rather than glossed:** the Planetary Computer STAC
collection reports `license: proprietary`, which is the catalogue's generic placeholder.
USGS Landsat Collection 2 data is US public domain with no restrictions. Both facts are
in data/SOURCES.md so nobody has to rediscover the contradiction.
**Next:** P1-04b Daytime heat per cell.
