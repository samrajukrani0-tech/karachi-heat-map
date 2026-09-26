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

## 2026-09-26 — P1-04b Daytime heat per cell
**What changed:** `pipeline/zonal.py`, a shared zonal-statistics helper that every raster
indicator will use, and `pipeline/heat.py` (P1-04b). Added `tests/test_zonal.py` (7) and
`tests/test_heat_cells.py` (9).
**Evidence:** `uv run python -m pipeline.heat` -> "Cells: 265; with values: 265;
flagged: 0". Mean LST per cell 39.19–46.28 degC (median 43.23, spread 7.09); P90 per cell
40.21–47.29; pixels per cell min 27, median 113. All inside the documented 20–65 range.
Wrote `data/processed/lst_cells.csv` (11 kB) and `artifacts/lst_cells_map.png`, viewed:
spatially coherent, with a cool band on the north-west edge and hot patches in the
south-centre — structure, not noise, which is the sanity check a real LST field should
pass.
**D15 is enforced in code, not in a comment.** `pipeline/zonal.py` takes the clipped cell
and a test proves clipping changes the answer: on a SYNTHETIC raster whose left half is
10 and right half 30, the whole polygon means 20 and the clipped left half means 10. Any
future indicator that forgets to clip will fail that test's intent rather than quietly
importing Korangi's values.
**A sub-pixel cell falls back rather than vanishing.** The smallest clipped edge cell
holds 27 pixels, but the helper handles the general case: if no pixel centre lies inside
a cell it retries with `all_touched=True` and records `all_touched_fallback`, so a tiny
cell is reported honestly rather than as missing data.
**Caught before it could stand as false evidence:** P1-04b was marked passing and the
gate then failed on ruff (an unused import in a new test). The evidence string claimed
"CHECK: PASS", so it was fixed and re-verified in the same turn before the commit —
104 passed, CHECK: PASS (3 checks). A feature only passes when its checks passed in the
same turn (§2.3).
**Observation logged for P1-08:** the five coolest cells cluster at 24.858–24.862 N,
67.159–67.178 E with normal clear-look counts (41–43), so the cool band is signal, not a
masking failure. Green cover should explain it; if it does not, that is worth chasing.
**Next:** P1-06 People per cell.

## 2026-09-26 — P1-06 People per cell
**What changed:** `pipeline/hdx.py` (fetch one member from a remote zip by HTTP range),
`pipeline/population.py`, `config/population.yaml`, `zonal.sum_by_cell`,
`tests/test_population.py` (9 tests). `check.py` validates a seventh config file.
**Evidence:** Meta 295,132 people (median 119 px/cell); WorldPop 308,105 (median 13
px/cell); per-cell Spearman rho 0.834. Source chosen: Meta, on resolution (D16). Density
min 0, median 6,366, max 48,332 per km2. Map viewed: dense core through the centre-south,
21 empty cells, and the dense band coincides with the hot patches from P1-04b.
`uv run pytest` -> 113 passed (109 in CI, 4 raw deselected); `check.py --quick` ->
`CHECK: PASS (3 checks)`.
**548 MB avoided.** The Meta layer ships as a ~549 MB zip of India and Pakistan, but it
holds 13 separate 10-degree tiles and Karachi is in one of them. `pipeline/hdx.py` reads
the zip's central directory from the tail of the remote file, then range-fetches just
that member: **18.4 MB instead of 549 MB**, a 30x saving, and the same principle as
reading a raster in windows (§2.8).
**HDX rate limiting handled properly.** HDX answers a burst of API calls with `202
Accepted` and an empty body rather than an error, which a naive client sees as a JSON
parse failure. `hdx.dataset()` now treats that as "slow down": backs off up to 90 s, and
caches the metadata so a rebuild asks once rather than once per layer.
**Counts are summed so that totals conserve.** Masking each cell separately would
double-count any pixel straddling a shared edge. `zonal.sum_by_cell` rasterises the cells
instead, giving every pixel exactly one owner.
**THE FINDING OF THIS TURN — a 2.3x population undercount.** The 2023 census puts Landhi
Town at 681,293. Both models say about 300,000. Rather than assume the cause, both
rasters were summed over the whole of Korangi District: 1.81M and 1.93M against a census
3.13M. The shortfall is systematic across the district, so the pilot boundary is fine and
the models undercount — probably because both predate the 2023 census and both infer
population from building footprint area, which understates multi-storey and dense
informal housing. Recorded as **D16** with the consequences spelt out, and raised as
**Q6**. The data was **not** rescaled to match the census (§2.1), and a test asserts that
it was not.
**Why the index probably survives it, and where it does not.** Priority ranks cells
within Landhi and normalisation is relative, so a uniform factor cancels exactly. But the
undercount is *not* uniform — Landhi (0.44) is worse than the district (0.58) — which
hints the densest informal areas are undercounted most, under-ranking exactly the places
that most need support. And D8's need definition inherits the undercount, so absolute
supply quantities are underestimates: a centre planning water for 300,000 in a town of
681,000 under-supplies by more than half.
**Next:** P1-07 Age groups.

