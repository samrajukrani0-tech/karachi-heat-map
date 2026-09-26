# Data sources

Every dataset used, with its URL, licence, access date, resolution and caveats.
Nothing enters the pipeline without an entry here.

Storage CRS: EPSG:4326. All distances and areas: EPSG:32642 (UTM zone 42N).

---

## Used in Phase 0

### OpenStreetMap administrative boundaries
- **URL:** https://overpass-api.de/api/interpreter (Overpass API)
- **Objects:** relation 16350631 (Landhi Town, admin_level=7) and, for the D2
  comparison, relations 16350629, 16350630, 16351913, 16351914
- **Licence:** ODbL 1.0 — © OpenStreetMap contributors
- **Accessed:** 2026-09-26
- **Resolution:** vector
- **Caveats:** town boundaries in OSM follow the post-2022 local-government
  reorganisation and are community-maintained; P1-01 must re-verify the geometry and
  record its own provenance rather than relying on this Phase 0 query.

### OpenStreetMap health facilities (count only, for the D2 comparison)
- **Query:** `amenity=hospital|clinic|doctors` inside each candidate town
- **Counts:** Korangi 56, Malir 41, Shah Faisal 39, Landhi 32
- **Licence:** ODbL 1.0
- **Accessed:** 2026-09-26
- **Caveats:** OSM coverage of Karachi health facilities is incomplete and
  unevenly maintained. P1-09 must measure and report the gap, not assume coverage.

### OpenStreetMap relief-centre search — negative result
- **Query:** names matching `Edhi|Saylani` inside each candidate town
- **Result:** **zero** matches in Landhi, Korangi, Shah Faisal and Malir Towns;
  55 matches across the wider Karachi bounding box, several of them false positives
  ("Edhi Interchange", "Medhi Manji Lab")
- **Accessed:** 2026-09-26
- **Consequence:** there is no open-data source for relief centres in the pilot area.
  `data/manual/centres.csv` is the only source, and it requires in-person
  verification (QUESTIONS.md Q2).

### 2023 census population (context for D2)
- **URL:** https://www.citypopulation.de/en/pakistan/admin/
- **Figures used:** Korangi District 3,128,971; Malir District 2,432,248
- **Original source:** Pakistan Bureau of Statistics, census date 2023-03-01
- **Accessed:** 2026-09-26
- **Caveats:** a secondary compilation. Used only as context for choosing the pilot
  area. P1-06 needs an independent figure at a matching administrative unit, ideally
  taken from PBS directly.

### June 2024 heatwave reporting (for face validity, P2-05)
- **Dawn, 25 June 2024:** https://www.dawn.com/news/1841754 — read directly.
  Names Landhi among the localities bodies were brought from, and records Edhi's
  Korangi mortuary receiving 10 bodies against a normal 5–6, Moosa Lane 35 against a
  normal 5–7, and Sohrab Goth 95 against a normal 30–35.
- **Bloomberg:** https://bnnbloomberg.ca/karachi-sees-a-surge-in-deaths-as-heat-wave-sears-pakistan-1.2090293 — cited in PROMPT.md, not yet read directly.
- **Express Tribune:** https://tribune.com.pk/story/2473712/heatwave-wreaks-havoc-15-found-dead-on-streets — **returns HTTP 403; not read, nothing cited from it.** See QUESTIONS.md Q1.
- **Caveat that must appear wherever these are used:** causes of death were disputed
  by the Sindh health department. This project never estimates deaths or assigns
  causes; the reporting is used only as a locality-level sanity check.

---

## Planned (Phase 1) — verify at fetch time; IDs, band names and licences change

| Dataset | Indicator | Access | Licence | Notes |
|---|---|---|---|---|
| Landsat 8/9 Collection 2 Level-2 (`landsat-c2-l2`, `lwir11`) | daytime LST | Microsoft Planetary Computer STAC; fallback AWS Earth Search (Element 84) | public domain (USGS) | April–June, several recent years; mask cloud/shadow with `qa_pixel`; median composite; check the USGS scale/offset (documented as 0.00341802 × DN + 149.0 = K) |
| Meta (Data for Good) high-resolution population density, Pakistan | people per cell | HDX | CC BY 4.0 | ~30 m; compare against WorldPop before choosing |
| WorldPop constrained 100 m, Pakistan | people per cell | worldpop.org | CC BY 4.0 | reference year must be recorded |
| Meta demographic layers (60+, under 5) | age shares | HDX | CC BY 4.0 | handle zero-population cells explicitly |
| Google Open Buildings / Microsoft Global ML Building Footprints | built fraction | respective releases | CC BY 4.0 / ODbL | check Karachi coverage first; OSM buildings as fallback, with a completeness caveat |
| ESA WorldCover 10 m | lack of green cover | Planetary Computer | CC BY 4.0 | Sentinel-2 hot-season NDVI as an alternative |
| OpenStreetMap health facilities | distance to care | Overpass / osmnx | ODbL 1.0 | road-network distance if a routable graph works, else straight line × 1.3 |
| `data/manual/centres.csv` | distance to relief centre | hand-made, verified in person | project data | unverified candidates are excluded, not guessed |
| K-Electric load-shed schedules | load-shedding exposure | publicly published schedules | see their terms | gated behind the P1-10 feasibility study |
