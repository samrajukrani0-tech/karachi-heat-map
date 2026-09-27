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

## 2026-09-26 — P2-02 AHP tool
**What changed:** `pipeline/ahp.py` (eigenvector by power iteration, CI/CR, conflict
detection, interactive session, `--dry-run`), `tests/test_ahp.py` (34 tests).
**Evidence:** demonstrated live in the terminal —
`printf 'a\n3\na\n5\na\n3\n' | uv run python -m pipeline.ahp --dry-run` ->
lambda_max 3.038511, CI 0.019256, CR 0.0332, kappa 1.8, weights lack_green 0.6370 /
dist_health 0.2583 / dist_centre 0.1047. `config/weights.yaml` still reads
`provisional: True, decided_by: None`, so **no judgement of Samraj's has been
fabricated** — P2-02b remains genuinely blocked on him.
`uv run pytest` -> 215 passed (211 in CI); `check.py --quick` -> `CHECK: PASS (3 checks)`.
**A `--dry-run` flag was added** so he can practise the tool before it counts.

### Checker subagent verdict (PROMPT.md §3.1) — AGREES
Given the specification and three matrices but not the implementation, it re-derived all
three independently by four cross-checking routes (LAPACK, power iteration, exact
characteristic polynomial, and Collatz–Wielandt bracketing) and **all three agreed
exactly**: M1 λmax = 3.038511090558; M2 λmax = **6.2 exactly** (circulant, so the common
row sum); M3 λmax = **4 exactly** (perfectly consistent).

**Six improvements applied and pinned by tests:**
1. **Graduated CR threshold** — Saaty published 0.05 for n = 3, not a flat 0.10, and our
   case is n = 3. Recorded as **D22 (provisional)** and **Q10**; a tightening, never a
   loosening.
2. **κ is now reported.** For a 3×3, λmax, CI and CR are all functions of
   κ = a₀₁·a₁₂/a₀₂ alone — it *is* the inconsistency, and it is far more interpretable.
3. **CI clamped at 0.** λmax ≥ n is a theorem, but floating point returns
   3.9999999999999996 for a consistent 4×4, which would print "CR = -0.0000".
4. **Collatz–Wielandt bracket** reported as a certified convergence diagnostic — honest
   evidence, unlike an iteration count.
5. **Input validation** for positivity, unit diagonal and exact reciprocity. Someone
   typing 0.33 for 1/3 would manufacture inconsistency that was never in the judgements.
6. **A sharp regression test:** at n = 3 the eigenvector equals the row geometric mean,
   which catches sign, normalisation and eigenvalue-selection bugs at once. A second test
   documents that this coincidence **fails from n = 4**, so nobody assumes it survives if
   indicators are added back.

**It also confirmed and proved the n = 3 finding this feature had already hit.** A 3×3
reciprocal matrix has trace 3 and zero principal 2×2 minors, so its characteristic
polynomial collapses to λ³ − 3λ² − det = 0 with det = (√κ − 1/√κ)². In log space the
three residuals are exactly +d/3, +d/3, −d/3 — identical in magnitude. So inconsistency
at n = 3 is one degree of freedom shared equally, and **no single answer can be blamed**,
which is what the tool now tells the user.

**A consequence worth carrying to the model report:** the three equally-consistent
repairs of M1 give the third item a weight anywhere from **0.077 to 0.130** — a factor of
1.7. "Inconsistency is small and unattributable" must not be read as "the weights are
pinned down".

**Points recorded for P2-06 (the model report), citations to be verified first.** The
checker explicitly said it was working from recall and asked that its references be
checked before publication, so they are recorded as arguments to verify, not as facts:
right–left asymmetry of the eigenvector method (we are immune at n = 3); rank reversal
when the item set changes; the bounded 1–9 scale forcing some inconsistency; disputed
RI(3) values (0.58 vs ≈0.5245, which would move our CR from 0.0332 to 0.0367);
consistency is not validity; weights are not influence, since realised influence depends
on each indicator's spread after scaling; and group judgements must be aggregated by
**geometric** mean, which matters for D7b's planned re-run with a field coordinator.
**Next:** P2-03 Scores.

## 2026-09-26 — P2-03 Scores
**What changed:** `pipeline/score.py`, `tests/test_score.py` (24 tests),
`data/processed/scores.csv` and `scores_weights_used.json`.
**Evidence:** hazard min 0.0100 (floored) / exposure min 0.0000 (unfloored, D6b) /
vulnerability min 0.1344; Priority min 0, median 0.6157, max 0.8529; Intensity median
0.5345 with 21 undefined. 21 cells score Priority exactly 0, matching the 21 with no
residents — D6b behaving exactly as designed. `uv run pytest` -> 239 passed;
`check.py --quick` -> `CHECK: PASS (3 checks)`.
**The missing indicator is handled out loud.** `dist_centre` has no data, so an
`IncompleteDimensionWarning` fires, the surviving vulnerability weights are renormalised
to 0.5/0.5, the weights actually used are published in `scores_weights_used.json`, and
every row carries `model_incomplete` and `weights_provisional`. Nothing can present these
scores as final.
**A real bug caught by testing the output rather than the code.** Six populated cells sit
below the pilot median on *every* indicator, so "the indicators that push this cell above
the median" was an empty list and the site would have rendered a blank "why" panel. They
now say "Below the Landhi average on every measure we track" — a correct answer, properly
presented.

