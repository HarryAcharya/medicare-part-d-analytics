-- GLP-1 family inventory, normalized at parent-brand level.
--
-- Improvements over 02_glp1_family_inventory.sql:
--   * Filters by Gnrc_Name (molecule) instead of brand-name list - catches
--     variants like 'Victoza 2-Pak', 'Bydureon Pen' without prior knowledge.
--   * CTE rolls up brand variants to parent brand
--     (Victoza 2-Pak + 3-Pak -> Victoza, Bydureon Bcise + Pen -> Bydureon)
--     to match clinical/prescriber-level rollup.
--   * Indication classified at parent-brand level
--     (preserves Wegovy/Saxenda/Zepbound vs Ozempic/Trulicity/etc. split).
--
-- Mftr_Name = 'Overall' filter applied per the grain finding from 01.

WITH glp1_normalized AS (
    SELECT
        CASE
            WHEN UPPER(Brnd_Name) LIKE 'VICTOZA%'  THEN 'Victoza'
            WHEN UPPER(Brnd_Name) LIKE 'BYDUREON%' THEN 'Bydureon'
            ELSE Brnd_Name
        END AS parent_brand,
        Gnrc_Name,
        year,
        Tot_Spndng,
        CASE
            WHEN UPPER(Brnd_Name) LIKE 'WEGOVY%'   THEN 'obesity (excluded)'
            WHEN UPPER(Brnd_Name) LIKE 'SAXENDA%'  THEN 'obesity (excluded)'
            WHEN UPPER(Brnd_Name) LIKE 'ZEPBOUND%' THEN 'obesity (excluded)'
            ELSE 'diabetes (covered)'
        END AS indication
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
      AND LOWER(Gnrc_Name) IN (
          'semaglutide',
          'tirzepatide',
          'dulaglutide',
          'liraglutide',
          'exenatide',
          'exenatide microspheres'
      )
)
SELECT
    parent_brand,
    Gnrc_Name,
    indication,
    ROUND(SUM(CASE WHEN year = '2019' THEN Tot_Spndng END) / 1e6, 1) AS spend_2019_m,
    ROUND(SUM(CASE WHEN year = '2020' THEN Tot_Spndng END) / 1e6, 1) AS spend_2020_m,
    ROUND(SUM(CASE WHEN year = '2021' THEN Tot_Spndng END) / 1e6, 1) AS spend_2021_m,
    ROUND(SUM(CASE WHEN year = '2022' THEN Tot_Spndng END) / 1e6, 1) AS spend_2022_m,
    ROUND(SUM(CASE WHEN year = '2023' THEN Tot_Spndng END) / 1e6, 1) AS spend_2023_m
FROM glp1_normalized
GROUP BY parent_brand, Gnrc_Name, indication
ORDER BY indication, parent_brand;