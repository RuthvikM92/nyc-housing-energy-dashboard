-- ============================================================
-- NYC Affordable Housing Energy Efficiency Analysis
-- Author: Ruthvik Mandala
-- Description: Core SQL queries for borough-level EUI analysis,
--              benchmarking, and retrofit prioritization
-- ============================================================


-- ============================================================
-- 1. ENERGY USE INTENSITY (EUI) BY BOROUGH
--    Aggregates average EUI per borough for dashboard KPIs
-- ============================================================
SELECT
    borough,
    COUNT(*)                                                        AS total_buildings,
    ROUND(AVG(site_energy_use_kbtu / gross_floor_area_sqft), 2)    AS avg_eui,
    ROUND(MIN(site_energy_use_kbtu / gross_floor_area_sqft), 2)    AS min_eui,
    ROUND(MAX(site_energy_use_kbtu / gross_floor_area_sqft), 2)    AS max_eui,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY site_energy_use_kbtu / gross_floor_area_sqft
    ), 2)                                                           AS median_eui
FROM nyc_housing_benchmarking
WHERE gross_floor_area_sqft > 0
  AND site_energy_use_kbtu IS NOT NULL
  AND site_energy_use_kbtu > 0
GROUP BY borough
ORDER BY avg_eui DESC;


-- ============================================================
-- 2. EFFICIENCY TIER DISTRIBUTION
--    Classifies all buildings into 4 tiers and counts per borough
-- ============================================================
WITH eui_calc AS (
    SELECT
        borough,
        property_name,
        address,
        building_type,
        construction_year,
        gross_floor_area_sqft,
        site_energy_use_kbtu,
        ROUND(site_energy_use_kbtu / gross_floor_area_sqft, 2) AS eui,
        CASE
            WHEN (site_energy_use_kbtu / gross_floor_area_sqft) > 150 THEN 'Critical'
            WHEN (site_energy_use_kbtu / gross_floor_area_sqft) > 100 THEN 'Inefficient'
            WHEN (site_energy_use_kbtu / gross_floor_area_sqft) > 75  THEN 'Moderate'
            ELSE 'Efficient'
        END AS efficiency_tier
    FROM nyc_housing_benchmarking
    WHERE gross_floor_area_sqft > 0
      AND site_energy_use_kbtu IS NOT NULL
      AND site_energy_use_kbtu > 0
)
SELECT
    borough,
    efficiency_tier,
    COUNT(*)                                AS building_count,
    ROUND(AVG(eui), 2)                      AS avg_eui_in_tier,
    ROUND(SUM(gross_floor_area_sqft), 0)    AS total_sqft
FROM eui_calc
GROUP BY borough, efficiency_tier
ORDER BY borough, 
    CASE efficiency_tier
        WHEN 'Critical'     THEN 1
        WHEN 'Inefficient'  THEN 2
        WHEN 'Moderate'     THEN 3
        WHEN 'Efficient'    THEN 4
    END;


-- ============================================================
-- 3. TOP 20 HIGHEST-PRIORITY RETROFIT CANDIDATES
--    Large footprint + high EUI = highest potential savings
-- ============================================================
SELECT
    property_name,
    address,
    borough,
    building_type,
    construction_year,
    gross_floor_area_sqft,
    ROUND(site_energy_use_kbtu / gross_floor_area_sqft, 2)  AS eui,
    ROUND(
        (site_energy_use_kbtu / gross_floor_area_sqft - 75)
        * gross_floor_area_sqft / 1000, 0
    )                                                        AS estimated_savings_kbtu_k,
    CASE
        WHEN (site_energy_use_kbtu / gross_floor_area_sqft) > 150 THEN 'Critical'
        WHEN (site_energy_use_kbtu / gross_floor_area_sqft) > 100 THEN 'Inefficient'
        WHEN (site_energy_use_kbtu / gross_floor_area_sqft) > 75  THEN 'Moderate'
        ELSE 'Efficient'
    END AS efficiency_tier
FROM nyc_housing_benchmarking
WHERE gross_floor_area_sqft > 50000          -- Focus on large buildings
  AND site_energy_use_kbtu IS NOT NULL
  AND site_energy_use_kbtu > 0
  AND gross_floor_area_sqft > 0
ORDER BY estimated_savings_kbtu_k DESC
LIMIT 20;


-- ============================================================
-- 4. EUI TREND BY REPORTING YEAR
--    Tracks portfolio-wide efficiency improvement over time
-- ============================================================
SELECT
    reporting_year,
    COUNT(*)                                                    AS buildings_reported,
    ROUND(AVG(site_energy_use_kbtu / gross_floor_area_sqft), 2) AS avg_eui,
    ROUND(
        100.0 * SUM(
            CASE WHEN (site_energy_use_kbtu / gross_floor_area_sqft) > 100
            THEN 1 ELSE 0 END
        ) / COUNT(*), 1
    )                                                           AS pct_above_threshold
FROM nyc_housing_benchmarking
WHERE gross_floor_area_sqft > 0
  AND site_energy_use_kbtu IS NOT NULL
  AND site_energy_use_kbtu > 0
GROUP BY reporting_year
ORDER BY reporting_year;


-- ============================================================
-- 5. BUILDING AGE vs. ENERGY PERFORMANCE
--    Quantifies how construction era impacts efficiency
-- ============================================================
SELECT
    CASE
        WHEN construction_year < 1940              THEN 'Pre-1940'
        WHEN construction_year BETWEEN 1940 AND 1979 THEN '1940–1979'
        WHEN construction_year BETWEEN 1980 AND 1999 THEN '1980–1999'
        WHEN construction_year >= 2000             THEN '2000–Present'
        ELSE 'Unknown'
    END AS construction_era,
    COUNT(*)                                                    AS building_count,
    ROUND(AVG(site_energy_use_kbtu / gross_floor_area_sqft), 2) AS avg_eui,
    ROUND(AVG(gross_floor_area_sqft), 0)                        AS avg_sqft
FROM nyc_housing_benchmarking
WHERE gross_floor_area_sqft > 0
  AND site_energy_use_kbtu IS NOT NULL
  AND site_energy_use_kbtu > 0
  AND construction_year IS NOT NULL
GROUP BY construction_era
ORDER BY
    CASE construction_era
        WHEN 'Pre-1940'     THEN 1
        WHEN '1940–1979'    THEN 2
        WHEN '1980–1999'    THEN 3
        WHEN '2000–Present' THEN 4
        ELSE 5
    END;


-- ============================================================
-- 6. BUILDING TYPE EFFICIENCY SUMMARY
--    Compares EUI across residential, mixed-use, commercial, etc.
-- ============================================================
SELECT
    building_type,
    COUNT(*)                                                    AS building_count,
    ROUND(AVG(site_energy_use_kbtu / gross_floor_area_sqft), 2) AS avg_eui,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY site_energy_use_kbtu / gross_floor_area_sqft
    ), 2)                                                       AS median_eui,
    ROUND(SUM(gross_floor_area_sqft) / 1e6, 2)                 AS total_sqft_millions
FROM nyc_housing_benchmarking
WHERE gross_floor_area_sqft > 0
  AND site_energy_use_kbtu IS NOT NULL
  AND site_energy_use_kbtu > 0
GROUP BY building_type
HAVING COUNT(*) >= 50
ORDER BY avg_eui DESC;