### Checker subagent verdict (PROMPT.md §3.1) — AGREES on the arithmetic, disagrees on the formulation
Given the spec and the raw table but neither the implementation nor the output, it
re-derived three cells end to end and **all three matched to six decimal places**. It then
made five empirical claims, and **all five were independently verified here**:

| claim | verified |
|---|---|
| The vulnerability floor never binds | min V = 0.1344 vs a floor of 0.01 — **dead code** |
| 31% of cells are tied at a clipped extreme | 81 of 265 |
| Intensity scores empty cells highly | up to 0.7402, best rank **24 of 265** |
| LST is rank-uncorrelated with everything | Spearman +0.048 green, +0.004 built, −0.005 population |
| Zero-imputation would be rank-identical | it is a constant factor, so ranking is unchanged |

**One fix applied: Intensity is now undefined where nobody lives.** "How bad is it for a
person here" has no answer when there is no person here.

**Two things recorded for Samraj rather than decided here:**
- **Q11.** PROMPT.md calls Intensity "the per-person view". It contains no population
  term — it is *exposure-blind*, which is not the same thing. Recommended: keep the
  formula, correct the description to something like "Severity".
- **Q12 — a correction to something Claude told Samraj.** D19's second reason for dropping
  `built_fraction` was that built-up surface causes the LST that Hazard already measures.
  Measured, `lst_mean_c` vs `built_fraction` is Spearman **+0.004**. There was no
  double-counting to prevent. D19 still stands on its first reason (0.93 redundancy with
  `lack_green`), but he decided partly on a claim the data does not support, and he has
  been told.

**A finding for the model report.** Vegetation buys Landhi very little: cells ≥90% green
average **42.48 °C** against **43.31 °C** for cells under 10% green — a gap of **0.83 °C**.
The relationship flips sign between the green minority (−0.275) and the built majority
(+0.382), which is why the overall correlation is ≈ 0. The hazard layer's 7 °C spread is
real and spatially coherent, but it is **not** explained by land cover, so the report must
not imply the textbook urban-heat-island story.
**A silver lining in the same finding:** the three dimensions are near-independent, so
each contributes information rather than repeating the others. That is good index design —
and it also means no dimension dominates, so the ranking is sensitive to the weights,
which P2-04 must quantify.
**Next:** P2-04 Sensitivity.

## 2026-09-27 — P2-04 Sensitivity
**What changed:** `pipeline/sensitivity.py`, `tests/test_sensitivity.py` (13 tests),
`data/processed/confidence.csv`, `artifacts/sensitivity.png`. Plus a bug fix recorded as
**D23** and a new question **Q13**.
**Evidence:** 1000 seeded draws (seed 20260926), α = 50, methods run separately then
pooled. Rank interval width median 53, max 182; priority interval width median 0.193.
Monte Carlo SE on P at most 0.016. `uv run pytest` -> 252 passed; `check.py --quick` ->
`CHECK: PASS (3 checks)`. The reproducibility test re-runs the whole analysis and asserts
the committed output is reproduced byte for byte.

### The headline finding, and it is not comfortable
**Of the 53 cells in the published top 20%, only 28 stay there in at least 80% of draws,
and 12 are on the wrong side of a coin flip.** Roughly half the priority list does not
survive reasonable variation in the weights and the normalisation method. The top handful
and the bottom are stable; the middle is not. For a triage tool that is the right shape —
you act on the top — but it must be stated plainly rather than buried.

### Checker subagent verdict (PROMPT.md §3.1) — AGREES on every headline number
It built its own implementation from the specification, with its own seeds, and got:

| quantity | checker | mine |
|---|---|---|
| stability split | 27 / 49 / 189 | 28 / 48 / 189 (after its bug fix) |
| mean \|P_robust − P_percentile\| | 0.145 | 0.144 |
| cells where methods differ by > 0.5 | 36 | **36** |
| of 53 top cells, below a coin flip | 12 | **12** |
| the three spot cells | within MC error | within MC error |

**It found a real bug, fixed as D23.** D6b guarantees an empty cell scores Priority 0
because Exposure is unfloored. That held under robust min–max only: under percentile rank
the 21 empty cells share the minimum rank, whose average maps to **0.0379**, so they got
non-zero Priority and 21 distinct ranks. **Half the sensitivity draws were violating a
design invariant**, and those cells' published rank intervals were an artefact.
`population` is now declared `structural_zero: true` in config, and a raw count of zero
normalises to exactly zero under any method. Verified before and after.

