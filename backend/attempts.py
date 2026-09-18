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


def claim(tenant, rid, attempt):
    with store.db() as conn:
        conn.execute('INSERT INTO model_attempts VALUES(?,?,?,?,NULL)', (tenant, rid, attempt, 'claimed'))


def save(tenant, rid, value):
    encoded = ADAPTER.dump_json(value).decode()
    with store.db() as conn:
        if conn.execute("UPDATE model_attempts SET outcome='response',response=? WHERE tenant_id=? AND review_id=? AND outcome='claimed'", (encoded, tenant, rid)).rowcount != 1:
            raise RuntimeError('Attempt checkpoint conflict')


def unknown(tenant, rid):
    with store.db() as conn:
        conn.execute("UPDATE model_attempts SET outcome='unknown' WHERE tenant_id=? AND review_id=? AND outcome='claimed'", (tenant, rid))


def uncertain(tenant, rid, config):
    """A claim is written before dispatch, so no row means the provider was never called."""
    if config.get('mode') != 'openai':
        return False
    with store.db() as conn:
        row = conn.execute('SELECT outcome FROM model_attempts WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    return bool(row) and row['outcome'] != 'response'


def failure_metrics(tenant, rid, config):
    """Keep observed usage on refusal/schema failures; unknown usage stays null."""
    with store.db() as conn:
        row = conn.execute('SELECT response FROM model_attempts WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    if not row:
        return None
    value = ADAPTER.validate_json(row['response']) if row['response'] else None
    usage = value.raw_usage if value else None
    return dict(provider='openai', model=config['model'],
                model_calls=1 if value else None, requests=1 if value else None,
                input_tokens=usage.get('input_tokens') if usage else None,
                output_tokens=usage.get('output_tokens') if usage else None,
                total_tokens=usage.get('total_tokens') if usage else None)
