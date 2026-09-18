"""Explicit session authority and conservative accounting, independent of review resets.

Amounts are integer micro-USD. Runtime never initializes a missing ledger/session.
Unknown attempts retain their full reservation. No keys or report text live here.
"""
import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from .contracts import ReviewProblem
from .settings import ROOT, DATA

PRICING = {
    # Verified 2026-09-18: https://developers.openai.com/api/docs/pricing
    # Standard tier; long-context cache-write/input maximum, no cache discount.
    'gpt-6-astra': (25, 75),
    'gpt-5.6-sol': (10, 30),
    'gpt-5.6-terra': (5, 18),
}
PRICE_EXPIRES = '2026-10-18T00:00:00+00:00'


def path():
    value = Path(os.environ.get('QA_SPEND_LEDGER', str(ROOT / '.qa-spend/ledger.sqlite'))).resolve()
    if value == DATA or DATA in value.parents:
        raise ReviewProblem('SPEND_LEDGER_LOCATION', 'Spend ledger must be outside QA_DATA_DIR.')
    return value


@contextmanager
def db(create=False):
    target = path()
    if create:
        target.parent.mkdir(parents=True, exist_ok=True)
    elif not target.is_file():
        raise ReviewProblem('SPEND_NOT_AUTHORIZED', 'An existing authorized spend ledger is required.')
    conn = sqlite3.connect(target.as_uri() + ('?mode=rwc' if create else '?mode=rw'), uri=True, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA synchronous=FULL')
    try:
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            yield conn
    except sqlite3.DatabaseError as exc:
        raise ReviewProblem('SPEND_LEDGER_UNAVAILABLE', 'The spend ledger is unavailable or incompatible; no new spending is permitted.') from exc
    finally:
        conn.close()


def authorize(session_id, ceiling_micro_usd, expires_at, *, authorization):
    """Operator-only entrypoint. Never called by startup, reset or HTTP requests."""
    if not session_id or not authorization.strip() or not 0 < ceiling_micro_usd <= 1_000_000 or expires_at <= time.time():
        raise ValueError('Explicit authorization, future expiry and a ceiling no greater than $1 are required.')
    with db(create=True) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, ceiling INTEGER NOT NULL, expires REAL NOT NULL, authorization TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS reservations (id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id), tenant TEXT NOT NULL, operation_key TEXT NOT NULL, fingerprint TEXT NOT NULL, bound INTEGER NOT NULL, charged INTEGER NOT NULL, state TEXT NOT NULL, config TEXT NOT NULL, UNIQUE(session_id,tenant,operation_key))')
        # Reauthorization never resets or enlarges an existing allowance.
        conn.execute('INSERT INTO sessions VALUES(?,?,?,?)', (session_id, ceiling_micro_usd, expires_at, authorization))


def session(conn, session_id):
    row = conn.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
    if not row or row['expires'] <= time.time():
        raise ReviewProblem('SPEND_NOT_AUTHORIZED', 'The live-test session is missing or expired.')
    return row


def prices(model):
    from datetime import datetime, timezone
    if model not in PRICING or datetime.now(timezone.utc) >= datetime.fromisoformat(PRICE_EXPIRES):
        raise ReviewProblem('MODEL_PRICING_UNAVAILABLE', 'No current verified pricing bound is configured for this model.')
    a, b = PRICING[model]
    return dict(input_micro_usd=a, output_micro_usd=b, source='https://developers.openai.com/api/docs/pricing', verified_at='2026-09-18', expires_at=PRICE_EXPIRES, service_tier='default')