**Three further findings applied:**
1. **The method swap and the weight jitter were confounded.** Pooled, they produce
   *bimodal* rank distributions whose median lands in the trough — a value no draw
   favours. The two arms are now run separately and reported separately. They are not a
   detail: mean |P_robust − P_percentile| is 0.144, and 36 cells disagree by more than 0.5.
2. **Four-decimal P overstated precision by roughly 300×.** At p ≈ 0.6 with 1000 draws the
   standard error is 0.016. P is now reported to 2 dp with its standard error, and the
   classification is computed from the published rounded number so a reader checking
   "0.80 → high" finds it true.
3. **Rank is the wrong primary object.** Rank is competitive — a cell moves when *other*
   cells move — and the priority curve is nearly flat mid-ranking. Priority intervals are
   now published alongside: median width 0.193 on a 0–0.85 scale, far better behaved than
   rank intervals of 6 to 182 places.

**Q13 raised.** §7's confidence classes, read literally against P(top 20%), label 215 of
265 cells "low confidence" — 155 of them with P below 0.01, i.e. cells the model is
*certain* about. Three columns are now published so nothing is hidden: `stability`
(confidently in 28 / uncertain 48 / confidently out 189), `confidence` (the §7 thresholds
against certainty), and `confidence_literal` (§7 read straight).

**Recorded for the model report, not acted on:** α = 50 implies a marginal SD of 0.066 on
each exponent, so this measures robustness to *small* perturbation, not to a genuinely
different weighting; the checker's sweep showed the count of stable cells falling from 49
at α = 500 to 11 at α ≈ 3. And the weights are still `provisional: true`, so the
uncertainty from "these are not yet Samraj's judgement" exceeds anything sampled here.
**Next:** P2-05 Validation pack.

## 2026-09-27 — P2-05 Validation pack
**What changed:** `pipeline/validate.py`, `tests/test_validate.py` (23 tests),
`docs/expert-ranking-form.md`, `data/processed/validation.json`.
**Evidence:** `uv run pytest` -> 275 passed; `check.py --quick` -> `CHECK: PASS`.

### The honest result
**(a)** The equal-weights baseline is *currently a tautology*: the configured weights ARE
equal weights while P2-02b is blocked, so ρ = 1.0 by construction. Reporting that as a
validation result would read as agreement between two methods. The JSON now declares it
**not applicable yet** and points at P2-04 as what answers the question meanwhile.
Informative substitutes are reported instead: hazard-led ρ 0.9570, exposure-led 0.9651,
vulnerability-led 0.9660.
**(b)** The one June 2024 incident reported inside Landhi resolves to four plausible
locations, ranking **106, 112, 156 and 160 of 245** — all mid-distribution, which is
exactly what a randomly drawn cell would give. Downgraded from D14's "weak evidence" to
**illustrative context only**: a single incident has no denominator, so it is neither
support nor refutation.
**(c)** The expert-ranking form is built from **12 real OpenStreetMap place nodes** inside
Landhi — not invented — plus 13 blank rows, because OSM maps only a small part of Landhi
(D18) and the list is certainly incomplete.

### Checker subagent verdict (§3.1) — AGREES, and improved six things
It re-derived the three spot ranks independently: **106, 156, 160 — exact match**. Its
bootstrap gave ρ 0.965035, τ 0.848485, percentile CI [0.8175, 1.0000] — all matching.

Applied:
1. **Ranks are quoted against 245 distinguishable positions, not 265 cells.** 21 empty
   cells tie at the bottom, so "of 265" implied resolution the model does not have.
2. **Quintile labels dropped** in favour of rank plus priority. Rank 106 was *exactly* the
   last cell of Q2 and 160 *exactly* the first of Q4, so "Q2 to Q4" implied a three-fifths
   spread when all three sit mid-table.
3. **Face validity downgraded to no evidentiary weight**, with the denominator argument
   written into the data.
4. **The equal-weights tautology is declared in the output**, not just mentioned in print.
5. **A permutation test was added.** "Better than chance" is a test, not an interval; at
   n = 12 the one-sided 5% critical value sits near ρ = 0.50.
6. **The Fisher SE corrected to Bonett–Wright** (√(1.06/(n−3)) rather than the Pearson
   1/√(n−3)), giving [0.8721, 0.9908] against the checker's [0.8720, 0.9908]. The Pearson
   SE was slightly too narrow — the wrong direction to be wrong in for a small-n exercise.

**A power limitation now stated on the form itself:** with 12 localities only very strong
agreement is detectable; about 25 are needed to tell a genuinely useful model from
guesswork. Field staff are asked to add places we have missed.
**Performance:** vectorising the bootstrap and permutation took the suite from 53 s to
2.5 s.
**Next:** P2-06 Model report.

