# Medicare Part D Drug Analytics — GLP-1 Deep-Dive

End-to-end analytics on five years of CMS Medicare Part D drug spending (2019–2023), with a dedicated investigation of GLP-1 receptor agonists — the drug class driving roughly **one in six dollars** of Part D growth.

**Status:** Phase 1 complete (foundation + GLP-1 baseline). Phases 2–7 in progress.

---

## Headline findings (Phase 1)

- **GLP-1 diabetes drugs** grew from **$5.3B to $22.2B** in Medicare Part D gross spending between 2019 and 2023 — a 4.2× increase, +$16.9B in annual spend.
- GLP-1s now represent **8.1% of all Part D spending** and account for **17.5% of total Part D spend growth** over the period.
- **Ozempic alone** contributed $8.6B of new annual spend over the five-year window — half of all GLP-1 growth.
- **Policy crack identified:** Wegovy — statutorily excluded from Part D coverage under Section 1860D-2(e)(2)(A) of the Social Security Act — recorded **$199,774 in Part D spending across 47 unique beneficiaries** in 2023, with 142 prescription fills. Likely mechanism: plan-level formulary exceptions and front-running of the cardiovascular indication that gained FDA approval in March 2024.

---

## Tech stack

- **SQL:** DuckDB 1.5.3 (in-process analytical SQL)
- **Python:** pandas, duckdb-py (SQL execution + reproducibility harness)
- **Visualization:** Power BI (Phase 4), Streamlit (Phase 5)
- **Source control:** git + GitHub

---

## Data source

[CMS Medicare Part D Spending by Drug, Reporting Year 2025](https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug)

- 14,309 drug-manufacturer combinations × 5 years = **71,545 long-format rows** after unpivot
- Annual gross-spending totals validated within **1.5%** of CMS published headline figures every year
- Suppression handled per CMS rules (<11 beneficiaries per drug-year = suppressed cell)

---

## Repository structure

---

## Phase roadmap

| Phase | Status | Scope |
|-------|--------|-------|
| 1. Foundation + GLP-1 baseline | ✅ Complete | Data load, schema reshape, GLP-1 family inventory, CMS validation |
| 2. Foundation SQL Analysis | ⏳ Next | YoY growth (window functions), top-25 drugs, volume × price decomposition, GDR opportunity |
| 3. GLP-1 Deep-Dive | ⏳ | Off-label inference, 3-scenario 2024–2027 forecast under policy variants |
| 4. Power BI Dashboard | ⏳ | 4-page interactive dashboard incl. dedicated GLP-1 page |
| 5. Streamlit App | ⏳ | Live web app with GLP-1 forecast simulator |
| 6. Memos + Polish | ⏳ | Executive memo (CFO), utilization memo (P&T committee) |
| 7. Interview prep | ⏳ | Talk track, resume bullets, LinkedIn post |

---

## SQL technique demonstrations

Phase 1 SQL files demonstrate the four core analytical SQL techniques expected of a senior data analyst:

| Technique | File |
|-----------|------|
| Schema introspection | `sql/00_describe_schema.sql` |
| Conditional aggregation (pivoting) | `sql/02_glp1_family_inventory.sql` |
| Discovery via molecule-level filtering | `sql/03_glp1_brand_discovery.sql` |
| CTEs + parent-brand normalization | `sql/04_glp1_family_normalized.sql` |
| `FILTER` clause + aggregate validation | `sql/05_annual_totals_validation.sql` |
| Window functions (LAG/LEAD) | Phase 2 (incoming) |
| Joins (FDA Orange Book layer) | Phase 3 (incoming) |

---

## Reproducing locally

```powershell
# 1. Clone
git clone https://github.com/HarryAcharya/medicare-part-d-analytics.git
cd medicare-part-d-analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download CMS source data
#    Get the latest Medicare Part D Spending by Drug Excel file from
#    https://data.cms.gov and place it in data/raw/

# 4. Build the DuckDB database
#    (Manual via DuckDB CLI for now; build_db.py script coming in Phase 6.)

# 5. Run any analytical query
python src/run_sql.py sql/04_glp1_family_normalized.sql

# 6. Regression-check the full Phase 1 baseline
python src/validate_phase1.py
```

---

## About

Built by [Hari Acharya](https://github.com/HarryAcharya) — analyst / data scientist focused on pharma, PBM, and payer applications. Chicago, IL.

- Email: acharyaharii95@gmail.com
- Tableau Public: https://public.tableau.com/app/profile/hari.acharya2369