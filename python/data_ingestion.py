"""
data_ingestion.py
=================
Fetches NYC Local Law 84 (LL84) Benchmarking data from the NYC Open Data API
(Socrata), performs initial cleaning, and saves a standardized CSV for
downstream feature engineering.

Author : Ruthvik Mandala
Source : https://data.cityofnewyork.us/resource/vdzd-yy49.json
"""

import requests
import pandas as pd
import os
import logging
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL   = "https://data.cityofnewyork.us/resource/vdzd-yy49.json"
LIMIT      = 10000           # Socrata page size (max 50 000 per call)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "nyc_housing_benchmarking_raw.csv")

COLUMNS_NEEDED = [
    "property_name",
    "address_1_self_reported",
    "borough",
    "property_gfa_self_reported_ft",
    "site_eui_kbtu_ft",
    "weather_normalized_site_eui_kbtu_ft",
    "site_energy_use_kbtu",
    "year_built",
    "primary_property_type_self_selected",
    "reported_benchmarking_year",
    "latitude",
    "longitude",
]

RENAME_MAP = {
    "address_1_self_reported"               : "address",
    "property_gfa_self_reported_ft"         : "gross_floor_area_sqft",
    "site_eui_kbtu_ft"                      : "site_eui_kbtu_ft",
    "weather_normalized_site_eui_kbtu_ft"   : "weather_norm_eui",
    "year_built"                            : "construction_year",
    "primary_property_type_self_selected"   : "building_type",
    "reported_benchmarking_year"            : "reporting_year",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch_page(offset: int) -> list[dict]:
    """Pull one page of records from the Socrata API."""
    params = {
        "$limit" : LIMIT,
        "$offset": offset,
        "$select": ",".join(COLUMNS_NEEDED),
    }
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_all_records() -> pd.DataFrame:
    """Paginate through the full dataset and return a combined DataFrame."""
    all_records = []
    offset = 0

    log.info("Starting data fetch from NYC Open Data …")
    while True:
        log.info(f"  Fetching rows {offset} – {offset + LIMIT - 1}")
        page = fetch_page(offset)
        if not page:
            break
        all_records.extend(page)
        offset += LIMIT
        if len(page) < LIMIT:
            break   # last page

    log.info(f"Total records fetched: {len(all_records):,}")
    return pd.DataFrame(all_records)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns, coerce types, and drop unusable rows."""
    df = df.rename(columns=RENAME_MAP)

    # Coerce numerics
    numeric_cols = [
        "gross_floor_area_sqft",
        "site_eui_kbtu_ft",
        "weather_norm_eui",
        "site_energy_use_kbtu",
        "construction_year",
        "reporting_year",
        "latitude",
        "longitude",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalise borough names
    borough_map = {
        "Manhattan"   : "Manhattan",
        "MANHATTAN"   : "Manhattan",
        "Brooklyn"    : "Brooklyn",
        "BROOKLYN"    : "Brooklyn",
        "Bronx"       : "Bronx",
        "BRONX"       : "Bronx",
        "Queens"      : "Queens",
        "QUEENS"      : "Queens",
        "Staten Island": "Staten Island",
        "STATEN ISLAND": "Staten Island",
    }
    if "borough" in df.columns:
        df["borough"] = df["borough"].map(borough_map).fillna(df["borough"])

    # Drop rows missing the two columns we can't impute
    before = len(df)
    df = df.dropna(subset=["gross_floor_area_sqft", "site_energy_use_kbtu"])
    df = df[df["gross_floor_area_sqft"] > 0]
    df = df[df["site_energy_use_kbtu"]  > 0]
    log.info(f"Dropped {before - len(df):,} rows with missing/zero energy data.")

    # Strip whitespace from string fields
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    return df.reset_index(drop=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df_raw   = fetch_all_records()
    df_clean = clean_dataframe(df_raw)

    df_clean.to_csv(OUTPUT_FILE, index=False)
    log.info(f"Saved {len(df_clean):,} clean rows → {OUTPUT_FILE}")

    # Quick summary
    print("\n── Dataset Summary ──────────────────────────────")
    print(f"  Rows   : {len(df_clean):,}")
    print(f"  Columns: {len(df_clean.columns)}")
    if "borough" in df_clean.columns:
        print(f"\n  Buildings per borough:")
        print(df_clean["borough"].value_counts().to_string())
    print("─────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
