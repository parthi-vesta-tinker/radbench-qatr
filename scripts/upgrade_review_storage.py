"""Explicit, backed-up schema-6 -> schema-7 upgrade. Stop the application first."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def upgrade(directory: Path):
    source = directory / 'reviews.sqlite'
    if not source.is_file():
        raise SystemExit('No reviews.sqlite in this directory; nothing changed.')
    conn = sqlite3.connect(source)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=OFF')
        conn.execute('BEGIN EXCLUSIVE')
        if conn.execute('PRAGMA user_version').fetchone()[0] != 6:
            raise SystemExit('Expected schema 6; nothing changed.')
        for table, field in [('review_records', 'execution_status'), ('playground_runs', 'status')]:
            if conn.execute(f"SELECT 1 FROM {table} WHERE {field} IN ('queued','running') LIMIT 1").fetchone():
                raise SystemExit('Pending work exists. Finish it with the previous application before upgrading.')
        # Backup using a separate reader while our exclusive WAL writer prevents new writes.
        backup_path = directory / ('reviews-schema6-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.sqlite.bak')
        with sqlite3.connect(source) as reader, sqlite3.connect(backup_path) as backup:
            reader.backup(backup)
        feedback = []
        for row in conn.execute('SELECT * FROM feedback'):
            doc = json.loads(row['document'])
            target = conn.execute('SELECT document FROM observations WHERE tenant_id=? AND review_id=? AND id=?',
                                  (row['tenant_id'], row['review_id'], doc.get('observation_id'))).fetchone()
            doc['target_comment'] = json.loads(target[0])['comment'] if target else None
            doc.pop('result_version', None)
            doc.pop('input_hash', None)
            feedback.append((row['tenant_id'], row['id'], row['review_id'], json.dumps(doc), 7))
        conn.execute('DROP TABLE feedback')
        schema = (Path(__file__).resolve().parents[1] / 'backend/schema.sql').read_text()
        start = schema.index('CREATE TABLE feedback')
        conn.execute(schema[start:schema.index(';', start) + 1])
        conn.execute('CREATE INDEX feedback_review_order ON feedback(tenant_id,review_id)')
        conn.executemany('INSERT INTO feedback(tenant_id,id,review_id,document,schema_version) VALUES(?,?,?,?,?)', feedback)
        conn.execute('ALTER TABLE review_records ADD COLUMN input_version INTEGER NOT NULL DEFAULT 1')
        conn.execute('DROP TRIGGER review_input_immutable')
        conn.execute('DROP TRIGGER review_terminal_immutable')
        conn.execute('DROP VIEW reviews')
        start = schema.index('CREATE VIEW reviews')
        conn.execute(schema[start:schema.index(';', start) + 1])
        if conn.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Foreign-key validation failed; upgrade rolled back.')
        conn.execute('PRAGMA user_version=7')
        conn.commit()
        print(f'Upgraded to schema 7. Backup: {backup_path}')
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    args = parser.parse_args()
    upgrade(args.data_dir.resolve())