## 2026-09-27 — P2-06 Model report
**What changed:** `docs/model-report.md` (175 lines), `tests/test_model_report.py` (12).
**Evidence:** `uv run pytest` -> 287 passed; `check.py --quick` -> `CHECK: PASS`.
**Generated from the committed outputs**, not retyped, so every figure traces to
`data/processed/`. Twelve tests re-read those outputs and assert the report still matches
— a report that goes stale fails the suite rather than quietly misreporting.
**It leads with the uncomfortable result**, not with the map: only 28 of the 53 top-20%
cells survive in 80% of draws, and 12 are on the wrong side of a coin flip. The
limitations sit in §3, *before* the results, and include the population undercount, the
load-shedding mechanism the model cannot see, the fact that surface temperature is
rank-uncorrelated with every other layer, the age-share collapse, and OSM's 6% coverage.
**One test corrected rather than loosened:** it first banned the word "dangerous"
outright, but PROMPT.md §1 itself says "circumstances that make heat more dangerous". It
now enforces the actual §2.5 rule — never call an *area* dangerous — by requiring the word
to reference heat.
**Phase 2 is now complete except P2-02b, which is blocked on Samraj running the AHP tool.**
**Next:** Phase 3, starting with P3-01 DESIGN.md.

## 2026-09-27 — P3-01 DESIGN.md
**What changed:** `DESIGN.md` (191 lines), `tests/test_design.py` (12 tests).
**Evidence:** `uv run pytest` -> 299 passed; `check.py --quick` -> `CHECK: PASS`.
**Written before any styling**, as §9 requires. Three project-specific principles, the
first being that **the uncertainty is part of the answer, not a disclaimer** — only 28 of
53 top cells survive the sensitivity analysis, so cells the model is unsure about must
*look* unsure. Hatching, not a tooltip.
**A colour claim was wrong and the colour was changed, not the claim.** The first draft
said `--muted #5C5952` gives 7.0:1 on the page background. Measured: **6.59:1**. The token
was darkened to `#58554E` (7.01:1). Every other value is now measured too: `--ink`
16.12:1, `--deep` 9.96:1, `--signal` 6.90:1.
**A constraint discovered by measuring:** ink on the deepest ramp step is only **1.62:1**,
so map cells can carry no text at all. That is now written into the design rather than
discovered during implementation.
**The ramp was verified, not assumed:** monotone in lightness (survives photocopying, which
field briefs get) and order-preserving under simulated deuteranopia, protanopia and
tritanopia.
**The avoid-list review forced two real revisions**, both recorded: the warm-cream-plus-
serif-display combination lost its serif, and the panel stopped being a rounded card with
a shadow.
**Status:** provisional until Samraj approves the plan.
**Next:** P3-02 Shell.

## 2026-09-27 — P3-02 Shell
**What changed:** `scripts/build_site_data.py`, `site/style.css`, six pages,
`package.json` + `.htmlvalidate.json` + `playwright.config.js`,
`tests/e2e/shell.spec.js` (44 tests across both viewports).
**Evidence:** `npx html-validate site` clean; `npx playwright test` 44 passed;
`check.py --quick` -> **`CHECK: PASS (6 checks)`** — up from 3, because html-validate,
Playwright and site-data consistency are now live.
**Two checks were fixed rather than left misleading.** `site-data consistency` globbed
`*.json` and so never matched `cells.geojson` — it silently reported N/A forever. It is
now a real check: every served cell must exist in the processed data with matching
priority, rank and temperature, the cell sets must be identical, and the provisional flags
must be present. And `axe-core` was **failing** with "no tests found" rather than
deferring; it now reports N/A until an axe-tagged test exists, and fails properly once one
does.
**I committed on a misread and had to correct it.** I read Playwright's "44 passed" and
missed "2 failed" printed above it, and pushed. The alignment test was failing because the
nav uses a negative margin, so its links' *boxes* start 12 px left of their *text* — the
test measured boxes. Fixed by measuring the text edge, which is what a reader actually
sees, and pushed immediately. The lesson is to read the gate's own verdict line rather
than the test runner's tail.
**Screenshots critiqued, as DESIGN.md requires, and two real faults fixed:**
1. The laptop view broke **DESIGN.md's own alignment rule** — nav at x=16, heading at
   x=305, two competing left edges where the rule says one. Header and footer now share
   main's column, and a test asserts all four edges agree within 2 px.
2. The phone nav consumed about 100 px before any content — space the map needs.
   Tightened without dropping below the 44 px tap target.
**One unnecessary element removed:** the footer said "Built by Samraj Lal Ukrani" and then
"fieldwork by Samraj Lal Ukrani" one sentence later.
**Next:** P3-03 Map and legend.

