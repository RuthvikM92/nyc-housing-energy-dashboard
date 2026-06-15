# Data Dictionary

## Source: NYC Local Law 84 (LL84) Benchmarking Dataset

**Source URL:** https://data.cityofnewyork.us/resource/vdzd-yy49.json  
**Update Frequency:** Annual  
**Coverage:** Buildings ≥ 25,000 sq ft in NYC

---

## Raw Fields (after ingestion)

| Field | Type | Description |
|-------|------|-------------|
| `property_name` | string | Building name as self-reported by owner |
| `address` | string | Street address |
| `borough` | string | NYC borough (Manhattan, Brooklyn, Bronx, Queens, Staten Island) |
| `gross_floor_area_sqft` | float | Total gross floor area in square feet |
| `site_eui_kbtu_ft` | float | Site Energy Use Intensity from LL84 filing (kBtu/sq ft) |
| `weather_norm_eui` | float | Weather-normalized EUI — adjusts for atypical climate years |
| `site_energy_use_kbtu` | float | Total annual site energy consumption in kBtu |
| `construction_year` | int | Year the building was constructed |
| `building_type` | string | Primary property type (e.g., Multifamily Housing, Office) |
| `reporting_year` | int | Year of LL84 compliance report (energy data is for prior year) |
| `latitude` | float | Latitude coordinate for map visuals |
| `longitude` | float | Longitude coordinate for map visuals |

---

## Engineered Features (added in feature_engineering.py)

| Field | Type | Formula / Logic | Purpose |
|-------|------|-----------------|---------|
| `eui` | float | `site_energy_use_kbtu / gross_floor_area_sqft` | Normalised energy intensity metric — the primary KPI |
| `efficiency_tier` | categorical | EUI >150 → Critical; >100 → Inefficient; >75 → Moderate; ≤75 → Efficient | Dashboard color-coding and filter |
| `construction_era` | categorical | Year buckets: Pre-1940 / 1940–1979 / 1980–1999 / 2000–Present | Age-vs-efficiency analysis |
| `size_category` | categorical | <25k / 25k–100k / 100k–500k / 500k+ sq ft | Building size segmentation |
| `potential_savings_k` | int | `max(eui - 75, 0) × gross_floor_area_sqft / 1,000` | Estimated kBtu savings (thousands) if brought to baseline EUI of 75 |

---

## Efficiency Tier Thresholds

| Tier | EUI Range | Meaning |
|------|-----------|---------|
| **Efficient** | ≤ 75 kBtu/sq ft | At or below NYC best-practice target |
| **Moderate** | 76–100 | Above target but below NYC LL84 penalty threshold |
| **Inefficient** | 101–150 | High energy use; qualifies for efficiency programs |
| **Critical** | > 150 | Significantly over-consuming; priority retrofit candidates |

---

## Notes on Data Quality

- Buildings with `gross_floor_area_sqft = 0` or `site_energy_use_kbtu = 0` are excluded (data errors)
- EUI values > 1,000 are treated as outliers and removed (~0.3% of records)
- `construction_year` is missing for ~8% of buildings — these are bucketed as "Unknown" in construction era
- Weather-normalized EUI (`weather_norm_eui`) is preferred for year-over-year trend analysis; raw `eui` is used for benchmarking snapshots
