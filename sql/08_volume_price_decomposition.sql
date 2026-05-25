-- Phase 2 Q3: Volume x Price decomposition of Part D growth 2019-2023.
--
-- THE KILLER QUERY. Partitions the +$97B Part D gross-spend increase into:
--   * Volume effect    delta_Claims * Price_2019         (more Rx at 2019 prices)
--   * Price effect     Claims_2019  * delta_Price        (2019 volume at 2023 prices)
--   * Interaction      delta_Claims * delta_Price        (cross term, both moving)
--
-- Math: Spend = Volume x AvgPrice (per claim).
--   d(Spend) = d(V) * P_2019 + V_2019 * d(P) + d(V) * d(P)
--            = Volume_effect + Price_effect + Interaction
--   Closes exactly to total growth -- no residual.
--
-- INTERPRETATION CAVEAT: 'Price effect' here uses portfolio-weighted average
-- price per claim, which conflates TRUE UNIT-PRICE INFLATION with MIX SHIFT
-- (patients moving to pricier drugs). To separate the two cleanly requires
-- per-drug Laspeyres indexing -- see Q3b (forthcoming) for that drilldown.
--
-- Mftr_Name = 'Overall' filter applied per Phase 1 grain finding.

WITH yearly AS (
    SELECT
        year,
        SUM(Tot_Spndng)                  AS total_spend,
        SUM(Tot_Clms)                    AS total_claims,
        SUM(Tot_Spndng) / SUM(Tot_Clms)  AS avg_price_per_claim
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
    GROUP BY year
),
bookends AS (
    SELECT
        MAX(CASE WHEN year = '2019' THEN total_spend END)         AS spend_2019,
        MAX(CASE WHEN year = '2023' THEN total_spend END)         AS spend_2023,
        MAX(CASE WHEN year = '2019' THEN total_claims END)        AS claims_2019,
        MAX(CASE WHEN year = '2023' THEN total_claims END)        AS claims_2023,
        MAX(CASE WHEN year = '2019' THEN avg_price_per_claim END) AS price_2019,
        MAX(CASE WHEN year = '2023' THEN avg_price_per_claim END) AS price_2023
    FROM yearly
),
decomp AS (
    SELECT
        spend_2019,
        spend_2023,
        spend_2023 - spend_2019                                  AS total_growth,
        (claims_2023 - claims_2019) * price_2019                 AS volume_effect,
        claims_2019 * (price_2023 - price_2019)                  AS price_effect,
        (claims_2023 - claims_2019) * (price_2023 - price_2019)  AS interaction
    FROM bookends
),
report AS (
    SELECT 1 AS ord,
           'Spend 2019 ($B)' AS metric,
           ROUND(spend_2019 / 1e9, 2) AS value_b,
           NULL::DOUBLE AS pct_of_growth
    FROM decomp
    UNION ALL
    SELECT 2, 'Spend 2023 ($B)',
           ROUND(spend_2023 / 1e9, 2), NULL
    FROM decomp
    UNION ALL
    SELECT 3, 'Total growth 2019->2023 ($B)',
           ROUND((spend_2023 - spend_2019) / 1e9, 2), 100.0
    FROM decomp
    UNION ALL
    SELECT 4, '  Volume effect ($B)   [more Rx at 2019 prices]',
           ROUND(volume_effect / 1e9, 2),
           ROUND(100.0 * volume_effect / total_growth, 1)
    FROM decomp
    UNION ALL
    SELECT 5, '  Price effect ($B)    [2019 Rx at 2023 prices; incl. mix shift]',
           ROUND(price_effect / 1e9, 2),
           ROUND(100.0 * price_effect / total_growth, 1)
    FROM decomp
    UNION ALL
    SELECT 6, '  Interaction ($B)     [growth in both V and P simultaneously]',
           ROUND(interaction / 1e9, 2),
           ROUND(100.0 * interaction / total_growth, 1)
    FROM decomp
)
SELECT metric, value_b, pct_of_growth
FROM report
ORDER BY ord;