## 2026-09-27 — P3-03 Map and legend, P3-04 Layers and panel
**Evidence:** `npx playwright test` -> 83 passed, 1 skipped; `check.py --quick` ->
**`CHECK: PASS (7 checks)`** — axe-core is now live.
**A fault no test could have caught as written (P3-03).** CARTO's basemap tiles return
HTTP 200 with `naturalWidth > 0`, so "tiles actually load" passed — while serving
**"API KEY REQUIRED" watermarks**. §9 requires a basemap needing no key. Visible only by
looking at the screenshot. Measured at z=13 over Landhi: CARTO 2.0 kB / **16 distinct
colours**; Esri Light Gray Canvas 12.3 kB / 161; OSM standard 35.7 kB / 256. Switched to
Esri (**D24**), and the test now rasterises a tile to a canvas and requires > 40 distinct
colours, because "it is an image" was never the property that mattered.
**DESIGN.md principle 1 is now enforced in code.** Uncertain cells are **hatched**, not
tinted — a tint would read as "lower priority", a different claim — and a test asserts a
non-`none` `stroke-dasharray` on them.
**The panel cannot drift from the data:** a test reads `cells.geojson` directly and
compares the rendered rank, temperature and population against it.
**The caveats travel with the screenshot.** "What this cannot tell you" carries the
population undercount, the missing relief-centre indicator, LST not being air temperature,
and the absent power cuts — so a panel forwarded on WhatsApp still says what it cannot do.
**One unnecessary element removed:** "never a verdict on a neighbourhood" appeared three
times (panel, standalone paragraph, footer). The standalone paragraph is gone.
**Next:** P3-05 Confidence.

## 2026-09-27 — P3-05 Confidence
**Evidence:** `npx playwright test` -> 89 passed, 1 skipped; `check.py --quick` ->
`CHECK: PASS (7 checks)`.
**Q13 had to be resolved here, because the site cannot show two definitions.** §7's
classes read literally would print **"low confidence" on 215 of 265 cells**, 155 of them
with P below 0.01 — cells the model is *certain* about. On a page a coordinator acts from
that is not imprecise, it is false. The site therefore uses the directional three-way
call (**D25**): confidently a priority 28, uncertain 48, confidently not a priority 189.
All three columns stay in `confidence.csv`, so the choice is visible and reversible by
changing one mapping.
**The middle band is the product.** The Confidence layer carries a note saying so — those
48 cells are the ones worth a human's attention, and the literal scheme buried them among
214 others.
**A test that checks wording against data:** for both a "confidently in" and a
"confidently out" cell it asserts the panel states the right label and the exact rank
interval from the file, so the prose cannot drift from the numbers.
**Next:** P3-06 Content pages.

## 2026-09-27 — P3-06 Content pages
**Evidence:** `npx playwright test` -> 107 passed, 1 skipped; `check.py --quick` ->
`CHECK: PASS (7 checks)`.
**Generated from the committed data**, so the figures on the site cannot drift from the
model. How it works explains the three questions, why the model multiplies rather than
adds, and how sure it is — with the maths section deliberately placed *after* the plain
explanation, which a test asserts by checking the order.
**The uncomfortable numbers are on the public site, not just in the report:** 28 of 53
top areas survive, 12 fail a coin flip, the population count is roughly half the census
figure, and power cuts are absent.
**Three decisions are now enforced by tests on the live pages:** no page names the school
(D11b), About shows no email or contact channel of any kind (D11c), and no page calls an
area unsafe or dangerous (§2.5).
**Next:** P3-08 Quality gates, then P3-09 Deploy. (P3-07 and P3-07b are dropped by D9.)

## 2026-09-27 — P3-08 Quality gates
**Evidence:** `check.py --lighthouse` -> **`CHECK: PASS (8 checks)`**; Lighthouse
performance 91, accessibility 100, best practices 96, SEO 100. All eight §10 gates are now
live.
**Performance started at 79 against a floor of 85, and the floor was not moved.** Three
genuine faults were fixed instead, 79 → 84 → 86 → 91:
1. **A 404 from a missing favicon.** Notable because the Playwright console test passed
   while Lighthouse's console-errors audit failed — the favicon request happens outside
   the page's own script, so the page-level listener never saw it.
2. **A 0.165 layout shift** caused by the provisional banner being revealed by JavaScript
   after load.
3. **`leaflet.css` blocking the critical path**, now loaded non-blocking with a
   `<noscript>` fallback.
**The layout-shift fix improved the site's honesty, not just its score.** The provisional
banner is now rendered visible in the HTML and is only ever *removed* by JavaScript — so
the honest state no longer depends on a script running. A test loads the page with
JavaScript disabled and asserts the banner is still there.
**Two budget tests added:** first load excluding basemap tiles is well under 1.5 MB, and
the site makes no third-party request except the basemap, because Leaflet is vendored.
**Next:** P3-09 Deploy.

## P3-09 Deploy — PASS

GitHub Pages deploys from CI, and the live site is up at
<https://samrajukrani0-tech.github.io/karachi-heat-map>. All six pages,
`data/cells.geojson` and the vendored Leaflet return HTTP 200.

**The smoke suite against the live URL nearly went into features.json as a pass on a
misreading — the same mistake as P3-02.** The first live run printed `12 passed (6.2m)`
with two bare test names above it and no counters. Twelve of a 113-test suite is not a
result worth trusting, and 6.2 minutes for twelve tests is a timeout signature, not a
fast run.

