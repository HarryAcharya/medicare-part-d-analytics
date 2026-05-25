"""
Phase 1 validation: comprehensive go/no-go check before Phase 2.

Verifies database integrity, table grain, year coverage, suppression patterns,
GLP-1 family inventory, the Wegovy 2023 headline finding, annual totals vs
CMS published gross figures, GLP-1 trajectory and share of growth, and
existence of all SQL/CSV deliverables.

Usage (from project root):
    python src/validate_phase1.py
"""
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "partd.duckdb"
SQL_DIR = PROJECT_ROOT / "sql"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "sql_outputs"


def header(text):
    print()
    print("=" * 72)
    print(text)
    print("=" * 72)


def ok(check, detail=""):
    print(f"  [PASS] {check}" + (f"  -- {detail}" if detail else ""))


def fail(check, detail=""):
    print(f"  [FAIL] {check}" + (f"  -- {detail}" if detail else ""))


def warn(check, detail=""):
    print(f"  [WARN] {check}" + (f"  -- {detail}" if detail else ""))


def main():
    all_ok = True

    # ---- 1. Database file and tables ----
    header("1. Database and table integrity")
    if not DB_PATH.exists():
        fail("Database file exists", f"missing: {DB_PATH}")
        return 1
    ok("Database file exists", str(DB_PATH.relative_to(PROJECT_ROOT)))

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        for table in ["raw_wide", "partd_long"]:
            if table in tables:
                ok(f"Table '{table}' exists")
            else:
                fail(f"Table '{table}' exists")
                all_ok = False

        # ---- 2. Row counts and grain ----
        header("2. Row counts and grain")
        wide_count = con.execute("SELECT COUNT(*) FROM raw_wide").fetchone()[0]
        if wide_count == 14309:
            ok("raw_wide row count", f"{wide_count:,}")
        else:
            fail("raw_wide row count", f"expected 14,309, got {wide_count:,}")
            all_ok = False

        long_count = con.execute("SELECT COUNT(*) FROM partd_long").fetchone()[0]
        if long_count == 71545:
            ok("partd_long row count", f"{long_count:,}  (14,309 x 5 years)")
        else:
            fail("partd_long row count", f"expected 71,545, got {long_count:,}")
            all_ok = False

        years = sorted(r[0] for r in con.execute(
            "SELECT DISTINCT year FROM partd_long").fetchall())
        if years == ['2019', '2020', '2021', '2022', '2023']:
            ok("Year coverage", "2019-2023")
        else:
            fail("Year coverage", f"got {years}")
            all_ok = False

        overall_rows = con.execute(
            "SELECT COUNT(*) FROM partd_long WHERE Mftr_Name = 'Overall'"
        ).fetchone()[0]
        ok("Overall-grain row count", f"{overall_rows:,} (3,598 drugs x 5 years)")

        # ---- 3. Suppression ----
        header("3. Suppression patterns")
        total_suppressed = con.execute(
            "SELECT COUNT(*) FROM partd_long WHERE Tot_Spndng IS NULL"
        ).fetchone()[0]
        if 10500 <= total_suppressed <= 11500:
            ok("Total suppressed rows", f"{total_suppressed:,} (~15% of 71,545)")
        else:
            warn("Total suppressed rows",
                 f"{total_suppressed:,} (expected ~11,067)")

        # ---- 4. GLP-1 family ----
        header("4. GLP-1 family inventory (filtered by molecule)")
        glp1_brands = sorted(r[0] for r in con.execute("""
            SELECT DISTINCT Brnd_Name
            FROM partd_long
            WHERE LOWER(Gnrc_Name) IN (
                'semaglutide', 'tirzepatide', 'dulaglutide',
                'liraglutide', 'exenatide', 'exenatide microspheres'
            )
        """).fetchall())
        expected = {'Ozempic', 'Rybelsus', 'Wegovy', 'Mounjaro', 'Trulicity',
                    'Saxenda', 'Victoza 2-Pak', 'Victoza 3-Pak',
                    'Byetta', 'Bydureon Bcise', 'Bydureon Pen'}
        missing = expected - set(glp1_brands)
        if not missing:
            ok(f"All {len(expected)} expected GLP-1 brands present")
        else:
            fail("Missing GLP-1 brands", str(missing))
            all_ok = False
        for brand in glp1_brands:
            print(f"           - {brand}")

        # ---- 5. Wegovy 2023 ----
        header("5. Wegovy 2023 headline finding (policy crack)")
        wegovy = con.execute("""
            SELECT Tot_Spndng, Tot_Clms, Tot_Benes
            FROM partd_long
            WHERE Brnd_Name = 'Wegovy' AND year = '2023' AND Mftr_Name = 'Overall'
        """).fetchone()
        if wegovy is None:
            fail("Wegovy 2023 row exists")
            all_ok = False
        else:
            spend, claims, benes = wegovy
            if spend and abs(spend - 199773.59) < 1:
                ok("Wegovy 2023 spend", f"${spend:,.2f}")
            else:
                fail("Wegovy 2023 spend",
                     f"got ${spend}, expected $199,773.59")
                all_ok = False
            if claims == 142:
                ok("Wegovy 2023 claims", f"{claims}")
            else:
                fail("Wegovy 2023 claims", f"got {claims}, expected 142")
                all_ok = False
            if benes == 47:
                ok("Wegovy 2023 beneficiaries",
                   f"{benes}  (>10, so unsuppressed -- real Part D dispensing)")
            else:
                fail("Wegovy 2023 beneficiaries",
                     f"got {benes}, expected 47")
                all_ok = False

        # ---- 6. Annual totals vs CMS published ----
        header("6. Annual Part D totals vs CMS published (gross)")
        cms_pub = {'2019': 180.0, '2020': 195.0, '2021': 215.0,
                   '2022': 240.0, '2023': 280.0}
        annual = con.execute("""
            SELECT year, SUM(Tot_Spndng) / 1e9 AS spend_b
            FROM partd_long
            WHERE Mftr_Name = 'Overall'
            GROUP BY year
            ORDER BY year
        """).fetchall()
        for year, spend in annual:
            cms = cms_pub[year]
            delta_pct = abs(spend - cms) / cms * 100
            line = f"{year}: ${spend:.2f}B (CMS ~${cms}B, delta {delta_pct:.1f}%)"
            if delta_pct < 3:
                ok(line)
            elif delta_pct < 5:
                warn(line)
            else:
                fail(line)
                all_ok = False

        # ---- 7. GLP-1 trajectory ----
        header("7. GLP-1 spend trajectory (the headline)")
        glp1_traj = con.execute("""
            WITH glp1 AS (
                SELECT
                    year,
                    Tot_Spndng,
                    CASE
                        WHEN UPPER(Brnd_Name) LIKE 'WEGOVY%'   THEN 'obesity'
                        WHEN UPPER(Brnd_Name) LIKE 'SAXENDA%'  THEN 'obesity'
                        WHEN UPPER(Brnd_Name) LIKE 'ZEPBOUND%' THEN 'obesity'
                        ELSE 'diabetes'
                    END AS indication
                FROM partd_long
                WHERE Mftr_Name = 'Overall'
                  AND LOWER(Gnrc_Name) IN (
                      'semaglutide', 'tirzepatide', 'dulaglutide',
                      'liraglutide', 'exenatide', 'exenatide microspheres'
                  )
            )
            SELECT year,
                   ROUND(SUM(CASE WHEN indication = 'diabetes'
                                  THEN Tot_Spndng END) / 1e9, 2) AS diabetes_b
            FROM glp1
            GROUP BY year
            ORDER BY year
        """).fetchall()
        for year, spend in glp1_traj:
            print(f"           {year}: ${spend}B (diabetes GLP-1)")
        d_2019 = glp1_traj[0][1]
        d_2023 = glp1_traj[-1][1]
        if 5.0 <= d_2019 <= 5.5 and 22.0 <= d_2023 <= 22.5:
            mult = d_2023 / d_2019
            ok("GLP-1 trajectory matches headline",
               f"${d_2019}B -> ${d_2023}B ({mult:.1f}x)")
        else:
            warn("GLP-1 trajectory range",
                 f"${d_2019}B -> ${d_2023}B")

        # ---- 8. GLP-1 share of Part D growth ----
        header("8. GLP-1 share of Part D growth (CFO line)")
        partd_2019 = next(s for y, s in annual if y == '2019')
        partd_2023 = next(s for y, s in annual if y == '2023')
        partd_growth = partd_2023 - partd_2019
        glp1_growth = d_2023 - d_2019
        share = glp1_growth / partd_growth * 100
        print(f"           Total Part D growth 2019-2023:  ${partd_growth:.1f}B")
        print(f"           GLP-1 (diabetes) growth:         ${glp1_growth:.1f}B")
        if 15 <= share <= 20:
            ok("GLP-1 share of Part D growth",
               f"{share:.1f}%  (CFO-line ready)")
        else:
            warn("GLP-1 share of Part D growth",
                 f"{share:.1f}% (expected ~17%)")
    finally:
        con.close()

    # ---- 9. Deliverables ----
    header("9. SQL file and CSV deliverables")
    expected_sql = [
        "00_describe_schema.sql",
        "01_glp1_obesity_probe.sql",
        "02_glp1_family_inventory.sql",
        "03_glp1_brand_discovery.sql",
        "04_glp1_family_normalized.sql",
        "05_annual_totals_validation.sql",
    ]
    for fname in expected_sql:
        if (SQL_DIR / fname).exists():
            ok(f"sql/{fname}")
        else:
            fail(f"sql/{fname}", "missing")
            all_ok = False

    for fname in expected_sql:
        csv_name = fname.replace(".sql", ".csv")
        if (OUTPUT_DIR / csv_name).exists():
            ok(f"docs/sql_outputs/{csv_name}")
        else:
            warn(f"docs/sql_outputs/{csv_name}",
                 "not generated; rerun the SQL to produce")

    # ---- Final verdict ----
    header("PHASE 1 STATUS")
    if all_ok:
        print()
        print("  >>> ALL CRITICAL CHECKS PASSED. Phase 1 is complete. <<<")
        print("  >>> Cleared for Phase 2.                              <<<")
        print()
        return 0
    else:
        print()
        print("  >>> SOME CHECKS FAILED. Review above before proceeding. <<<")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())