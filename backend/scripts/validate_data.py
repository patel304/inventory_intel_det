"""Read-only data quality report. Does not modify MySQL records or ground_truth.csv."""

from pathlib import Path

from sqlalchemy import text

from app.config import BACKEND_ROOT
from app.database import engine

REPORT_PATH = BACKEND_ROOT.parent / "docs" / "DATA_VALIDATION_REPORT.md"
GROUND_TRUTH = BACKEND_ROOT / "data" / "generated" / "ground_truth.csv"


def q(connection, sql: str):
    return connection.execute(text(sql)).fetchall()


def scalar(connection, sql: str):
    return connection.execute(text(sql)).scalar()


def main():
    lines = [
        "# Data Validation Report",
        "",
        "Read-only checks against the existing MySQL database and ground-truth CSV.",
        "Original records were not modified.",
        "",
    ]

    with engine.connect() as connection:
        tables = [row[0] for row in q(connection, "SHOW TABLES")]
        lines.append("## Table counts")
        lines.append("")
        lines.append("| Table | Rows |")
        lines.append("| --- | ---: |")
        for table in tables:
            count = scalar(connection, f"SELECT COUNT(*) FROM `{table}`")
            lines.append(f"| {table} | {count} |")

        lines.append("")
        lines.append("## Inventory movements")
        lines.append("")
        lines.append("| Check | Result |")
        lines.append("| --- | ---: |")
        lines.append(
            f"| Negative quantities | {scalar(connection, 'SELECT COUNT(*) FROM inventory_movements WHERE quantity < 0')} |"
        )
        lines.append(
            f"| NULL store_id | {scalar(connection, 'SELECT COUNT(*) FROM inventory_movements WHERE store_id IS NULL')} |"
        )
        lines.append(
            f"| Unknown movement types | {scalar(connection, "SELECT COUNT(*) FROM inventory_movements WHERE movement_type NOT IN ('OPENING_BALANCE','RECEIPT','RETURN_IN','TRANSFER_IN','ADJUSTMENT_IN','SALE','DAMAGE','TRANSFER_OUT','ADJUSTMENT_OUT')")} |"
        )
        lines.append(
            f"| Unmatched transfer groups | {scalar(connection, """
                SELECT COUNT(*) FROM (
                  SELECT transfer_group_id,
                         SUM(movement_type='TRANSFER_OUT') AS outs,
                         SUM(movement_type='TRANSFER_IN') AS ins
                  FROM inventory_movements
                  WHERE transfer_group_id IS NOT NULL
                  GROUP BY transfer_group_id
                  HAVING outs <> ins
                ) t
            """)} |"
        )
        lines.append(
            f"| Orphan store FKs | {scalar(connection, 'SELECT COUNT(*) FROM inventory_movements m LEFT JOIN stores s ON m.store_id = s.id WHERE s.id IS NULL')} |"
        )
        lines.append(
            f"| Orphan SKU FKs | {scalar(connection, 'SELECT COUNT(*) FROM inventory_movements m LEFT JOIN skus k ON m.sku_id = k.id WHERE k.id IS NULL')} |"
        )

        lines.append("")
        lines.append("## Alerts")
        lines.append("")
        lines.append("| Check | Result |")
        lines.append("| --- | ---: |")
        lines.append(
            f"| NULL expected_quantity | {scalar(connection, 'SELECT COUNT(*) FROM shrinkage_alerts WHERE expected_quantity IS NULL')} |"
        )
        lines.append(
            f"| NULL cycle_count_id | {scalar(connection, 'SELECT COUNT(*) FROM shrinkage_alerts WHERE cycle_count_id IS NULL')} |"
        )
        lines.append(
            f"| Duplicate alert_code | {scalar(connection, 'SELECT COUNT(*) FROM (SELECT alert_code FROM shrinkage_alerts GROUP BY alert_code HAVING COUNT(*) > 1) t')} |"
        )

    lines.append("")
    lines.append("## Ground truth")
    lines.append("")
    if GROUND_TRUTH.exists():
        import csv

        with GROUND_TRUTH.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        codes = [row["count_code"] for row in rows]
        shrinkage = sum(int(row.get("is_shrinkage") or 0) for row in rows)
        missing = sum(1 for row in rows if not row.get("count_code"))
        duplicates = len(codes) - len(set(codes))
        lines.append(f"- File: `{GROUND_TRUTH}`")
        lines.append(f"- Rows: {len(rows)}")
        lines.append(f"- Shrinkage labels: {shrinkage}")
        lines.append(f"- Missing count_code: {missing}")
        lines.append(f"- Duplicate count_code: {duplicates}")
        lines.append("- File was read only; it was not rewritten.")
    else:
        lines.append("- ground_truth.csv was not found (expected under backend/data/generated/).")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Returns and promotions tables are empty in the current dataset.")
    lines.append("- No ADJUSTMENT_* movement types are present; the API still implements them.")
    lines.append("- Negative expected stock is possible in theory if sales exceed receipts; not repaired.")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