The cause was URL joining. With `baseURL` set to the Pages project URL
`https://…github.io/karachi-heat-map`, a test path written as `/index.html` resolves
against the **domain root**, because a leading slash discards the path. Every live
navigation was requesting `https://samrajukrani0-tech.github.io/index.html` — someone
else's 404 page. Locally the bug was invisible: the dev server *is* the domain root,
so `/index.html` happened to be right.

Two changes fixed it: test paths are now relative (`index.html`), and the config
normalises `baseURL` to end in `/`, without which a relative path resolves against the
last path *segment* and drops `karachi-heat-map` anyway. A `@smoke` tag now marks the
subset worth running over the network — page loads, cell rendering, basemap tiles, the
panel, and axe — so the live check is 18 tests in 13 seconds instead of the whole suite.

**Evidence:** live smoke 18 passed / 0 failed; local suite 113 passed / 1 skipped;
`check.py --lighthouse` CHECK: PASS (8 checks).

**Worth noting:** Lighthouse performance came in at 85 against a threshold of 85, down
from 91 in P3-08. Same site, same commit — this is run-to-run variance on a cold CDN,
not a regression, but it has no headroom left and the next thing added to the page will
break it. Raised as Q14.

**Phase 3 is complete: 9 of 9.** Next: P4-01 Solver.

## 2026-09-27 — P4-01 Solver: PASS
**Evidence:** pytest 842 passed; `check.py --quick` → **`CHECK: PASS (7 checks)`**, twice in
a row; fresh checker subagent verdict **PASS**.
**Health check first.** The turn opened on `CHECK: FAIL` — ruff was linting the untracked
`/brag` video scratch (`brag-output/`, `stills-tmp.mjs`), not project code. Those files are
now gitignored and kept on disk. The ruff gate itself is unchanged.
**What was missing.** The solvers, docs and the six §8 property tests were already built
across the earlier P4-01 commits (D26–D28). Two acceptance criteria were not met: D13
was enforced by one untested line in `main()` that read the flag alone, and nothing
proved an ambulance standby point is never given stock. `stock_holding_centres()` is now
the only route from `centres.csv` to a solver. It excludes standby points by role, treats
"unknown" as "no", and refuses unreadable or contradictory rows, naming the row (**D29,
proposed** — Samraj to confirm). There are 13 new tests. A mutation run confirmed the
role test goes red when the role rule is deleted.
**The checker re-derived three values independently:**
- example A: 119.964
- example B: LP 16.994 against greedy 8.998
- its own problem: LP 9.1958 against greedy 6.4977

All three match the repo exactly. It also found two real weaknesses:
- One test's solver-loop assertions passed by construction. They are now replaced with
  stronger ones.
- D13 holds only at the gate, and nothing wires centres into a solver yet. This is added
  to P4-02's acceptance, not left as a note.

**Transient:** one run of the external-tile test `basemap tiles actually load` failed
under full-suite load. It passed alone and in the next three full runs. It was not
caused by this change (no site code touched), but it depends on live Esri tiles and may
flake again.
**Next:** P4-02 Scenarios.

## 2026-09-27 — D29 approved; Phase 6 marked pending
**D29 decided by Samraj:** an `ambulance_standby` row marked `can_hold_stock: yes` stops
the run with that row named, rather than being silently excluded. This is what
`stock_holding_centres()` already does, so no code changed; DECISIONS.md now records his
decision and the status moves from proposed to approved.
**Phase 6 is PENDING, not abandoned.** P6-01 (expert agreement) is explicitly blocked on
Samraj collecting real rankings from relief workers in Landhi, using
`docs/expert-ranking-form.md`. There is nothing to build until those forms exist, and
nothing may be simulated in their place (§2.1). `features.json` P6-01 `blocked_on` now
says so in those words.
**Also answered this turn, before any building:** Samraj asked what a Karachi-wide
expansion would involve. Explained in the session (data, solver scale, time, risks);
no expansion work started, pending his go-ahead.
**Next:** P4-02 Scenarios.

## 2026-09-27 — P4-02 split; P4-02a Scenario pipeline and export: PASS
**Why split:** P4-02 asks for precomputed scenarios, and a scenario needs a centre that
holds stock. None has been verified in person (Q2), and inventing one is forbidden
(§2.1). So P4-02a builds and tests the pipeline and the export; **P4-02b** (real
scenarios from a verified centre) is blocked on Q2 and runs automatically once a row
is added to `centres.csv`. Every original P4-02 criterion is kept in P4-02a, and two
were added: shares only (D21), and an honest empty export.
**What changed:** `pipeline/scenarios.py`, `tests/test_scenarios.py` (11 tests),
`site/data/scenarios.json`, `docs/allocation.md` §6, a Sphere entry in `data/SOURCES.md`.
**The Sphere figure is verified, not recalled.** The handbook text says survival water
intake is 2.5–3 L per person per day, "depends on climate and individual physiology"
(p. 107; Appendix 3, p. 145). The 3 L in config is the top of that range, which is right
for a heatwave. The official PDF returned HTTP 403 to our client. We did not retry with a
disguised user agent. The same file hosted by Support to Life was read instead, and the
source is recorded.
**A test replaced by a stronger one.** `test_the_config_the_solver_will_run_on_is_still_
marked_provisional` asserted the basis said UNVERIFIED — a placeholder meant to fail the
moment P4-02 changed it without checking. It now requires the Sphere citation and page,
and still requires `provisional: true`.
**The D21 test found a real leak on its first run.** The solver's equity note says
"8,244 units short of the 16,947 they are owed" — fine for a mentor, a D21 breach on the
site. Summaries now say "fall short by 19% of the stock", and the note is not exported.
**Evidence:** pytest 853 passed; `check.py --quick` CHECK: PASS (7 checks). On the real
grid with a test-only SYNTHETIC depot, LP ≥ greedy in all 18 scenarios.
**Flake, second sighting:** `basemap tiles actually load` (phone) failed once under the
full suite and passed alone and on the rerun. It depends on live Esri tiles; recorded,
not loosened.
**Next:** P4-03 Planner page.

