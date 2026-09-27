"""Validate demo CSV contracts against setup_bigquery.sh DDL."""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from tests._support import DATA_DIR, SETUP_DIR, read_text

# Tip tables used by the bakery agent / BigQuery MCP demo.
EXPECTED_TABLES = {
    "demographics": [
        "zip_code",
        "city",
        "neighborhood",
        "median_household_income",
        "total_population",
        "median_age",
        "bachelors_degree_pct",
        "foot_traffic_index",
    ],
    "bakery_prices": [
        "store_name",
        "product_type",
        "price",
        "region",
        "is_organic",
    ],
    "sales_history_weekly": [
        "week_start_date",
        "store_location",
        "product_type",
        "quantity_sold",
        "total_revenue",
    ],
    "foot_traffic": [
        "zip_code",
        "time_of_day",
        "foot_traffic_score",
    ],
}


def _csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
    return header


def _parse_bq_table_columns(script: str, table: str) -> list[str]:
    # setup_bigquery.sh escapes backticks inside double-quoted bq query strings.
    pattern = re.compile(
        rf"CREATE OR REPLACE TABLE\s+\\`\$PROJECT_ID\.\$DATASET_NAME\.{re.escape(table)}\\`\s*\((.*?)\)\s*OPTIONS",
        re.DOTALL,
    )
    match = pattern.search(script)
    if not match:
        raise AssertionError(f"No CREATE TABLE for {table} in setup_bigquery.sh")
    body = match.group(1)
    columns: list[str] = []
    for line in body.splitlines():
        stripped = line.strip().rstrip(",")
        if not stripped or stripped.startswith("--"):
            continue
        # column lines look like: name TYPE OPTIONS(...)
        name = stripped.split()[0]
        columns.append(name)
    return columns


class DemoCsvSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup_script = read_text(SETUP_DIR / "setup_bigquery.sh")

    def test_expected_csv_files_exist(self):
        for table in EXPECTED_TABLES:
            path = DATA_DIR / f"{table}.csv"
            self.assertTrue(path.is_file(), f"missing {path}")

    def test_csv_headers_match_expected_contract(self):
        for table, columns in EXPECTED_TABLES.items():
            with self.subTest(table=table):
                self.assertEqual(_csv_header(DATA_DIR / f"{table}.csv"), columns)

    def test_csv_headers_match_bigquery_ddl(self):
        for table, columns in EXPECTED_TABLES.items():
            with self.subTest(table=table):
                ddl_columns = _parse_bq_table_columns(self.setup_script, table)
                self.assertEqual(ddl_columns, columns)

    def test_csv_files_have_data_rows(self):
        for table in EXPECTED_TABLES:
            with self.subTest(table=table):
                path = DATA_DIR / f"{table}.csv"
                with path.open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertGreater(len(rows), 0, f"{table}.csv has no data rows")
                # Every declared column present on the first row.
                for column in EXPECTED_TABLES[table]:
                    self.assertIn(column, rows[0])

    def test_is_organic_parses_as_bool_strings(self):
        path = DATA_DIR / "bakery_prices.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        values = {row["is_organic"] for row in rows}
        self.assertTrue(values)
        self.assertTrue(values.issubset({"True", "False"}))

    def test_foot_traffic_times_of_day(self):
        path = DATA_DIR / "foot_traffic.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        times = {row["time_of_day"] for row in rows}
        self.assertEqual(times, {"morning", "afternoon", "evening"})


if __name__ == "__main__":
    unittest.main()
