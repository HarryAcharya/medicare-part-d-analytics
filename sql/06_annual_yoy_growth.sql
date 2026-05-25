-- Phase 2 Q1: Annual Part D totals with year-over-year growth.
--
-- Demonstrates window functions (LAG OVER ORDER BY) -- the 4th of 4 core
-- SQL techniques targeted alongside CTEs, conditional aggregation, and
-- FILTER clauses.
--
-- Derives spend-per-claim (average dollar value per Rx fill), the single
-- cleanest signal of unit-cost growth plus mix shift.
--
-- Mftr_Name = 'Overall' filter applied per the grain finding from Phase 1.
-- 2019 row will show NULL YoY columns -- expected (no prior year to compare).

WITH annual AS (
    SELECT
        year,
        SUM(Tot_Spndng) AS total_spend,
        SUM(Tot_Clms)   AS total_claims
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
    GROUP BY year
),
with_lag AS (
    SELECT
        year,
        total_spend,
        total_claims,
        total_spend / total_claims                            AS spend_per_claim,
        LAG(total_spend)                OVER (ORDER BY year)  AS prior_spend,
        LAG(total_claims)               OVER (ORDER BY year)  AS prior_claims,
        LAG(total_spend / total_claims) OVER (ORDER BY year)  AS prior_spc
    FROM annual
)
SELECT
    year,
    ROUND(total_spend / 1e9, 2)                                          AS spend_billions,
    ROUND(100.0 * (total_spend  - prior_spend)  / prior_spend,  1)       AS spend_yoy_pct,
    ROUND(total_claims / 1e6, 2)                                         AS claims_millions,
    ROUND(100.0 * (total_claims - prior_claims) / prior_claims, 1)       AS claims_yoy_pct,
    ROUND(spend_per_claim, 2)                                            AS spend_per_claim,
    ROUND(100.0 * (spend_per_claim - prior_spc) / prior_spc, 1)          AS spend_per_claim_yoy_pct
FROM with_lag
ORDER BY year;