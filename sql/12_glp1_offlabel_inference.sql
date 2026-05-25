-- Phase 3 Q2: Off-label inference signals.
--
-- For each diabetes-indicated GLP-1 brand, traces beneficiary-count growth
-- against the implied Medicare diabetic population growth ceiling (~4-5%/yr,
-- per CMS Chronic Conditions Data Warehouse).
--
-- If a brand's bene-count growth dramatically exceeds 5%/yr -- and other
-- GLP-1s aren't declining by an offsetting amount (which would indicate
-- pure intra-class migration) -- the excess growth is the off-label
-- inference signal.
--
-- Per-bene metrics also surfaced:
--   * spend_per_bene  -- avg annual Part D spend per patient on the brand
--   * claims_per_bene -- avg Rx fills per patient per year (~12 = monthly)
--   * benes_yoy_pct   -- year-over-year growth in bene count vs ~4-5% ceiling
--
-- Wegovy / Saxenda / Zepbound excluded (obesity-indicated; covered separately).
-- Parent-brand normalization: Victoza variants and Bydureon variants rolled up.
-- Mftr_Name = 'Overall' filter applied per the Phase 1 grain finding.

WITH glp1_diabetes AS (
    SELECT
        CASE
            WHEN UPPER(Brnd_Name) LIKE 'VICTOZA%'  THEN 'Victoza'
            WHEN UPPER(Brnd_Name) LIKE 'BYDUREON%' THEN 'Bydureon'
            ELSE Brnd_Name
        END AS parent_brand,
        year,
        Tot_Spndng,
        Tot_Clms,
        Tot_Benes
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
      AND LOWER(Gnrc_Name) IN (
          'semaglutide', 'tirzepatide', 'dulaglutide',
          'liraglutide', 'exenatide', 'exenatide microspheres'
      )
      AND UPPER(Brnd_Name) NOT LIKE 'WEGOVY%'
      AND UPPER(Brnd_Name) NOT LIKE 'SAXENDA%'
      AND UPPER(Brnd_Name) NOT LIKE 'ZEPBOUND%'
),
aggregated AS (
    SELECT
        parent_brand,
        year,
        SUM(Tot_Spndng) AS spend,
        SUM(Tot_Clms)   AS claims,
        SUM(Tot_Benes)  AS benes
    FROM glp1_diabetes
    GROUP BY parent_brand, year
)
SELECT
    parent_brand,
    year,
    ROUND(spend / 1e9, 2)                                                AS spend_b,
    benes,
    ROUND(spend / NULLIF(benes, 0), 0)                                   AS spend_per_bene,
    ROUND(claims / NULLIF(benes, 0), 1)                                  AS claims_per_bene,
    ROUND(100.0 * (benes - LAG(benes) OVER (PARTITION BY parent_brand ORDER BY year))
              / NULLIF(LAG(benes) OVER (PARTITION BY parent_brand ORDER BY year), 0), 1)
                                                                          AS benes_yoy_pct
FROM aggregated
WHERE benes IS NOT NULL
ORDER BY parent_brand, year;