"""
summary_stats.py
================
Reads the processed dataset and generates the KPI summary table used
directly in the Power BI Executive Summary page.

Outputs
-------
data/processed/kpi_summary.csv   – one row per borough with 8 KPIs
data/processed/tier_breakdown.csv – efficiency tier counts by borough

Author : Ruthvik Meka
"""

import pandas as pd
import os

BASE_DIR     = os.path.dirname(__file__)
INPUT_FILE   = os.path.join(BASE_DIR, "..", "data", "processed",
                            "nyc_housing_energy_processed.csv")
OUTPUT_DIR   = os.path.join(BASE_DIR, "..", "data", "processed")


def generate_borough_kpis(df: pd.DataFrame) -> pd.DataFrame:
    kpis = df.groupby("borough").agg(
        total_buildings     = ("eui",                    "count"),
        avg_eui             = ("eui",                    "mean"),
        median_eui          = ("eui",                    "median"),
        max_eui             = ("eui",                    "max"),
        pct_above_threshold = ("eui",                    lambda x: (x > 100).mean() * 100),
        total_sqft_M        = ("gross_floor_area_sqft",  lambda x: x.sum() / 1e6),
        total_savings_kM    = ("potential_savings_k",    lambda x: x.sum() / 1_000),
        critical_buildings  = ("efficiency_tier",        lambda x: (x == "Critical").sum()),
    ).round(2).reset_index()
    return kpis


def generate_tier_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    breakdown = (
        df.groupby(["borough", "efficiency_tier"])
          .size()
          .reset_index(name="building_count")
    )
    breakdown["pct_of_borough"] = (
        breakdown.groupby("borough")["building_count"]
                 .transform(lambda x: x / x.sum() * 100)
                 .round(1)
    )
    return breakdown


def main():
    print("Reading processed data …")
    df = pd.read_csv(INPUT_FILE)

    kpis      = generate_borough_kpis(df)
    breakdown = generate_tier_breakdown(df)

    kpis.to_csv(os.path.join(OUTPUT_DIR, "kpi_summary.csv"), index=False)
    breakdown.to_csv(os.path.join(OUTPUT_DIR, "tier_breakdown.csv"), index=False)

    print("\n── Borough KPI Summary ──────────────────────────────────────────")
    print(kpis.to_string(index=False))
    print("\n── Tier Breakdown (first 10 rows) ──────────────────────────────")
    print(breakdown.head(10).to_string(index=False))
    print("\nFiles saved to data/processed/")


if __name__ == "__main__":
    main()
