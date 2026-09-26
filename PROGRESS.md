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
