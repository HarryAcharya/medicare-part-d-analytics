-- Phase 3 Q1: GLP-1 conversion rate -- share of Part D diabetes spend
-- that's now flowing to GLP-1 receptor agonists.
--
-- Buckets diabetes drugs into 4 mutually exclusive classes:
--   1. GLP-1 (diabetes-indicated only -- excludes Wegovy/Saxenda/Zepbound)
--   2. SGLT-2 inhibitors
--   3. Insulins
--   4. Other oral (metformin, DPP-4s, sulfonylureas, TZDs)
--
-- Then computes per-year totals and share. Establishes the headline:
-- "GLP-1s went from <X>% of diabetes spend in 2019 to <Y>% in 2023."
--
-- Mftr_Name = 'Overall' filter applied per Phase 1 grain finding.
-- Wegovy/Saxenda/Zepbound deliberately excluded (obesity-indicated;
-- statutorily not Part D drugs; tracked separately in 01_glp1_obesity_probe.sql).

WITH diabetes_classified AS (
    SELECT
        year,
        Tot_Spndng,
        CASE
            WHEN LOWER(Gnrc_Name) IN ('semaglutide', 'tirzepatide', 'dulaglutide',
                                      'liraglutide', 'exenatide', 'exenatide microspheres')
                 AND UPPER(Brnd_Name) NOT LIKE 'WEGOVY%'
                 AND UPPER(Brnd_Name) NOT LIKE 'SAXENDA%'
                 AND UPPER(Brnd_Name) NOT LIKE 'ZEPBOUND%'
                THEN 'GLP-1'
            WHEN LOWER(Gnrc_Name) IN ('empagliflozin', 'dapagliflozin propanediol',
                                      'dapagliflozin', 'canagliflozin',
                                      'ertugliflozin pidolate',
                                      'empagliflozin/metformin hcl',
                                      'empagliflozin/linagliptin')
                THEN 'SGLT-2'
            WHEN LOWER(Gnrc_Name) LIKE '%insulin%'
                THEN 'Insulin'
            WHEN LOWER(Gnrc_Name) LIKE 'sitagliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'linagliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'saxagliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'alogliptin%'
                 OR LOWER(Gnrc_Name) LIKE 'metformin%'
                 OR LOWER(Gnrc_Name) IN ('glipizide', 'glimepiride',
                                         'pioglitazone hcl', 'glyburide')
                THEN 'Other Oral'
            ELSE NULL  -- not a diabetes drug
        END AS diabetes_class
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
),
by_year AS (
    SELECT
        year,
        SUM(CASE WHEN diabetes_class = 'GLP-1'      THEN Tot_Spndng ELSE 0 END) AS glp1_spend,
        SUM(CASE WHEN diabetes_class = 'SGLT-2'     THEN Tot_Spndng ELSE 0 END) AS sglt2_spend,
        SUM(CASE WHEN diabetes_class = 'Insulin'    THEN Tot_Spndng ELSE 0 END) AS insulin_spend,
        SUM(CASE WHEN diabetes_class = 'Other Oral' THEN Tot_Spndng ELSE 0 END) AS other_oral_spend,
        SUM(CASE WHEN diabetes_class IS NOT NULL    THEN Tot_Spndng ELSE 0 END) AS total_diabetes
    FROM diabetes_classified
    GROUP BY year
)
SELECT
    year,
    ROUND(total_diabetes   / 1e9, 2)                            AS total_diab_b,
    ROUND(glp1_spend       / 1e9, 2)                            AS glp1_b,
    ROUND(100.0 * glp1_spend       / total_diabetes, 1)         AS glp1_pct,
    ROUND(sglt2_spend      / 1e9, 2)                            AS sglt2_b,
    ROUND(100.0 * sglt2_spend      / total_diabetes, 1)         AS sglt2_pct,
    ROUND(insulin_spend    / 1e9, 2)                            AS insulin_b,
    ROUND(100.0 * insulin_spend    / total_diabetes, 1)         AS insulin_pct,
    ROUND(other_oral_spend / 1e9, 2)                            AS other_b,
    ROUND(100.0 * other_oral_spend / total_diabetes, 1)         AS other_pct
FROM by_year
ORDER BY year;