## 2026-09-26 — P1-07 Age groups
**What changed:** `pipeline/demographics.py`, age-layer config and the zero-population
rule in `config/population.yaml`, `tests/test_demographics.py` (9 tests). Two more Meta
tiles fetched by the same range-request route (18.5 MB each rather than 549 MB each).
**Evidence:** 265 cells; shares defined 244; undefined 21. share_over60 0.0447–0.0620,
share_under5 0.0909–0.1097, all within [0,1]. Elderly 17,084 (5.8%), under-5 28,148
(9.5%). `uv run pytest` -> 122 passed (118 in CI); `check.py --quick` -> `CHECK: PASS (3 checks)`.
**Zero-population rule, as specified and tested:** a share is a ratio, so with no
residents it is **undefined** — written empty and flagged `no_population` — never 0, and
never imputed from neighbours, which would invent data. Treating it as 0 in the index is
safe rather than arbitrary, because Exposure is deliberately unfloored (D6b), so such a
cell already has Priority 0 whatever its Vulnerability.
**THE FINDING — two of the six vulnerability indicators carry no signal.** The shares
looked suspiciously narrow, so they were measured rather than accepted:
- correlation between `share_over60` and `share_under5`: **exactly −1.0000**
- 86% of cells sit on just two values
- their sum spans 0.15291–0.15441, a range of 0.0015, CV **0.0045** (LST 0.028,
  population 0.994)
Meta applies an administrative-unit age profile to the population raster; Landhi spans
two such zones, so the two shares are one binary variable with opposite signs. Both have
direction +1 and would sit in the same weighted mean, so they would largely cancel while
consuming two of six weights and diluting the four indicators that do carry information.
A combined dependency ratio does not help, because the sum is the constant thing.
**Same failure mode as D4's dropped indicators, but only findable by measurement.** Night
LST and RWI were dropped because their resolution was visibly too coarse. This one looks
fine on paper — 31 m data — and only betrays itself in the numbers.
**What survives:** only the shares are uninformative. The **counts** vary with population
and are exactly what D8's need definition uses, so Phase 4 is unaffected. They are
written to `age_cells.csv` and retained.
**Recorded as D17 (provisional) and Q7.** Dropping a D4-approved indicator is Samraj's
call. P1-07 itself passes: it produced the shares in [0,1] with the zero rule implemented
and tested, exactly as specified.
**Tests pin the finding:** assertions require the anti-correlation to stay below −0.99
and the combined ratio's CV below 0.02, so if a future Meta release fixes this, the suite
fails and D17 gets revisited rather than silently outliving its evidence.
**Next:** P1-08 Built environment.

