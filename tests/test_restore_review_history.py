"""Offline recovery tests; synthetic reports, no provider or DBOS execution."""
import sqlite3
from pathlib import Path
import pytest
from scripts.restore_review_history import restore


def database(path, rid):
    path.mkdir()
    with sqlite3.connect(path / 'reviews.sqlite') as c:
        c.executescript(Path('backend/schema.sql').read_text())
        c.execute('PRAGMA user_version=7')
        c.execute("INSERT INTO tenants VALUES('vesta','vesta-qatr')")
        c.execute("INSERT INTO review_snapshots VALUES('vesta',?,'hash','{}')", (rid,))
        c.execute("INSERT INTO review_records VALUES('vesta',?,?,'synthetic','hash','2026-09-24',NULL,1,'completed','[]','{}',NULL,'2026-09-22')", (rid,rid))
        c.execute("INSERT INTO review_results VALUES('vesta',?,1,'{}')", (rid,))
        c.execute("INSERT INTO feedback VALUES('vesta',?,?,'{}',7)", ('feedback-'+rid,rid))
        c.execute("INSERT INTO model_attempts VALUES('vesta',?,?,'response','{}')", (rid,'attempt-'+rid))
        c.execute("INSERT INTO idempotency VALUES('vesta','POST /api/v1/reviews',?,'hash','2026-09-22','{}','2026-09-24')", (rid,))
    with sqlite3.connect(path / 'dbos.sqlite') as c:
        c.execute('CREATE TABLE marker(id TEXT)')
        c.execute('INSERT INTO marker VALUES(?)',(rid,))


def test_preserves_destination_imports_history_receipts_and_checkpoints(tmp_path):
    src, dst = tmp_path/'src', tmp_path/'dst'
    database(src,'old'); database(dst,'today')
    with sqlite3.connect(src/'reviews.sqlite') as c:
        c.execute("UPDATE tenants SET active_release='historic-release'")
    before=(src/'reviews.sqlite').read_bytes()
    dbos=(dst/'dbos.sqlite').read_bytes()
    result=restore(src,dst)
    assert result['imported']['review_records']==1
    assert len(result['backups'])==2
    for path in result['backups']:
        assert (Path(path)/'reviews.sqlite').is_file()
        assert (Path(path)/'dbos.sqlite').is_file()
    with sqlite3.connect(dst/'reviews.sqlite') as c:
        for table in ('review_records','review_results','feedback','model_attempts','idempotency'):
            assert c.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==2
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
        assert c.execute('SELECT active_release FROM tenants').fetchone()[0]=='vesta-qatr'
    assert (src/'reviews.sqlite').read_bytes()==before
    assert (dst/'dbos.sqlite').read_bytes()==dbos
    assert restore(src,dst)['imported']['review_records']==0


def test_conflict_rolls_back_all_imported_rows(tmp_path):
    src, dst=tmp_path/'src',tmp_path/'dst'
    database(src,'same'); database(dst,'same')
    with sqlite3.connect(src/'reviews.sqlite') as c:
        c.execute("UPDATE review_records SET report_text='different'")
    with pytest.raises(ValueError,match='Conflicting'):
        restore(src,dst)
    with sqlite3.connect(dst/'reviews.sqlite') as c:
        assert c.execute('SELECT report_text FROM review_records').fetchone()[0]=='synthetic'


@pytest.mark.parametrize('side',['src','dst'])
def test_pending_work_refused(tmp_path,side):
    src,dst=tmp_path/'src',tmp_path/'dst'
    database(src,'old');database(dst,'today')
    with sqlite3.connect(tmp_path/side/'reviews.sqlite') as c:
        c.execute("UPDATE review_records SET execution_status='running'")
    with pytest.raises(ValueError,match='Pending'):
        restore(src,dst)
    assert not list(dst.glob('history-backup-*'))