def reserve(tenant, key, fingerprint, config, input_bound):
    session_id = os.environ.get('QA_SPEND_SESSION', '')
    operation_key = hashlib.sha256(key.encode()).hexdigest()
    with db() as conn:
        auth = session(conn, session_id)
        old = conn.execute('SELECT * FROM reservations WHERE session_id=? AND tenant=? AND operation_key=?', (session_id, tenant, operation_key)).fetchone()
        if old:
            if old['fingerprint'] != fingerprint:
                raise ReviewProblem('SPEND_RESERVATION_CONFLICT', 'This spend reservation belongs to different input.')
            if old['state'] != 'reserved':
                raise ReviewProblem('SPEND_RESERVATION_USED', 'This request already used its reservation; restore its original review database.')
            return json.loads(old['config'])
        pricing = prices(config['model'])
        # 10% headroom, rounded up; reasoning included in the output limit.
        bound = (110 * (input_bound * pricing['input_micro_usd'] + config['model_max_output_tokens'] * pricing['output_micro_usd']) + 99) // 100
        used = conn.execute('SELECT coalesce(sum(charged),0) FROM reservations WHERE session_id=?', (session_id,)).fetchone()[0]
        if used + bound > auth['ceiling']:
            raise ReviewProblem('SPEND_LIMIT_EXCEEDED', 'The complete request exceeds the remaining authorized session budget.')
        rid = 'qa_' + uuid.uuid4().hex
        captured = dict(config, spend=dict(session_id=session_id, reservation_id=rid, input_bound=input_bound, bound_micro_usd=bound, pricing=pricing))
        conn.execute('INSERT INTO reservations VALUES(?,?,?,?,?,?,?,?,?)', (rid, session_id, tenant, operation_key, fingerprint, bound, bound, 'reserved', json.dumps(captured)))
        return captured


def claim(tenant, config):
    """Called inside the actual model method, never as a replayable permission step."""
    spend = config['spend']
    with db() as conn:
        session(conn, spend['session_id'])
        from datetime import datetime, timezone
        if datetime.now(timezone.utc) >= datetime.fromisoformat(spend['pricing']['expires_at']):
            raise ReviewProblem('MODEL_PRICING_UNAVAILABLE', 'Accepted pricing has expired before dispatch.')
        row = conn.execute('SELECT config FROM reservations WHERE id=? AND tenant=?', (spend['reservation_id'], tenant)).fetchone()
        if not row or json.loads(row['config']) != config:
            raise ReviewProblem('SPEND_RESERVATION_CONFLICT', 'Accepted configuration does not match its spend reservation.')
        if conn.execute("UPDATE reservations SET state='claimed' WHERE id=? AND tenant=? AND session_id=? AND state='reserved'", (spend['reservation_id'], tenant, spend['session_id'])).rowcount != 1:
            raise ReviewProblem('MODEL_OUTCOME_UNKNOWN', 'A provider attempt was already claimed. It will not be sent again automatically.')


def settle(tenant, config, usage):
    """Only complete explicit usage can lower a reservation; never infer missing usage as zero."""
    s = config['spend']
    known = isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('input_tokens', 'output_tokens', 'total_tokens'))
    known = known and usage['total_tokens'] == usage['input_tokens'] + usage['output_tokens'] and usage['input_tokens'] <= s['input_bound'] and usage['output_tokens'] <= config['model_max_output_tokens']
    charge = s['bound_micro_usd']
    if known:
        p = s['pricing']
        charge = (110 * (usage['input_tokens'] * p['input_micro_usd'] + usage['output_tokens'] * p['output_micro_usd']) + 99) // 100
    with db() as conn:
        conn.execute("UPDATE reservations SET charged=?,state='settled' WHERE id=? AND tenant=? AND state='claimed'", (charge, s['reservation_id'], tenant))
    return charge if known else None


def release_unclaimed(tenant, config):
    if 'spend' not in config:
        return
    with db() as conn:
        conn.execute("UPDATE reservations SET charged=0,state='released' WHERE id=? AND tenant=? AND state='reserved'", (config['spend']['reservation_id'], tenant))


def status(session_id):
    with db() as conn:
        row = conn.execute('SELECT id,ceiling,expires FROM sessions WHERE id=?', (session_id,)).fetchone()
        if not row:
            raise ValueError('Unknown session')
        used = conn.execute('SELECT coalesce(sum(charged),0) FROM reservations WHERE session_id=?', (session_id,)).fetchone()[0]
        return dict(row) | dict(committed_micro_usd=used, remaining_micro_usd=max(0, row['ceiling']-used))
