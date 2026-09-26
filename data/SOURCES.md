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
  reorganisation and are community-maintained.
- **Used by P1-01 (2026-09-26):** `pipeline/boundary.py` re-fetched relation 16350631
  independently of the Phase 0 query and measured **25.370 km²** in EPSG:32642, matching
  the Phase 0 figure. Output `data/processed/pilot_area.geojson` (EPSG:4326) carries its
  own provenance: relation id, admin level, licence, access date and the sha256 of the
  raw Overpass response. The build **refuses to write** if the measured area falls
  outside `config/area.yaml`'s 25.37 ± 0.75 km², so a silent upstream boundary change
  fails the build instead of quietly redefining the pilot area.
- **Raw cache:** `data/raw/osm/relation_16350631.json` (gitignored). Registered in
  `data/raw/manifest.json` (tracked in git) with its url, sha256, size, date and licence
  since P1-03.
- **What the response hash does and does not prove:** Overpass embeds a timestamp in
  every response, so re-running the identical query yields a different sha256 while the
  geometry is unchanged. The hash fingerprints one download; it is **not** a content hash
  of the boundary. Reproducibility of the result is checked by re-measuring the area
  (25.370 km² on both downloads), and `pilot_area.geojson` carries a
  `raw_response_sha256_note` saying exactly this.

### Derived: H3 analysis grid (P1-02, 2026-09-26)
- **Output:** `data/processed/grid.geojson` — 265 H3 resolution-9 cells, EPSG:4326.
- **Derived from:** `data/processed/pilot_area.geojson` (OSM relation 16350631) via
  `pipeline/grid.py`. No new upstream data.
- **Licence:** ODbL 1.0 — a derived database of OpenStreetMap, © OpenStreetMap contributors.
- **Inclusion rule (D15, provisional):** centre inside the boundary, or ≥ 25% of the
  cell's area inside. 248 cells qualify by centre, 17 by the area rule.
- **Coverage:** 99.115% of the boundary; 0.885% — thin edge slivers — is covered by no
  cell and must appear in the model report's limitations.
- **Caveat that travels with every indicator:** hexagons total 27.080 km² while Landhi is
  25.370 km². Indicators are computed over the **clipped** geometry (cell ∩ boundary),
  so the 1.935 km² of overhang is excluded and no cell reports a neighbouring town's
  values. `clipped_area_km2` is stored per cell.

### OpenStreetMap health facilities (count only, for the D2 comparison)
- **Query:** `amenity=hospital|clinic|doctors` inside each candidate town
- **Counts:** Korangi 56, Malir 41, Shah Faisal 39, Landhi 32
- **Licence:** ODbL 1.0
- **Accessed:** 2026-09-26
- **Caveats:** OSM coverage of Karachi health facilities is incomplete and
  unevenly maintained. P1-09 must measure and report the gap, not assume coverage.

### OpenStreetMap relief-centre search — negative result, re-run and widened
- **First query (2026-09-26, superseded):** names matching `Edhi|Saylani` inside each
  candidate town. Result: zero. **That query was weaker than it was first reported to
  be** — it missed spelling variants, and the wider search below found a Saylani branch
  recorded in OSM as "Silani Welfare - Korangi 4", which the original pattern could not
  have matched anywhere.
- **Widened query (2026-09-26):** `name` or `operator` matching
  `Edhi|Edhee|Aidhi|Saylani|Silani|Sailani|Saylany|Chhipa|Chipa|Chippa|Cheepa|Alkhidmat|
  Al-Khidmat|Al Khidmat|Aman Foundation|JDC|Khidmat-e-Khalq` plus the Urdu forms
  `ایدھی|سیلانی|چھیپا|الخدمت`, over bbox 24.74,67.03,25.00,67.42; plus
  `amenity=social_facility|charity`, `office=charity|ngo`,
  `emergency=ambulance_station` and `amenity=ambulance_station` over the same area.
- **Result:** 133 distinct objects across the bounding box; **zero inside the Landhi
  Town boundary.** The single OSM `social_facility` inside Landhi is
  "Maqsood Haleem karkhana" (node/12142718007), which is a food workshop, not a welfare
  facility — an example of the tagging noise that makes OSM unusable as a relief-centre
  source here.
- **Consequence, unchanged:** there is no open-data source for relief centres in the
  pilot area. `data/manual/centres.csv` remains the only source and requires in-person
  verification (QUESTIONS.md Q2). Candidates found nearby are recorded separately in
  `data/manual/centre_candidates.csv`, all marked `UNVERIFIED`; nothing in that file
  enters the model.
- **Licence:** ODbL 1.0 — © OpenStreetMap contributors.

### OpenStreetMap health facilities inside Landhi Town
- **Query:** `amenity=hospital|clinic|doctors|pharmacy` inside relation 16350631
- **Result:** 37 named objects (16 tagged `hospital`, 14 `clinic`, 5 `pharmacy`,
  plus others). Named landmarks include Landhi Medical Complex, Landhi Cardiac
  Emergency Center, Urban Health Center Babar Market Landhi, MALC Landhi Leprosy
  Centre, Awadh Hospital, Al Razi Hospital and Razia Sultana Hospital.
