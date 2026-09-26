# Data dictionary

`data/processed/indicators.parquet` and `indicators.csv` — one row per H3 cell.

**Cells:** 265 · **Columns:** 14 · **Grid:** H3 resolution 9 over Landhi Town (D2, D3)

Every value is computed over the **clipped** cell — the part of the hexagon inside
the pilot boundary — so no cell reports a neighbouring town's measurements (D15).

| Column | Role | Unit | Missing | Description |
|---|---|---|---|---|
| `h3` | key | — | 0 | H3 cell index, resolution 9 |
| `clipped_area_km2` | key | km² | 0 | Area of the cell inside the pilot boundary |
| `inside_fraction` | key | fraction | 0 | Share of the hexagon inside the boundary |
| `lst_mean_c` | indicator | degC | 0 | Hot-season daytime land surface temperature, mean of the April-June median composite 2022-2026 |
| `lst_p90_c` | context | degC | 0 | 90th percentile of the same composite: how hot the cell gets at worst. Shown in the panel, not indexed (D4) |
| `population` | indicator | people | 0 | Modelled residents, Meta HRSL v1.5 (2020). Undercounts: see D16 |
| `density_per_km2` | context | people per km2 | 0 | Population divided by the clipped cell area |
| `people_over60` | context | people | 0 | Modelled residents aged 60+. Used by D8's need definition, not indexed |
| `people_under5` | context | people | 0 | Modelled residents under 5. Used by D8's need definition, not indexed |
| `lack_green` | indicator | fraction | 0 | 1 minus green cover fraction, ESA WorldCover 10 m (2021) |
| `green_fraction` | context | fraction | 0 | Vegetation classes 10/20/30/40/95 |
| `built_fraction` | context | fraction | 0 | WorldCover built-up surface. Dropped as an indicator by D19 (correlates ~0.93 with lack_green and double-counts Hazard) |
| `dist_health_m` | indicator | m | 0 | Straight-line distance to the nearest OSM health facility x 1.3 circuity factor. Overstates isolation: OSM maps ~11% of Landhi (D18) |
| `dist_centre_m` | indicator | m | **265 (all)** | Distance to the nearest VERIFIED relief centre. Empty: P1-09b is blocked on QUESTIONS.md Q2, and there is no open-data fallback |

## Missing values

Every scored indicator is complete except one, and that gap is structural rather
than accidental:

- **`dist_centre_m` is empty for all cells.** P1-09b is blocked on QUESTIONS.md Q2:
  no relief centre has been verified in person, and there is no open-data fallback.
  OpenStreetMap covers about 11% of Landhi's built area (D18), so its silence about
  relief facilities is not evidence that none exist. 11 unverified candidates are
  listed in `data/manual/centre_candidates.csv`; none may enter the model.
  The table is rebuilt once a centre is verified.

## What these numbers are not

- `lst_mean_c` is **land surface temperature, not air temperature**, and carries no
  humidity information — which matters enormously in Karachi.
- `population` **undercounts by roughly a factor of 2.3** against the 2023 census
  (D16). Relative ranking survives a uniform factor; the bias may not be uniform.
- `dist_health_m` **overstates** isolation from care, because unmapped clinics can
  only make the true distance shorter (D18).
- Age **shares** were dropped (D17) because Meta's layers encode an administrative
  zone rather than spatial demography. The **counts** here are still usable.
- Load-shedding is absent (D20). The mechanism Faisal Edhi named in June 2024 is the
  one this model cannot see.

## Provenance

Every dataset, its licence, access date, resolution and caveats are in
`data/SOURCES.md`. Raw downloads are checksummed in `data/raw/manifest.json`.
