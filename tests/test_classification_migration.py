"""Schema 7 survives the explicit backed-up classification upgrade."""

import json
import sqlite3
from pathlib import Path

from scripts.upgrade_classification_storage import upgrade


ROOT = Path(__file__).resolve().parents[1]


def schema7_database(directory):
    directory.mkdir()
    source = directory / "reviews.sqlite"
    schema = (ROOT / "backend/schema.sql").read_text(encoding="utf-8")
    schema = schema[:schema.index("-- JEV research classifications")]
    with sqlite3.connect(source) as conn:
        conn.executescript(schema)
        conn.execute("PRAGMA user_version=7")
        conn.execute("INSERT INTO tenants(id,active_release) VALUES('vesta','vesta-qatr')")
        conn.execute("INSERT INTO review_snapshots(tenant_id,id,sha256,config) VALUES(?,?,?,?)",
                     ("vesta", "qs-1", "hash", json.dumps({"workflow_version":"foundation-f3-0.14.0"})))
        conn.execute("""INSERT INTO review_records(tenant_id,id,snapshot_id,report_text,input_hash,created_at,
            execution_status,steps,provenance,api_version) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            ("vesta", "qr-1", "qs-1", "Findings: normal. Impression: normal.", "hash",
             "2026-09-24T00:00:00+00:00", "completed", "[]", "{}", "2026-09-22"))
    return source


def test_upgrade_preserves_review_and_creates_classification_tables(tmp_path):
    source = schema7_database(tmp_path / "data")
    upgrade(source.parent)
    with sqlite3.connect(source) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 8
        assert conn.execute("SELECT report_text FROM review_records").fetchone()[0].startswith("Findings:")
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='finding_classifications'").fetchone()
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert list(source.parent.glob("reviews-schema7-*.sqlite.bak"))


def test_upgrade_refuses_pending_work(tmp_path):
    source = schema7_database(tmp_path / "data")
    with sqlite3.connect(source) as conn:
        conn.execute("UPDATE review_records SET execution_status='running'")
    try:
        upgrade(source.parent)
    except SystemExit as exc:
        assert "Pending work" in str(exc)
    else:
        raise AssertionError("Pending schema-7 work was not refused")
    with sqlite3.connect(source) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 7
