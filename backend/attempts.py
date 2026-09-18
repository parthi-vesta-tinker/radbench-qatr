"""Private response checkpoint. Persist before SDK parsing, including refusals and usage."""
from pydantic import TypeAdapter
from agents.items import ModelResponse
from . import store
from .contracts import ReviewProblem

ADAPTER = TypeAdapter(ModelResponse)


def response(tenant, rid):
    with store.db() as conn:
        row = conn.execute('SELECT * FROM model_attempts WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    if row and row['outcome'] == 'response':
        return ADAPTER.validate_json(row['response'])
    if row:
        raise ReviewProblem('MODEL_OUTCOME_UNKNOWN', 'The provider outcome is unknown. Automatic repeat dispatch is blocked.')
    return None


def claim(tenant, rid, reservation):
    with store.db() as conn:
        conn.execute('INSERT INTO model_attempts VALUES(?,?,?,?,NULL)', (tenant, rid, reservation, 'claimed'))


def save(tenant, rid, value):
    encoded = ADAPTER.dump_json(value).decode()
    with store.db() as conn:
        if conn.execute("UPDATE model_attempts SET outcome='response',response=? WHERE tenant_id=? AND review_id=? AND outcome='claimed'", (encoded, tenant, rid)).rowcount != 1:
            raise RuntimeError('Attempt checkpoint conflict')


def unknown(tenant, rid):
    with store.db() as conn:
        conn.execute("UPDATE model_attempts SET outcome='unknown' WHERE tenant_id=? AND review_id=? AND outcome='claimed'", (tenant, rid))


def uncertain(tenant, rid, config):
    if 'spend' not in config:
        return False
    from . import spend
    with store.db() as conn:
        row = conn.execute('SELECT outcome FROM model_attempts WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    if row:
        return row['outcome'] != 'response'
    try:
        with spend.db() as conn:
            row = conn.execute('SELECT state FROM reservations WHERE tenant=? AND id=?', (tenant, config['spend']['reservation_id'])).fetchone()
        return row is None or row['state'] not in ('reserved', 'released')
    except Exception:
        return True  # No evidence that dispatch did not happen.


def failure_metrics(tenant, rid, config):
    """Keep observed usage on refusal/schema failures; unknown usage stays null."""
    from . import spend
    with store.db() as conn:
        row = conn.execute('SELECT response FROM model_attempts WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    if not row:
        return None
    value = ADAPTER.validate_json(row['response']) if row['response'] else None
    usage = value.raw_usage if value else None
    cost = spend.settle(tenant, config, usage) if value else None
    return dict(provider='openai', model=config['model'],
                model_calls=1 if value else None, requests=1 if value else None,
                input_tokens=usage.get('input_tokens') if usage else None,
                output_tokens=usage.get('output_tokens') if usage else None,
                total_tokens=usage.get('total_tokens') if usage else None,
                cost_upper_bound_micro_usd=cost)
