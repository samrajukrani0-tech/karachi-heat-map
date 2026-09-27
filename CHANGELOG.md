# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions
follow [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-09-27

**Released on provisional equal weights, by Samraj's decision (D32).** PROMPT.md §14
allows v1 to ship either with his AHP weights or with a recorded decision to ship equal
weights; he chose the second for now. The site still labels the model provisional. His
own weights (P2-02b), a verified relief centre (P1-09b) and expert validation (P6-01)
are planned for v1.1 and later.

### Added
- **Pilot area and grid:** Landhi Town from OSM relation 16350631 (25.37 km²), covered
  by 265 H3 resolution-9 cells with 99.1% coverage, every indicator computed over the
  clipped cell (D2, D3, D15).
- **Indicators:** hot-season daytime land surface temperature from 48 Landsat 8/9 scenes
  (April–June 2022–2026); Meta population; ESA WorldCover green cover; distance to the
  nearest OSM health facility. Age counts, built-up surface and the LST 90th percentile
  are computed as panel context.
- **Model:** robust min–max normalisation (D5); Priority as a weighted geometric mean of
  Hazard, Exposure and Vulnerability, with Exposure deliberately unfloored (D6, D23); an
  AHP tool for Samraj's weights (D7, D22); 1,000-draw sensitivity analysis with a
  directional confidence call (D25); a validation pack and an expert-ranking form (D14).
- **Model report** (`docs/model-report.md`), limitations first, checked against the data
  by tests.
- **Website** on GitHub Pages: map with five layers, a cell panel with reasons and
  confidence, How it works, Data and credits, and About. Accessible (axe clean),
  mobile-first, Lighthouse gated.
- **Allocation:** an exact integer programme (HiGHS) and a greedy baseline (D26–D29),
  hand-solvable examples in `docs/allocation.md`, precomputed scenarios exported as
  shares only (D21), and the Sphere 2018 survival water figure verified and cited.
- **Plan supplies page:** exact scenarios once a centre is verified, plus a browser-side
  quick estimate from stock points the user places, labelled approximate (D30). The
  browser version is proved to match the Python solver on 63 problems.
- **Offline mode:** a service worker caches the site and data, and the offline map draws
  OSM main roads instead of the basemap tiles.
- **Field briefs:** one A4 page per named OSM locality (12), as HTML, PDF and PNG, each
  under 1 MB.
- **NGO one-pager** draft (`docs/pitch/`), for Samraj to tailor and hand over himself.
- **Reproducibility:** `uv run python -m pipeline.run --all` rebuilds everything from a
  checksummed download cache, and the rebuild reproduces every committed output.
- README with screenshots, `CITATION.cff`, and three licences: MIT, CC BY 4.0, ODbL 1.0.
- **Expert validation, prepared:** `pipeline/expert.py` imports completed ranking forms and
  compares them with the model (D31). It waits for real rankings and does nothing until then.

### Known limitations (stated on the site as well)
- Weights are provisional equal weights (P2-02b).
- Distance to a relief centre has no data: no centre has been verified in person
  (P1-09b), so the planner has no exact scenarios yet (P4-02b).
- The population layer counts about 43% of the 2023 census total for Landhi (D16).
- Age could not be mapped within Landhi (D17), and power cuts are not modelled (D20).
- Expert validation (Phase 6) waits on rankings from relief workers in Landhi.

### Removed (by decision)
- Night-time LST and the Relative Wealth Index: too coarse for 25 km² (D4).
- Age shares (D17), built-up fraction from the index (D19), load-shedding (D20).
- Urdu for v1 (D9); strings stay externalised so it can be added later.