## 2026-09-26 — P1-08 Built environment
**What changed:** `config/landcover.yaml`, `pipeline/landcover.py`,
`tests/test_landcover.py` (9 tests). `check.py` validates an eighth config file.
**Evidence:** ESA WorldCover 10 m 2021 v200, median 1,314 px/cell. built_fraction median
0.692 (0.000–0.991); green_fraction median 0.131 (0.000–1.000). `uv run pytest` -> 131 passed (127 in CI); `check.py --quick` -> `CHECK: PASS (3 checks)`. Map viewed: the built
and green panels are near-complements, matching the measured r = −0.929.
**Source substitution, recorded as D18 (provisional).** Microsoft Building Footprints is
on the Planetary Computer and covers Pakistan, but its asset is an `abfs://` Azure path
needing `adlfs` -> `azure-storage-blob` -> `cryptography`, and cryptography ships no
x86_64 macOS wheel — it tries to build from source with Rust. That is the third time this
Intel Mac has been abandoned by current wheels (after h3 4.4). Installing Rust is a
system-wide install (§2.7), and pinning a security library backwards to read a building
dataset is a poor trade, so ESA WorldCover is used for both indicators. The quantity is
*built-up surface* (includes roads and paving), not building footprints, and is named
that way so the report cannot overclaim.
**Cross-validation that was not planned.** P1-04b flagged five unexplained cool cells for
P1-08 to check. They are **93–100% green** against a pilot median of 13.1%. Landsat
thermal infrared and ESA land classification are independent datasets measured in
different years, and they agree on where Landhi's vegetation is. The open question from
P1-04b is closed with evidence rather than assertion.
**A number that reframes the Phase 0 relief-centre finding.** OSM building polygons cover
6.01% of Landhi against WorldCover's 54.7% built-up — about 11% as much, from 711 mapped
buildings. So OSM listing no Edhi or Saylani facility in Landhi is **not evidence they do
not exist**; it is evidence that OSM barely describes Landhi at all. Recorded prominently
in data/SOURCES.md, and P1-09 must carry the same caveat.
**New question Q8.** With Vulnerability down to four indicators after D17, two of them —
`built_fraction` and `lack_green` — correlate at about +0.93, because WorldCover gives
each pixel one class so built and green are near-complements. Recommendation: drop
`built_fraction`, keep `lack_green`, because built-up surface is a *cause* of the high
land surface temperature that Hazard already measures directly, so keeping it would count
the same physical fact twice.
**Next:** P1-09 Access, which will split into P1-09a and P1-09b.

## 2026-09-26 — P1-09 split; P1-09a Distance to nearest health facility
**Why split:** P1-09b needs a relief centre verified in person (Q2) and has no open-data
fallback, so it would have blocked the health-facility indicator too. Split per the Phase
1 instruction: P1-09a unblocked, P1-09b blocked on Samraj.
**What changed:** `config/access.yaml`, `pipeline/access.py`, `tests/test_access.py`
(8 tests). `check.py` validates a ninth config file.
**Evidence:** 228 OSM health facilities within 6 km (32 inside Landhi, 196 outside).
Distance min 14 m, median 849 m, max 2,471 m, inside the documented limits.
`uv run pytest` -> 139 passed (135 in CI); `check.py --quick` -> `CHECK: PASS (3 checks)`.
Map viewed: facilities cluster along the central corridor; the worst-served cells are the
north-west band — the same cells P1-08 found greenest and P1-04b coolest, which is a
coherent picture rather than a contradiction.
**The search buffer earned its place, measurably.** 42 of 265 cells have their nearest
facility outside Landhi. Without the 6 km buffer those cells would have been scored as
far from care purely because a clinic sits over an administrative boundary. That is a
measured justification, not an assumption.
**Bias direction stated, not just the caveat.** OSM maps about 11% of Landhi's built area
(D18), so unmapped clinics almost certainly exist. Every missing facility can only make
the true distance *shorter*, so this indicator **overstates** isolation from care — the
opposite direction to the population undercount (D16), which understates exposure. The
two do not cancel: they act on different dimensions, and both belong in the model report.
**Straight line x 1.3 rather than a routable graph:** §6 permits either. A routable graph
needs osmnx and networkx and would refine an estimate whose dominant error is OSM's
coverage, not the circuity approximation. Logged as a v2 refinement in data/SOURCES.md.
**Next:** P1-10 Load-shedding feasibility. P1-09b stays blocked on Q2.

