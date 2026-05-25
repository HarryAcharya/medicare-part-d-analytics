-- Phase 2 Q2: Top 25 Part D drugs by 2023 spend, with growth rates.
--
-- Demonstrates RANK() window function for ordering, combined with
-- conditional aggregation to pivot annual values into per-drug columns.
--
-- Data caveat: drugs appear as CMS brand names (NDC level). Some are
-- sold under multiple package-size variants (e.g. Victoza 2-Pak vs 3-Pak)
-- and will appear separately. For ranking purposes this is acceptable;
-- clinical rollup is handled in the dedicated GLP-1 analysis file
-- (sql/04_glp1_family_normalized.sql).
--
-- NULL growth columns expected for drugs launched mid-window
-- (e.g. Mounjaro: spend_2019 IS NULL, so five_yr_pct = NULL).
--
-- Mftr_Name = 'Overall' filter applied per the Phase 1 grain finding.

WITH pivoted AS (
    SELECT
        Brnd_Name,
        MAX(Gnrc_Name)                                       AS Gnrc_Name,
        MAX(CASE WHEN year = '2023' THEN Tot_Spndng END)     AS spend_2023,
        MAX(CASE WHEN year = '2022' THEN Tot_Spndng END)     AS spend_2022,
        MAX(CASE WHEN year = '2019' THEN Tot_Spndng END)     AS spend_2019
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
    GROUP BY Brnd_Name
),
ranked AS (
    SELECT
        Brnd_Name,
        Gnrc_Name,
        spend_2023,
        spend_2022,
        spend_2019,
        RANK() OVER (ORDER BY spend_2023 DESC NULLS LAST) AS rnk
    FROM pivoted
    WHERE spend_2023 IS NOT NULL
)
SELECT
    rnk,
    Brnd_Name,
    Gnrc_Name,
    ROUND(spend_2023 / 1e9, 2)                                   AS spend_2023_b,
    ROUND(spend_2022 / 1e9, 2)                                   AS spend_2022_b,
    ROUND(100.0 * (spend_2023 - spend_2022) / spend_2022, 1)     AS yoy_pct,
    ROUND(spend_2019 / 1e9, 2)                                   AS spend_2019_b,
    ROUND(100.0 * (spend_2023 - spend_2019) / spend_2019, 1)     AS five_yr_pct
FROM ranked
WHERE rnk <= 25
ORDER BY rnk;