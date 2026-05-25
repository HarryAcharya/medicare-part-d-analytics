-- GLP-1 obesity probe.
-- Per CMS statute (Social Security Act Section 1860D-2(e)(2)(A)),
-- Medicare Part D excludes drugs used for weight loss.
-- Wegovy (semaglutide), Saxenda (liraglutide), and Zepbound (tirzepatide)
-- were FDA-approved ONLY for obesity during our 2019-2023 window.
-- Any spend rows here are findings.
--
-- We include Mftr_Name to verify the grain of partd_long:
--   * one row per brand-year   -> grain is brand-generic-year, sums are safe.
--   * multiple rows per brand-year -> grain is brand-generic-mftr-year,
--     and we'll need a filter (typically Mftr_Name = 'Overall') before summing.

SELECT
    Brnd_Name,
    Gnrc_Name,
    Mftr_Name,
    year,
    Tot_Spndng,
    Tot_Clms,
    Tot_Benes
FROM partd_long
WHERE UPPER(Brnd_Name) IN ('WEGOVY', 'SAXENDA', 'ZEPBOUND')
ORDER BY Brnd_Name, year, Mftr_Name;