## 2026-09-27 — P4-03 Planner page: PASS
**What changed:** `site/plan.html`, `site/plan.js`, `site/planner-core.js` (the arithmetic,
kept apart so it can be tested against Python), planner styles, cell centroids added to
`cells.geojson`, planner settings added to `scenarios.json`,
`tests/e2e/planner.spec.js` (10 tests × 2 viewports), and
`tests/fixtures/make_planner_fixtures.py` + `tests/test_planner_fixtures.py`.
**Two sections, honestly separated.** *Exact plans* come only from the precomputed
scenarios, which today says no centre has been verified. *Quick estimate — approximate*
runs greedy in the browser from stock points the user places ("your own what-ifs, not
verified relief centres"). That is a new design choice, recorded as **D30** and raised as
**Q16** for Samraj.
**The browser greedy is proved equal to the Python one, not assumed.** A fixture of 63
SYNTHETIC problems solved by `solve_greedy` is replayed in the page and must match
exactly. Mutation checks: dropping the whole-unit floor fails it; widening the distance
limit fails it; **reversing the tie order passed all 60 random problems**, because random
draws almost never tie. Three hand-written tie cases were added, and now that mutation
fails too. A second pytest fails if the fixtures drift from the solver.
**Evidence:** planner suite 20 passed; `check.py --quick` CHECK: PASS (7 checks);
screenshots at 375 and 1280 reviewed with a clean console.
**Screenshot critique, two fixes:** the supply label was cut off on a phone, so it is
shorter now. "Estimated need met" now says "Model's estimated need met", because a column
reading 100% next to a 2.3× undercount needs to say whose estimate it is.
**Seen in the screenshot, worth knowing:** with 3,000 L at one central point, the
top-ranked area alone takes 36% of the stock, and only 9 areas are served. That is
priority-first working as designed, and it shows how quickly supply is used up.
**Next:** P5-02 Offline and P5-04 README, which have no Phase 4 dependency; then P5-01
Field briefs.

## 2026-09-27 — P5-02 Offline: PASS (and `pipeline.run` finally exists)
**What changed:** `site/sw.js` (network-first service worker that precaches the shell and
data), `site/offline.js` and `site/sw-register.js`, `pipeline/roads.py`
(`site/data/roads.geojson`, 421 OSM main-road lines, 72 kB), `tests/test_offline.py`,
`tests/e2e/offline.spec.js`.
**Offline means instead of tiles, not on top of them.** The first test run found 12 Esri
tiles showing offline. They came from the browser's own HTTP cache, not ours. A handful
of leftover tiles would look like a map while missing most of it, so the offline view
now removes the tile layer and draws the road outline alone. The test checks that our
cache holds no third-party tile, because Esri's tiles are not ours to store.
**A layout fault caught by the screenshot:** the offline notice sat outside the page
column at x = 0. It is now inside it, and a test checks it shares the heading's edge.
**Overpass was polite-failed, not hammered.** The roads query got 504 from both
endpoints after five spaced retries. The next piece of work went ahead, and the query
succeeded on a later run from the cache-backed client.
**`pipeline.run` was referenced in CLAUDE.md but never written.** It now exists
(`--all`, `--from STEP`, `--list`). A full rebuild from the cache took about 110 s. It
reproduced every committed output byte for byte **except two date stamps**: the boundary's
`accessed` and the grid's `generated` are set to today even when read from cache. Those
two files were restored so the recorded access date stays true. The stamps are a small
provenance bug, logged here rather than silently tolerated.
**Evidence:** offline suite 8 passed; pytest 859 passed; `check.py --lighthouse` CHECK:
PASS (8 checks), performance 88 / accessibility 100 / best practices 96 / SEO 100.
**Next:** P5-04 README, then P5-01 Field briefs.

## 2026-09-27 — P5-01 Field briefs: PASS
**What changed:** `pipeline/localities.py` (the 12 named OSM place nodes inside Landhi,
now a proper pipeline step), `scripts/field_briefs.py` and `scripts/render_briefs.mjs`,
`site/briefs/` (12 × HTML, PDF, PNG, plus `index.json`), the Field briefs page, 
`tests/test_field_briefs.py` (10) and `tests/e2e/briefs.spec.js` (3 × 2 viewports).
**What a brief is.** One A4 page per place: a headline in plain words, a map of Landhi
with the nearby areas coloured (vector, no tiles, so it prints and photocopies), what
pushes the scores up, a table of the areas, four questions worth asking on the ground,
the caveats, and lines for visit notes. It covers the areas within **500 m of the point
OSM marks**. A place node is a point, not a boundary, and the page says so rather than
drawing a neighbourhood that does not exist.
**Found and fixed by looking at the output:**
1. The first render ran off the bottom of the page. The layout was tightened, and the
   renderer now **fails** if the footer ends below the page. The page hides overflow, so
   a page count alone could not have caught it.
2. "Why these areas rank where they do" read as praise on a low-ranked place, so it now
   says "What pushes these areas' scores up". "Confident about none of them being in
   the top fifth" was ambiguous, so there are now three separate sentences for confident
   in, confident out, and unsure.
3. html-validate caught single-quoted attributes and header cells with no `scope`.
4. On a phone the View / PDF / Image links were about 20 px tall. They are now 44 px, and
   a test checks it.
5. A query I wrote for the localities step asked Overpass for `out tags`, which returns
   no coordinates. It only worked because the cached response came from an earlier
   `out body` query, and a fresh clone would have broken. It now asks for `out body`.
**Precache scope, stated:** the brief pages are precached, so they open offline. The
PDF/PNG downloads are cached on first open instead: twelve pairs would cost a phone
about 8 MB on its first visit. `tests/test_offline.py` names this one exclusion with the
reason. It is not a blanket skip.
**Evidence:** pytest 870 passed; `check.py --quick` CHECK: PASS (7 checks); every PDF is
one A4 page; every file is under 1 MB (largest 422 kB).
**Next:** P5-04 README, P5-03 one-pager.

## 2026-09-27 — P5-04 README: PASS
**What changed:** `README.md` rewritten, `CITATION.cff`, three screenshots in `docs/img/`
taken from the running site and colour-quantised (map 207 kB, panel 19 kB, planner
212 kB), `tests/test_readme.py` (7). The Sphere Handbook and the OSM place names were
added to the site's Data and credits page. About now says that until Samraj sets the
weights, the site runs on placeholder equal weights. Before, it read as if the weights
were already his.
**The README says what is not done.** Its status line names P2-02b, P1-09b and Phase 6.
It also states the 2.3× undercount and that the model cannot see power cuts. A test
fails if any of those disappear.
**Every reproduce command is checked:** a test parses the Reproduce block and asserts
that every `python -m pipeline.X` and `scripts/X.py` it names exists. That is how the
missing `pipeline.run` would have been caught.
**Housekeeping:** the in-progress README and screenshots went into the P5-01 commit by
accident (`git add -A`). They are finished and recorded here.
**For Samraj to check:** `CITATION.cff` splits your name as given names "Samraj Lal",
family name "Ukrani". If "Lal" belongs with the family name, it is a one-line change.
**Evidence:** tests/test_readme.py 7 passed; `check.py --quick` CHECK: PASS (7 checks).
**Next:** P5-03 NGO one-pager.

## 2026-09-27 — P5-03 NGO one-pager: PASS (draft); P5-03b split out, blocked on Samraj
**What changed:** `docs/pitch/one-pager.md` (the draft Samraj edits),
`docs/pitch/one-pager.pdf` and `.html` rendered from it by `scripts/one_pager.py` and
`scripts/render_pdf.mjs`, `tests/test_one_pager.py` (5). `markdown` added to the project's
own environment with `uv add`. Nothing was installed system-wide.
**Why split:** PROMPT.md §12 says the one-pager is written for whichever organisation
agrees to host, and not generically. None has said yes yet (Q2). The draft carries a
marked placeholder for the name. **P5-03b** (tailored to the host, edited into Samraj's
own words) is blocked on him.
**Two faults found by reading the render:**
1. Markdown turned the underscores of the contact line into emphasis, so it printed as
   a short stub. It is now a real 120 mm writing line.
2. "Cannot see power cuts, which is exactly what your teams saw" assumed the host is
   Edhi. It now says the Edhi Foundation named power cuts, which is true whoever hosts.
**A process slip, caught and corrected:** P5-03 was marked passing one command before
its own test went green. The test was failing on a line break inside the D12 sentence.
The test was fixed to normalise whitespace (the wording is unchanged), and the feature
was re-verified: 5 passed, CHECK: PASS. Only then was it committed. §2.3 exists for
exactly this.
**Not sent anywhere.** Samraj hands it over himself (§2.6).
**Evidence:** PDF is 1 A4 page, 176 kB; tests 5 passed; `check.py --quick` CHECK: PASS (7).
**Next:** P5-05 Release, which is blocked on P2-02b.
