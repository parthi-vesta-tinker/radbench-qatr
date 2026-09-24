"""Explicit, backed-up schema-7 -> schema-8 upgrade. Stop the application first."""

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def upgrade(directory: Path):
    source = directory / "reviews.sqlite"
    if not source.is_file():
        raise SystemExit("No reviews.sqlite in this directory; nothing changed.")
    conn = sqlite3.connect(source)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN EXCLUSIVE")
        if conn.execute("PRAGMA user_version").fetchone()[0] != 7:
            raise SystemExit("Expected schema 7; nothing changed.")
        for table, field in (("review_records", "execution_status"), ("playground_runs", "status")):
            if conn.execute(f"SELECT 1 FROM {table} WHERE {field} IN ('queued','running') LIMIT 1").fetchone():
                raise SystemExit("Pending work exists. Finish it with the previous application before upgrading.")
        backup_path = directory / ("reviews-schema7-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".sqlite.bak")
        with sqlite3.connect(source) as reader, sqlite3.connect(backup_path) as backup:
            reader.backup(backup)
        schema = (Path(__file__).resolve().parents[1] / "backend/schema.sql").read_text(encoding="utf-8")
        tail = schema[schema.index("CREATE TABLE finding_classifications"):]
        statement = ""
        for line in tail.splitlines(True):
            statement += line
            if sqlite3.complete_statement(statement):
                conn.execute(statement)
                statement = ""
        if statement.strip():
            raise RuntimeError("Incomplete classification schema")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Foreign-key validation failed; upgrade rolled back.")
        conn.execute("PRAGMA user_version=8")
        conn.commit()
        print(f"Upgraded to schema 8. Backup: {backup_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    upgrade(args.data_dir.resolve())
