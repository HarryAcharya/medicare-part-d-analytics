"""
Run a .sql file against the project's DuckDB database.

Usage (from project root):
    python src/run_sql.py sql/00_describe_schema.sql

Prints results to terminal and writes a CSV to docs/sql_outputs/.
"""
import argparse
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "partd.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "sql_outputs"


def run_sql_file(sql_path: Path) -> None:
    if not sql_path.exists():
        sys.exit(f"SQL file not found: {sql_path}")

    sql = sql_path.read_text(encoding="utf-8")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        df = con.execute(sql).fetchdf()
    finally:
        con.close()

    print(f"\n=== {sql_path.name} ===")
    print(f"Rows returned: {len(df)}\n")
    print(df.to_string(index=False, max_rows=50))

    out_csv = OUTPUT_DIR / f"{sql_path.stem}.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_file")
    args = parser.parse_args()
    run_sql_file(PROJECT_ROOT / args.sql_file)
