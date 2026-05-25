"""
Phase 3 Q3: 3-scenario Medicare Part D GLP-1 spend forecast, 2024-2027.

Diabetes-indicated GLP-1s only (Ozempic, Mounjaro, Trulicity, Rybelsus,
Victoza, Bydureon, Byetta). Wegovy/Saxenda/Zepbound are statutorily
excluded from Part D and enter only via the obesity-expansion scenario.

Three policy scenarios:
  1. Status quo       -- current adoption with brand-specific deceleration
  2. Obesity coverage -- statute changes; Part D adds Wegovy/Zepbound from 2025
  3. IRA negotiation  -- Ozempic gets 30% IRA-negotiated price cut from 2026

Outputs:
  docs/sql_outputs/phase3_q3_glp1_forecast.csv
  docs/sql_outputs/phase3_q3_glp1_forecast.png

Usage (from project root):
  python src/forecast_glp1.py
"""
from pathlib import Path

import duckdb
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "partd.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "sql_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Load historical GLP-1 (diabetes-indicated) spend
# ---------------------------------------------------------------------------
HIST_QUERY = """
WITH glp1 AS (
    SELECT
        CASE
            WHEN UPPER(Brnd_Name) LIKE 'VICTOZA%'  THEN 'Victoza'
            WHEN UPPER(Brnd_Name) LIKE 'BYDUREON%' THEN 'Bydureon'
            ELSE Brnd_Name
        END AS parent_brand,
        CAST(year AS INTEGER) AS year,
        Tot_Spndng
    FROM partd_long
    WHERE Mftr_Name = 'Overall'
      AND LOWER(Gnrc_Name) IN (
          'semaglutide', 'tirzepatide', 'dulaglutide',
          'liraglutide', 'exenatide', 'exenatide microspheres'
      )
      AND UPPER(Brnd_Name) NOT LIKE 'WEGOVY%'
      AND UPPER(Brnd_Name) NOT LIKE 'SAXENDA%'
      AND UPPER(Brnd_Name) NOT LIKE 'ZEPBOUND%'
)
SELECT parent_brand, year, SUM(Tot_Spndng) AS spend
FROM glp1
GROUP BY parent_brand, year
ORDER BY parent_brand, year;
"""

con = duckdb.connect(str(DB_PATH), read_only=True)
hist = con.execute(HIST_QUERY).fetchdf()
con.close()


# ---------------------------------------------------------------------------
# 2. Brand-specific projection parameters (status quo scenario)
#    (start_2024_yoy_pct, decay_factor_applied_to_growth_each_subsequent_year)
# ---------------------------------------------------------------------------
PARAMS = {
    'Ozempic':   ( 70.0, 0.70),   # peak GLP-1, decel from 99% in 2023
    'Mounjaro':  (150.0, 0.40),   # post-launch decel from 1539% (2023)
    'Trulicity': (  5.0, 0.50),   # plateau; cannibalized by Ozempic/Mounjaro
    'Rybelsus':  ( 45.0, 0.65),   # oral semaglutide, growing fast from smaller base
    'Victoza':   (-15.0, 1.00),   # continues declining
    'Bydureon':  (-20.0, 1.00),   # legacy, fading
    'Byetta':    (-25.0, 1.00),   # twice-daily, clinically obsolete
}


def project_brand(brand_history, start_yoy, decay, years=(2024, 2025, 2026, 2027)):
    """Project one brand's annual spend with decaying YoY growth."""
    last_year = brand_history['year'].max()
    spend = brand_history.loc[brand_history['year'] == last_year, 'spend'].iloc[0]
    yoy = start_yoy
    rows = []
    for y in years:
        spend *= (1 + yoy / 100.0)
        rows.append({'year': y, 'spend': spend, 'yoy_applied': yoy})
        yoy *= decay
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. Scenarios
# ---------------------------------------------------------------------------
def scenario_status_quo(hist_df, params):
    rows = []
    for brand in hist_df['parent_brand'].unique():
        if brand not in params:
            continue
        brand_hist = hist_df[hist_df['parent_brand'] == brand]
        start_yoy, decay = params[brand]
        proj = project_brand(brand_hist, start_yoy, decay)
        for _, r in proj.iterrows():
            rows.append({'brand': brand, 'year': int(r['year']), 'spend': r['spend']})
    return pd.DataFrame(rows)