- **Accessed:** 2026-09-26
- **Caveat for P1-09:** at least two objects tagged `amenity=hospital` are clearly
  mis-tagged ("Finger steel ring cutting master" node/12140157270, "Alhameed Welvear
  Medical Store" node/12139620326). P1-09 must filter on more than the tag alone and
  must report the error rate it finds, not assume the tagging is correct.

### Express Tribune, 25 June 2024 — text supplied by Samraj
- **URL:** https://tribune.com.pk/story/2473712/heatwave-wreaks-havoc-15-found-dead-on-streets
- **Status:** returns HTTP 403 to automated fetching. Samraj opened it in a browser and
  supplied the text on 2026-09-26. The article text is **not** stored in this repo
  (copyright); only extracted facts are recorded, here and in QUESTIONS.md Q1.
- **Facts used:** 15 bodies recovered from streets on 24 June 2024, of which Chhipa
  volunteers moved 12 and Edhi 3; 526 bodies to three Edhi Karachi morgues over the
  week against a normal 30–40 a day, risen to 100–140; Faisal Edhi said some deaths may
  be heat-related but unconfirmed; Police Surgeon Dr Summaiya Syed confirmed 4
  heatstroke deaths on 24 June; Edhi's three cold storages are at Moosa Line, Sohrab
  Goth and Korangi.
- **Localities named:** Orangi Town (×3), MA Jinnah Road, Karimabad, Super Highway
  (Faqira Goth), Old Golimar, Gulistan-e-Johar Block 11, **Landhi (near Landhi
  Hospital's Chowrangi)**, New Karachi Sector 11-D, Surgical Market, Civil Lines,
  Mahmoodabad, North Karachi UP Mor, Shah Faisal Colony / Green Town.
- **Caveat that must travel with this source:** only one named locality falls inside the
  pilot area, so it supports a weak face-validity check for Landhi, not a strong one.
  Causes of death were disputed; this project never estimates deaths or assigns causes.

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

### Landsat 8/9 Collection 2 Level-2 surface temperature (P1-04a, 2026-09-26)
- **Access:** Microsoft Planetary Computer STAC API,
  `https://planetarycomputer.microsoft.com/api/stac/v1`, collection `landsat-c2-l2`,
  assets `lwir11` (Surface Temperature Band) and `qa_pixel`. Assets signed with the
  `planetary-computer` package; **no account or login is required**.
- **Selection:** April–June, 2022–2026 (Landsat 9 joined in 2022, doubling the cadence),
  platforms landsat-8 and landsat-9, scene cloud cover ≤ 50%. 48 scenes, all WRS path
  152 row 043. Full list with per-scene cloud cover in `data/processed/lst_scenes.csv`.
- **Resolution:** delivered at 30 m. **The thermal sensor's true resolution is about
  100 m**; the 30 m grid is resampled. This is the reason D3 chose H3 resolution 9.
- **Processing:** windowed reads over the pilot area only (never whole scenes);
  `qa_pixel` bits 0–4 masked (fill, dilated cloud, cirrus, cloud, cloud shadow);
  USGS scaling `kelvin = 0.00341802 × DN + 149.0`, then −273.15 to °C; per-pixel median
  across scenes; pixels with fewer than 5 clear looks discarded (none were).
- **Result:** 31.25 to 48.11 °C, median 43.16 °C; 33–47 clear looks per pixel.
- **Licence:** USGS Landsat Collection 2 data carries **no restrictions on use** (US
  public domain). Note: the Planetary Computer STAC collection's own `license` field
  reads `proprietary`, which is the catalogue's generic placeholder rather than a claim
  about Landsat; the USGS terms govern.
- **Caveats that must travel with this indicator:**
  - Land surface temperature is **not air temperature** and not a heat index. Surface
    readings of 43–48 °C are normal when air temperature is nearer 35–40 °C, and
    humidity — which matters enormously in Karachi — is not captured at all.
  - It is a **daytime** measurement, at roughly 05:56 UTC (about 10:56 local). Nights
    that fail to cool are a large part of heat harm and are not represented (D4).
  - The median is taken across five hot seasons, so it describes a typical hot-season
    day, not any particular heatwave.

### Derived: per-cell hot-season LST (P1-04b, 2026-09-26)
- **Output:** `data/processed/lst_cells.csv` — one row per grid cell with `lst_mean_c`,
  `lst_p90_c`, pixel count, pixel coverage, median clear looks and flags.
- **Method:** zonal statistics over the **clipped** cell (cell ∩ pilot boundary, D15),
  via `pipeline/zonal.py`. Cells resting on too few pixels or too few clear looks are
  flagged, not silently averaged; none were.
- **Result:** mean 39.19–46.28 °C (median 43.23), p90 40.21–47.29 °C, 27–113+ pixels per
  cell.
- **Licence:** derived from USGS Landsat (public domain) and the OSM-derived grid, so the
  file falls under `LICENSE-data` (ODbL 1.0) along with the rest of `data/processed`.

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
