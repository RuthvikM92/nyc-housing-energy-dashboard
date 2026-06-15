"""
feature_engineering.py
=======================
Reads the cleaned raw CSV produced by data_ingestion.py, engineers all
analytical features required by the Power BI dashboard, and saves the
final processed file.

New columns added
-----------------
eui                  – Energy Use Intensity (kBtu / sq ft / yr)
efficiency_tier      – Categorical: Efficient / Moderate / Inefficient / Critical
construction_era     – Building age bucket (Pre-1940, 1940-1979, 1980-1999, 2000-Present)
potential_savings_k  – Estimated kBtu savings (thousands) if brought to 75 EUI baseline
size_category        – Small / Medium / Large / Very Large by floor area

Author : Ruthvik Meka
"""

import pandas as pd
import numpy as np
import os
import logging

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
INPUT_FILE  = os.path.join(BASE_DIR, "..", "data", "raw",
                           "nyc_housing_benchmarking_raw.csv")
OUTPUT_DIR  = os.path.join(BASE_DIR, "..", "data", "processed")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "nyc_housing_energy_processed.csv")

EUI_BASELINE = 75   # kBtu/sq ft — NYC best-practice target

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Feature functions ─────────────────────────────────────────────────────────
def calc_eui(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Energy Use Intensity (kBtu per sq ft per year)."""
    df["eui"] = (
        df["site_energy_use_kbtu"] / df["gross_floor_area_sqft"]
    ).round(2)
    return df


def assign_efficiency_tier(eui: float) -> str:
    """Map EUI value to a named efficiency tier."""
    if eui > 150:   return "Critical"
    elif eui > 100: return "Inefficient"
    elif eui > 75:  return "Moderate"
    else:           return "Efficient"


def assign_construction_era(year) -> str:
    """Bucket construction year into a readable era label."""
    if pd.isna(year):       return "Unknown"
    year = int(year)
    if year < 1940:         return "Pre-1940"
    elif year < 1980:       return "1940–1979"
    elif year < 2000:       return "1980–1999"
    else:                   return "2000–Present"


def assign_size_category(sqft: float) -> str:
    """Categorise buildings by gross floor area."""
    if sqft < 25_000:       return "Small (<25k sqft)"
    elif sqft < 100_000:    return "Medium (25k–100k sqft)"
    elif sqft < 500_000:    return "Large (100k–500k sqft)"
    else:                   return "Very Large (500k+ sqft)"


def calc_potential_savings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate kBtu savings (in thousands) if each building reached the
    EUI_BASELINE target.  Buildings already at or below baseline get 0.
    """
    excess_eui = (df["eui"] - EUI_BASELINE).clip(lower=0)
    df["potential_savings_k"] = (
        excess_eui * df["gross_floor_area_sqft"] / 1_000
    ).round(0).astype(int)
    return df


# ── Main pipeline ─────────────────────────────────────────────────────────────
def run_pipeline(input_path: str, output_path: str) -> pd.DataFrame:
    log.info(f"Reading {input_path} …")
    df = pd.read_csv(input_path)
    log.info(f"  Loaded {len(df):,} rows, {len(df.columns)} columns.")

    # ── Core features ──────────────────────────────────────────────────────
    df = calc_eui(df)

    # Guard: remove extreme outliers (EUI > 1 000 are data errors)
    before = len(df)
    df = df[df["eui"] <= 1_000]
    log.info(f"  Removed {before - len(df):,} EUI outliers (>1,000).")

    df["efficiency_tier"]   = df["eui"].apply(assign_efficiency_tier)
    df["construction_era"]  = df["construction_year"].apply(assign_construction_era)
    df["size_category"]     = df["gross_floor_area_sqft"].apply(assign_size_category)
    df = calc_potential_savings(df)

    # ── Ordered categoricals (for correct Power BI sort order) ─────────────
    tier_order = ["Efficient", "Moderate", "Inefficient", "Critical"]
    era_order  = ["Pre-1940", "1940–1979", "1980–1999", "2000–Present", "Unknown"]

    df["efficiency_tier"]  = pd.Categorical(df["efficiency_tier"],
                                            categories=tier_order, ordered=True)
    df["construction_era"] = pd.Categorical(df["construction_era"],
                                            categories=era_order,  ordered=True)

    # ── Output ─────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info(f"Saved processed file → {output_path}")

    return df


def print_summary(df: pd.DataFrame):
    print("\n── Processed Dataset Summary ────────────────────────────────────")
    print(f"  Total buildings  : {len(df):,}")
    print(f"  Avg EUI          : {df['eui'].mean():.1f} kBtu/sq ft")
    print(f"  Median EUI       : {df['eui'].median():.1f} kBtu/sq ft")
    print(f"\n  Efficiency tier breakdown:")
    tier_counts = df["efficiency_tier"].value_counts().sort_index()
    for tier, cnt in tier_counts.items():
        pct = cnt / len(df) * 100
        print(f"    {tier:<15} {cnt:>6,}  ({pct:.1f}%)")
    print(f"\n  Borough avg EUI:")
    print(df.groupby("borough")["eui"].mean().sort_values(ascending=False)
            .round(1).to_string())
    print("─────────────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    df_processed = run_pipeline(INPUT_FILE, OUTPUT_FILE)
    print_summary(df_processed)
