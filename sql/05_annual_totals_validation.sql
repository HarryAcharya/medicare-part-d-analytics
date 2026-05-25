-- Annual Part D spending totals for CMS sanity check.
-- Expect to be a few percent LOW vs CMS published totals: the By-Drug file
-- suppresses drug-years with <11 beneficiaries, so suppressed spend is
-- excluded from SUM. A 20%+ shortfall would indicate an unpivot/join error.
--
-- Mftr_Name = 'Overall' filter applied per the grain finding from 01.

SELECT
    year,
    COUNT(*)                                              AS rows_total,
    COUNT(*) FILTER (WHERE Tot_Spndng IS NULL)            AS rows_suppressed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE Tot_Spndng IS NULL)
                / COUNT(*), 1)                             AS suppress_pct,
    ROUND(SUM(Tot_Spndng) / 1e9, 2)                       AS spend_billions,
    ROUND(SUM(Tot_Clms) / 1e6, 2)                         AS claims_millions
FROM partd_long
WHERE Mftr_Name = 'Overall'
GROUP BY year
ORDER BY year;