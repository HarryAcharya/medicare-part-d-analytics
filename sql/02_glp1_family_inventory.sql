-- GLP-1 family inventory and 5-year spend trajectory.
-- Catalogs every GLP-1 in the dataset and shows the spend curve in millions.
-- Splits diabetes-indicated (Part D covered) from obesity-indicated (statutorily excluded).
--
-- All aggregates use Mftr_Name = 'Overall' to avoid double-counting,
-- per the grain finding from 01_glp1_obesity_probe.sql.
--
-- Technique: conditional aggregation. SUM(CASE WHEN year = 'YYYY' THEN ...)
-- collapses multiple year-rows per drug into one wide row with year-columns --
-- the inverse of the wide-to-long unpivot done in Phase 1.

SELECT
    Brnd_Name,
    Gnrc_Name,
    CASE
        WHEN UPPER(Brnd_Name) IN ('WEGOVY', 'SAXENDA', 'ZEPBOUND')
            THEN 'obesity (excluded)'
        ELSE 'diabetes (covered)'
    END AS indication,
    ROUND(SUM(CASE WHEN year = '2019' THEN Tot_Spndng END) / 1e6, 1) AS spend_2019_m,
    ROUND(SUM(CASE WHEN year = '2020' THEN Tot_Spndng END) / 1e6, 1) AS spend_2020_m,
    ROUND(SUM(CASE WHEN year = '2021' THEN Tot_Spndng END) / 1e6, 1) AS spend_2021_m,
    ROUND(SUM(CASE WHEN year = '2022' THEN Tot_Spndng END) / 1e6, 1) AS spend_2022_m,
    ROUND(SUM(CASE WHEN year = '2023' THEN Tot_Spndng END) / 1e6, 1) AS spend_2023_m
FROM partd_long
WHERE Mftr_Name = 'Overall'
  AND UPPER(Brnd_Name) IN (
      'OZEMPIC', 'WEGOVY', 'RYBELSUS',          -- semaglutide
      'MOUNJARO', 'ZEPBOUND',                    -- tirzepatide
      'TRULICITY',                               -- dulaglutide
      'VICTOZA', 'SAXENDA',                      -- liraglutide
      'BYETTA', 'BYDUREON', 'BYDUREON BCISE'    -- exenatide
  )
GROUP BY Brnd_Name, Gnrc_Name, indication
ORDER BY indication, Brnd_Name;