## 2026-09-26 — P1-10 Load-shedding feasibility (study written; decision blocked on Samraj)
**What changed:** `docs/load-shedding-feasibility.md` (97 lines), K-Electric schedule PDF
cached and manifested at `data/raw/kelectric/`, `pypdf` added to read it.
**What was found — the data exists and varies:** the published schedule has **620 feeder
rows** across **58 grid stations**, **26 on the LANDHI grid**, with daily outage from
**4.0 to 10.0 hours, median 7.5**. That is a 6-hour spread, large enough that it might
matter more than several indicators that are in the model.
**Why it still cannot be built.** The schedule gives a feeder name and a grid station —
no coordinates, no boundaries, no street lists. K-Electric's own route from place to
feeder is a 13-digit account number in their app, which cannot be run for 265 cells. Many
feeder names are businesses or bare codes (`ZAFAR ICE`, `ROTI PLANT`, `36 B RMU`,
`NOOR BHAI`). And even with every feeder located as a point, spreading 26 feeders across
265 cells would mean **inventing a service boundary K-Electric has not published** — which
§2.1 forbids. The document found is also the **Ramadan 2026** schedule, not April–June.
**A security line not crossed:** `ke.com.pk` resolves but presents a **self-signed
certificate**, so TLS verification fails and plain HTTP times out. Disabling certificate
verification to scrape a utility's site is not something this project will do, so there
is no reproducible automated source either.
**Read the primary document rather than a summary.** A bill-help website described the
structure second-hand; the PDF was fetched, cached, manifested and parsed directly, which
is how the 620/58/26 counts and the 4–10 hour range were obtained.
**Recommendation (Q9):** approve dropping the indicator for v1, and say plainly in the
model report that **the mechanism Edhi actually named is the one this model cannot see.**
**The v2 route is fieldwork, not scraping:** feeder names printed on 10–15 K-Electric
bills from different parts of Landhi would tie feeder names to real addresses — exactly
the link the published schedule omits.
**Status:** P1-10 blocked on Samraj (Q9); the acceptance criterion requires his decision
either way.
**Next:** P1-11 Indicator table. Note it depends on P1-09b, which is blocked on Q2, so it
will be built with the indicators available and the gap documented.

## 2026-09-26 — P1-11 Indicator table
**What changed:** `pipeline/indicators.py`, `docs/data-dictionary.md` (generated),
`tests/test_indicators_table.py` (10 tests).
**Evidence:** 265 cells, 14 columns, 4 of 5 configured indicators present.
`data/processed/indicators.parquet` (29 kB) and `indicators.csv` (26 kB); data/processed
totals 304 kB against the 5 MB budget. `uv run pytest` -> 149 passed (145 in CI);
`check.py --quick` -> `CHECK: PASS (3 checks)`.
**A dependency handled honestly rather than by stalling.** P1-11 depended on P1-09b,
which is blocked on Q2 with no open-data fallback. Rather than halt the phase, the table
was built with the four available indicators and `dist_centre_m` carried as an explicitly
empty column. This is within the feature's own acceptance, which requires a
**missing-value summary** — precisely the mechanism for a documented gap. Two acceptance
criteria were **added** (never removed): that the gap is named explicitly, and that the
table is rebuilt once P1-09b unblocks. `depends_on` was changed from P1-09b to P1-09a and
the change recorded here so it is visible rather than quiet.
**The QA figure earned its place.** Reading it changed what Phase 2 should check:
- `lst_mean_c` is roughly normal around 43.2 — nothing to worry about.
- `population` is heavily right-skewed with a spike at zero, which is exactly why D4
  specified a `log1p` transform.
