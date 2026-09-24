"""Explicit schema-7 terminal review import. Stop both applications before running.

Preserves the destination's DBOS store and never imports executable workflows.
Both data folders are backed up. Source records and destination conflicts are never
modified; an identical repeat import is harmless. Studio and Playground are excluded.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


TABLES = ('review_snapshots', 'review_records', 'review_results', 'observations',
          'feedback', 'outcomes', 'model_attempts')


def restore(source: Path, destination: Path):
    source, destination = source.resolve(), destination.resolve()
    if source == destination:
        raise ValueError('Source and destination must differ.')
    for directory in (source, destination):
        if not (directory / 'reviews.sqlite').is_file():
            raise ValueError('Both folders must contain an existing reviews.sqlite.')
    src = sqlite3.connect(f'file:{source / "reviews.sqlite"}?mode=ro', uri=True)
    dst = sqlite3.connect(destination / 'reviews.sqlite')
    src.row_factory = dst.row_factory = sqlite3.Row
    backups = []
    try:
        dst.execute('PRAGMA foreign_keys=ON')
        for conn in (src, dst):
            if conn.execute('PRAGMA user_version').fetchone()[0] != 7:
                raise ValueError('Both stores must already use schema 7.')
            for table, status in [('review_records', 'execution_status'), ('playground_runs', 'status')]:
                if conn.execute(f"SELECT 1 FROM {table} WHERE {status} IN ('queued','running') LIMIT 1").fetchone():
                    raise ValueError('Pending work exists; nothing imported.')
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Source or destination integrity check failed.')
        # Applications must be stopped, including any process using the source folder.
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        for directory in (source, destination):
            backup_dir = directory / ('history-backup-' + stamp)
            backup_dir.mkdir(mode=0o700)
            backups.append(str(backup_dir))
            for name in ('reviews.sqlite', 'dbos.sqlite'):
                path = directory / name
                if path.is_file():
                    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as reader, sqlite3.connect(backup_dir / name) as backup:
                        reader.backup(backup)
        src.execute('BEGIN')
        dst.execute('BEGIN IMMEDIATE')
        records = list(src.execute('SELECT * FROM review_records'))
        ids = {(r['tenant_id'], r['id']) for r in records}
        snapshots = {(r['tenant_id'], r['snapshot_id']) for r in records}
        counts = {}

        def insert(table, rows):
            columns = [r[1] for r in src.execute(f'PRAGMA table_xinfo({table})') if r[6] == 0]
            target_columns = [r[1] for r in dst.execute(f'PRAGMA table_xinfo({table})') if r[6] == 0]
            if set(columns) != set(target_columns):
                raise ValueError(f'Incompatible columns in {table}.')
            keys = [r[1] for r in src.execute(f'PRAGMA table_info({table})') if r[5]]
            count = 0
            for row in rows:
                existing = dst.execute(f'SELECT * FROM {table} WHERE ' + ' AND '.join(f'{k}=?' for k in keys), [row[k] for k in keys]).fetchone()
                if existing is not None:
                    if any(existing[k] != row[k] for k in columns):
                        raise ValueError(f'Conflicting record in {table}; import rolled back.')
                    continue
                dst.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})', [row[k] for k in columns])
                count += 1
            counts[table] = count

        # Current tenant bindings remain server controlled. Historical configuration
        # is carried by each review snapshot, not the tenant's active release.
        known = {r[0] for r in dst.execute('SELECT id FROM tenants')}
        if {tenant for tenant, _ in ids} - known:
            raise ValueError('Source includes an unconfigured destination tenant.')
        for table in TABLES:
            rows = list(src.execute(f'SELECT * FROM {table}'))
            if table == 'review_snapshots':
                rows = [r for r in rows if (r['tenant_id'], r['id']) in snapshots]
            elif table != 'review_records':
                rows = [r for r in rows if (r['tenant_id'], r['review_id']) in ids]
            insert(table, rows)
        # Only review and review-feedback receipts belong to this import.
        operations = {'POST /api/v1/reviews'}
        operations.update(f'PUT /api/v1/reviews/{rid}' for _, rid in ids)
        operations.update(f'POST /api/v1/reviews/{rid}/feedback' for _, rid in ids)
        insert('idempotency', [r for r in src.execute('SELECT * FROM idempotency') if r['operation'] in operations])
        if dst.execute('PRAGMA foreign_key_check').fetchall() or dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Import integrity validation failed; rolled back.')
        dst.commit()
        return {'imported': counts, 'backups': backups}
    finally:
        src.close()
        dst.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--applications-stopped', action='store_true', required=True,
                        help='Confirm neither data folder is in use by an application.')
    args = parser.parse_args()
    print(restore(args.source, args.destination))