def scenario_obesity_expansion(status_quo_df):
    """
    Status quo + Wegovy/Zepbound newly Part D-covered from 2025.
    Assumptions:
      - Eligible Medicare population (T2D + obese, BMI 30+ seeking treatment): ~4M
      - Net price per patient/year post-rebate: ~$9,000
      - Uptake: 0% 2024, 3% 2025, 8% 2026, 18% 2027
    """
    eligible = 4_000_000
    net_cost = 9_000
    uptake = {2024: 0.00, 2025: 0.03, 2026: 0.08, 2027: 0.18}
    added = pd.DataFrame([
        {'brand': 'Wegovy/Zepbound (new coverage)',
         'year': y, 'spend': eligible * uptake[y] * net_cost}
        for y in (2024, 2025, 2026, 2027)
    ])
    return pd.concat([status_quo_df, added], ignore_index=True)


def scenario_ira_negotiation(status_quo_df, price_cut=0.30, volume_rebound=0.05):
    """
    Hypothetical: Ozempic selected for IRA negotiation, Maximum Fair Price
    in effect from 2026. Standard 30% price reduction; small volume rebound
    as out-of-pocket burden drops.
    """
    df = status_quo_df.copy()
    mask = (df['brand'] == 'Ozempic') & (df['year'] >= 2026)
    df.loc[mask, 'spend'] *= (1 - price_cut) * (1 + volume_rebound)
    return df


# ---------------------------------------------------------------------------
# 4. Build outputs
# ---------------------------------------------------------------------------
sq = scenario_status_quo(hist, PARAMS)
obesity = scenario_obesity_expansion(sq)
ira = scenario_ira_negotiation(sq)


def summarize(projection, scenario_name):
    g = projection.groupby('year')['spend'].sum().reset_index()
    g['spend_b'] = (g['spend'] / 1e9).round(2)
    g['scenario'] = scenario_name
    return g[['scenario', 'year', 'spend_b']]


hist_summary = (
    hist.groupby('year')['spend'].sum() / 1e9
).reset_index().rename(columns={'spend': 'spend_b'})
hist_summary['scenario'] = 'Historical'
hist_summary['spend_b'] = hist_summary['spend_b'].round(2)
hist_summary = hist_summary[['scenario', 'year', 'spend_b']]

combined = pd.concat([
    hist_summary,
    summarize(sq, '1. Status quo'),
    summarize(obesity, '2. Obesity coverage'),
    summarize(ira, '3. IRA negotiation'),
], ignore_index=True)

pivot = combined.pivot_table(index='year', columns='scenario', values='spend_b')

print("\n=== GLP-1 (Diabetes-Indicated) Part D Spend Forecast, $B ===\n")
print(pivot.to_string())

csv_path = OUTPUT_DIR / 'phase3_q3_glp1_forecast.csv'
pivot.to_csv(csv_path)
print(f"\nSaved CSV:   {csv_path.relative_to(PROJECT_ROOT)}")


# ---------------------------------------------------------------------------
# 5. Chart
# ---------------------------------------------------------------------------
plt.figure(figsize=(11, 6.5))

plt.plot(hist_summary['year'], hist_summary['spend_b'],
         marker='o', linewidth=2.5, color='black', label='Historical')

bridge_year = 2023
bridge_value = hist_summary[hist_summary['year'] == bridge_year]['spend_b'].iloc[0]

for name, df_sc, color in [
    ('1. Status quo',       sq,      '#1f77b4'),
    ('2. Obesity coverage', obesity, '#2ca02c'),
    ('3. IRA negotiation',  ira,     '#d62728'),
]:
    s = df_sc.groupby('year')['spend'].sum() / 1e9
    plt.plot([bridge_year] + list(s.index),
             [bridge_value] + list(s.values),
             marker='o', linewidth=2, color=color, label=name)

plt.axvline(x=2023.5, color='gray', linestyle='--', alpha=0.5)
plt.title('Medicare Part D GLP-1 (Diabetes-Indicated) Spend\n'
          'Historical 2019-2023 + 3 Forecast Scenarios 2024-2027',
          fontsize=12)
plt.xlabel('Year')
plt.ylabel('Annual Spend ($B)')
plt.legend(loc='upper left', fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()

png_path = OUTPUT_DIR / 'phase3_q3_glp1_forecast.png'
plt.savefig(png_path, dpi=120)
plt.close()
print(f"Saved chart: {png_path.relative_to(PROJECT_ROOT)}")