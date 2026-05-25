-- Phase 2 Q4: Brand vs Generic share & GDR opportunity (2023).
--
-- GDR (Generic Dispense Rate) = generic_claims / total_claims for a molecule.
-- Headline PBM metric: when a generic is available, what % of fills go to
-- the lower-cost version? Plan sponsors target GDR >= 90%.
--
-- Methodology: a row is treated as "generic" when Brnd_Name = Gnrc_Name
-- (CMS lists generics under the molecule's chemical name). All other rows
-- are treated as branded.
--
-- Limitation: biologic biosimilars (Humira's Cyltezo, Hyrimoz, etc.) appear
-- as distinct brand names rather than under the generic ingredient, so the
-- biosimilar savings opportunity is NOT captured here. Requires separate
-- purpose-built query.
--
-- Focus: molecules where BOTH brand and generic exist in 2023 with >$100M
-- total spend, sorted by absolute brand $$$. These are the actionable
-- opportunities -- big branded dollars where a cheaper alternative already
-- sits on the formulary.
--
-- Mftr_Name = 'Overall' filter applied per Phase 1 grain finding.

WITH per_molecule AS (
    SELECT
        Gnrc_Name,
        SUM(CASE WHEN Brnd_Name = Gnrc_Name
                 THEN Tot_Spndng ELSE 0 END)             AS generic_spend,
        SUM(CASE WHEN Brnd_Name = Gnrc_Name
                 THEN Tot_Clms ELSE 0 END)               AS generic_claims,
        SUM(CASE WHEN Brnd_Name <> Gnrc_Name
                 THEN Tot_Spndng ELSE 0 END)             AS brand_spend,
        SUM(CASE WHEN Brnd_Name <> Gnrc_Name
                 THEN Tot_Clms ELSE 0 END)               AS brand_claims,
        COUNT(DISTINCT CASE WHEN Brnd_Name <> Gnrc_Name
                            THEN Brnd_Name END)          AS distinct_brands
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
      AND year = '2023'
      AND Tot_Spndng IS NOT NULL
    GROUP BY Gnrc_Name
)
SELECT
    Gnrc_Name,
    distinct_brands,
    ROUND((brand_spend + generic_spend) / 1e6, 1)                       AS total_spend_m,
    ROUND(brand_spend / 1e6, 1)                                         AS brand_spend_m,
    ROUND(generic_spend / 1e6, 1)                                       AS generic_spend_m,
    ROUND(100.0 * generic_claims / (generic_claims + brand_claims), 1)  AS gdr_pct,
    ROUND(100.0 * brand_spend / (brand_spend + generic_spend), 1)       AS brand_spend_share_pct
FROM per_molecule
WHERE brand_spend > 0
  AND generic_spend > 0
  AND (brand_spend + generic_spend) > 100e6   -- materiality threshold: >$100M total 2023
ORDER BY brand_spend DESC
LIMIT 20;