- **`lack_green` is strongly bimodal**, with masses near 0 and near 1 and little between.
  It behaves closer to a binary "green or not" than a gradient, so robust min–max
  clipping at the 5th/95th percentile will behave differently on it than on a normal
  variable. Flagged for P2-01 rather than discovered later.
**Tests check the join, not just the output.** One test compares every value back against
its source layer, so a merge that silently reordered rows would fail. Another asserts the
data dictionary states the known biases — not air temperature, population undercount,
distance overstated, D16/D17/D20 — so a reader does not have to dig through DECISIONS.md
to learn the numbers are biased.
**Next:** Phase 1 is complete except P1-09b, which is blocked on Samraj.

## 2026-09-26 — P2-01 Normalisation
**What changed:** `pipeline/normalise.py` (both D5 methods), `tests/test_normalise.py`
(32 tests), `data/processed/indicators_normalised.csv`.
**Evidence:** all four available indicators normalise into [0,1] under both methods;
Spearman rho 0.9999 between methods per indicator. `uv run pytest` -> 181 passed (177 in CI);
`check.py --quick` -> `CHECK: PASS (3 checks)`.

### Checker subagent verdict (PROMPT.md §3.1) — AGREES
A fresh subagent was given the written specification and the data, but **not** the
implementation or any expected answers, and asked to re-derive three spot values. It
computed **18 numbers** (3 cells × 3 columns × 2 methods) and **all 18 matched to six
decimal places**. Verified in-turn by comparison against the implementation.

**Four improvements from its critique, applied and pinned by tests:**
1. **The constant test is now relative to magnitude**, not an absolute 1e-12. An absolute
   tolerance misjudges columns far from 1.0.
2. **A flat core with live tails now warns** (`FlatCoreWarning`) instead of silently
   returning zeros. A column can be constant between the 5th and 95th percentiles while
   varying in the tails; robust min–max would discard that variation without saying so.
3. **The direction flip is documented and tested as NOT applying to the constant case.**
   The checker found the written rule genuinely ambiguous: read as steps-in-order, a
   constant indicator with direction −1 gives 1 − 0 = 1 — *maximum risk in every cell*.
   The short-circuit reading is now pinned by a test.
4. **`log1p` is documented and tested as rank-invariant**, so a future non-monotone
   transform cannot silently change the percentile-rank branch.

**A real finding about our own data, confirmed independently.** `population`'s 5th
percentile is **exactly 0.000000**, because 21 cells hold no people. So **not one cell is
clipped at the bottom** while 14 are clipped at the top — "robust" min–max is one-sided in
practice on this indicator. Assessed: this is harmless here rather than a defect. The 21
zero-population cells map to exactly 0, which is what D6b wants, since Exposure is
deliberately unfloored so those cells get Priority 0 regardless. But the name implies
symmetric trimming, so it belongs in the model report.

**Two disagreements recorded rather than silently accepted:**
- The checker argued a constant indicator should be **dropped with weights renormalised**,
  not mapped to 0, because 0 drags every composite down by that indicator's full weight
  and because a constant column is usually a symptom of an upstream bug. That is a good
  argument, but **PROMPT.md §7 explicitly specifies "becomes 0, with a warning"**, and
  §2.2 forbids changing a criterion without Samraj. Noted for the model report; currently
  moot, as no indicator is constant. Its force is also reduced by D21: we publish ranks
  and shares, and the rule is rank-neutral either way.
- It suggested masking zero-population cells out of the ranking entirely. **Already
  handled by D6b**: Exposure is unfloored, so those cells score Priority 0 by construction
  rather than by exclusion.

**Carried forward to P2-04.** The checker measured that swapping normalisation method
reorders **4,048 of 34,980 cell pairs** in an equal-weight composite (Spearman 0.926).
Within a single indicator the methods cannot invert order — both are monotone — but the
composite is a sum of differently-*spaced* components, and spacing changes rank. That is
exactly what the sensitivity analysis must quantify, and it is now a concrete target
rather than a vague intention.
**Next:** P2-02 AHP tool.
