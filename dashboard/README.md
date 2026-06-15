# Power BI Dashboard Reference

## Dashboard Pages

| Page | Purpose |
|------|---------|
| **Executive Summary** | High-level KPIs: total buildings, avg EUI, % above threshold, top borough |
| **Borough Analysis** | Map + bar chart: EUI by borough with drill-through to building list |
| **Building Type Breakdown** | Clustered bar: avg EUI by building type + construction era |
| **Retrofit Priority Matrix** | Scatter plot: EUI (Y) vs. floor area (X), bubble size = potential savings |
| **Trend Over Time** | Line chart: avg EUI by reporting year (2018–2023) |

---

## DAX Measures

```dax
-- ── Core KPIs ──────────────────────────────────────────────────────────────

Total Buildings = COUNTROWS(housing_data)

Avg EUI =
ROUND(AVERAGE(housing_data[eui]), 1)

Median EUI =
ROUND(MEDIANX(housing_data, housing_data[eui]), 1)

Pct Above Threshold =
DIVIDE(
    CALCULATE(COUNTROWS(housing_data), housing_data[eui] > 100),
    COUNTROWS(housing_data)
) * 100

Critical Buildings =
CALCULATE(COUNTROWS(housing_data), housing_data[efficiency_tier] = "Critical")

Total Potential Savings (kBtu M) =
ROUND(SUM(housing_data[potential_savings_k]) / 1000, 1)


-- ── Comparison measures ────────────────────────────────────────────────────

EUI vs NYC Average =
VAR SelectedAvg = AVERAGE(housing_data[eui])
VAR OverallAvg  = CALCULATE(AVERAGE(housing_data[eui]), ALL(housing_data))
RETURN SelectedAvg - OverallAvg

EUI YoY Change =
VAR CurrentYear  = MAX(housing_data[reporting_year])
VAR PreviousYear = CurrentYear - 1
VAR CurrentEUI   = CALCULATE(AVERAGE(housing_data[eui]),
                       housing_data[reporting_year] = CurrentYear)
VAR PreviousEUI  = CALCULATE(AVERAGE(housing_data[eui]),
                       housing_data[reporting_year] = PreviousYear)
RETURN
    IF(ISBLANK(PreviousEUI), BLANK(),
       DIVIDE(CurrentEUI - PreviousEUI, PreviousEUI) * 100)


-- ── Color-coding for efficiency tiers ────────────────────────────────────

Tier Color =
SWITCH(
    SELECTEDVALUE(housing_data[efficiency_tier]),
    "Efficient",    "#22C55E",   -- green
    "Moderate",     "#F59E0B",   -- amber
    "Inefficient",  "#F97316",   -- orange
    "Critical",     "#EF4444",   -- red
    "#94A3B8"                    -- gray (unknown)
)
```

---

## Data Connection

- **Data source:** `data/processed/nyc_housing_energy_processed.csv`
- **Refresh:** Import mode (re-run Python pipeline to refresh)
- **Relationships:** Single flat table (no star schema needed at this scale)

---

## Screenshots

> Add Power BI screenshots here after publishing the `.pbix` file.
> Recommended: Executive Summary page + Retrofit Priority Matrix scatter.
