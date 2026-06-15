# 🏙️ NYC Affordable Housing — Energy Efficiency Dashboard

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat-square&logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?style=flat-square&logo=powerbi&logoColor=black)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-22C55E?style=flat-square)

> **Analyzed 10,000+ NYC affordable housing units to surface energy inefficiency patterns — reducing manual reporting time by 45% and enabling borough-level capital planning decisions.**

---

## 📌 Project Overview

New York City's affordable housing portfolio spans thousands of buildings with varying levels of energy efficiency. This project builds an **end-to-end analytics pipeline** — from raw open data ingestion to an interactive Power BI dashboard — to help housing authorities identify which buildings are consuming the most energy per square foot, benchmark performance by borough and building type, and prioritize retrofit investments.

### Business Questions Answered
- Which boroughs and building types have the highest energy use intensity (EUI)?
- What % of units are above the NYC benchmarking threshold?
- How does building age correlate with energy inefficiency?
- Where should retrofit investments be prioritized to maximize impact?

---

## 🏗️ Architecture

```
NYC Open Data (LL84 Benchmarking)
        │
        ▼
┌──────────────────┐
│  Python Ingestion │  ← data_ingestion.py
│  & Cleaning       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   SQL Transforms  │  ← analysis_queries.sql
│   & Aggregations  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Processed CSV   │  ← nyc_housing_energy_processed.csv
│   (Star Schema)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Power BI Report  │  ← dashboard/
│  (Interactive)    │
└──────────────────┘
```

---

## 📁 Repository Structure

```
nyc-housing-energy-dashboard/
│
├── data/
│   ├── raw/                        # Source data from NYC Open Data
│   └── processed/                  # Cleaned, transformed output
│
├── sql/
│   └── analysis_queries.sql        # Core SQL: EUI rankings, borough aggregations, benchmarks
│
├── python/
│   ├── data_ingestion.py           # Fetch + clean raw data
│   ├── feature_engineering.py      # EUI calculation, age buckets, efficiency tiers
│   └── summary_stats.py            # Generate KPI summary table
│
├── dashboard/
│   └── README.md                   # Dashboard screenshots + DAX measures reference
│
├── docs/
│   └── data_dictionary.md          # Field definitions and transformation logic
│
└── README.md
```

---

## 🔑 Key Metrics & Results

| Metric | Value |
|--------|-------|
| Buildings Analyzed | 10,847 |
| Boroughs Covered | 5 (BX, BK, MN, QN, SI) |
| Avg. Energy Use Intensity (EUI) | 112 kBtu/sq ft/yr |
| Buildings Above NYC Threshold (>100 EUI) | 58% |
| Reporting Time Reduction | 45% (vs. manual Excel process) |
| Top Inefficiency Borough | Bronx (avg EUI: 134) |

---

## 🧹 Data Pipeline

### Source
NYC Local Law 84 (LL84) Benchmarking data — publicly available via [NYC Open Data](https://data.cityofnewyork.us/)

### Transformations Applied
- Removed buildings with missing/null energy consumption values
- Standardized building type classifications (residential, mixed-use, commercial)
- Calculated **Energy Use Intensity (EUI)** = Site Energy Use (kBtu) / Gross Floor Area (sq ft)
- Created efficiency tier labels: `Efficient`, `Moderate`, `Inefficient`, `Critical`
- Binned building age into construction era buckets (Pre-1940, 1940–1980, Post-1980)

---

## 💻 SQL Highlights

```sql
-- Top 10 most energy-inefficient buildings by borough
SELECT
    borough,
    property_name,
    address,
    building_type,
    ROUND(site_energy_use_kbtu / gross_floor_area_sqft, 2) AS eui,
    construction_year,
    CASE
        WHEN site_energy_use_kbtu / gross_floor_area_sqft > 150 THEN 'Critical'
        WHEN site_energy_use_kbtu / gross_floor_area_sqft > 100 THEN 'Inefficient'
        WHEN site_energy_use_kbtu / gross_floor_area_sqft > 75  THEN 'Moderate'
        ELSE 'Efficient'
    END AS efficiency_tier
FROM nyc_housing_benchmarking
WHERE gross_floor_area_sqft > 0
  AND site_energy_use_kbtu IS NOT NULL
ORDER BY eui DESC
LIMIT 10;
```

See full query set → [`sql/analysis_queries.sql`](sql/analysis_queries.sql)

---

## 🐍 Python Highlights

```python
# Feature engineering — EUI calculation + efficiency tiering
df['eui'] = df['site_energy_use_kbtu'] / df['gross_floor_area_sqft']

def assign_efficiency_tier(eui):
    if eui > 150:   return 'Critical'
    elif eui > 100: return 'Inefficient'
    elif eui > 75:  return 'Moderate'
    else:           return 'Efficient'

df['efficiency_tier'] = df['eui'].apply(assign_efficiency_tier)
```

See full pipeline → [`python/feature_engineering.py`](python/feature_engineering.py)

---

## 📊 Dashboard Features (Power BI)

| Page | What It Shows |
|------|---------------|
| **Executive Summary** | KPI cards: total buildings, avg EUI, % above threshold, top borough |
| **Borough Drill-Through** | EUI by borough with map visual + building count |
| **Building Type Analysis** | Clustered bar: EUI by building type and construction era |
| **Retrofit Priority Matrix** | Scatter: EUI vs. floor area — size = potential savings |
| **Trend Over Time** | Line: average EUI by reporting year (2018–2023) |

### Key DAX Measures
```dax
Avg EUI = AVERAGE(housing_data[eui])

% Above Threshold = 
DIVIDE(
    COUNTROWS(FILTER(housing_data, housing_data[eui] > 100)),
    COUNTROWS(housing_data)
) * 100

Buildings in Critical Tier = 
CALCULATE(COUNTROWS(housing_data), housing_data[efficiency_tier] = "Critical")
```

---

## ⚙️ How to Run

```bash
# 1. Clone the repo
git clone https://github.com/RuthvikM92/nyc-housing-energy-dashboard.git
cd nyc-housing-energy-dashboard

# 2. Install dependencies
pip install pandas numpy requests matplotlib seaborn

# 3. Run data ingestion
python python/data_ingestion.py

# 4. Run feature engineering
python python/feature_engineering.py

# 5. Output will be in data/processed/nyc_housing_energy_processed.csv
#    Load this into Power BI to rebuild the dashboard
```

---

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| Data Source | NYC Open Data (Socrata API) |
| Data Processing | Python (Pandas, NumPy) |
| Analysis & Querying | SQL (PostgreSQL syntax) |
| Visualization | Power BI (DAX, Power Query) |
| Version Control | Git / GitHub |

---

## 📚 Data Dictionary

See [`docs/data_dictionary.md`](docs/data_dictionary.md) for full field definitions.

---

## 👤 Author

**Ruthvik Mandala** — Data Analyst | IBM  
[LinkedIn](https://www.linkedin.com/in/ruthvik-mandala) · [GitHub](https://github.com/RuthvikM92)
