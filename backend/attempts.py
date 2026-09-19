"""Private response checkpoint. Persist before SDK parsing, including refusals and usage."""
from pydantic import TypeAdapter
from agents.items import ModelResponse
from . import store
from .contracts import ReviewProblem

ADAPTER = TypeAdapter(ModelResponse)
LIVE = 'model_attempts'
TABLES = {LIVE, 'playground_attempts'}


def table(config):
    """Playground runs checkpoint in their own table; the rules are identical."""
    name = config.get('attempt_table', LIVE)
    if name not in TABLES:
        raise ValueError('Unknown attempt table')
    return name


def response(tenant, rid, table=LIVE):
    with store.db() as conn:
        row = conn.execute(f'SELECT * FROM {table} WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    if row and row['outcome'] == 'response':
        return ADAPTER.validate_json(row['response'])
    if row:
        raise ReviewProblem('MODEL_OUTCOME_UNKNOWN', 'The provider outcome is unknown. Automatic repeat dispatch is blocked.')
    return None


def claim(tenant, rid, attempt, table=LIVE):
    with store.db() as conn:
        conn.execute(f'INSERT INTO {table} VALUES(?,?,?,?,NULL)', (tenant, rid, attempt, 'claimed'))


def save(tenant, rid, value, table=LIVE):
    encoded = ADAPTER.dump_json(value).decode()
    with store.db() as conn:
        if conn.execute(f"UPDATE {table} SET outcome='response',response=? WHERE tenant_id=? AND review_id=? AND outcome='claimed'", (encoded, tenant, rid)).rowcount != 1:
            raise RuntimeError('Attempt checkpoint conflict')


def unknown(tenant, rid, table=LIVE):
    with store.db() as conn:
        conn.execute(f"UPDATE {table} SET outcome='unknown' WHERE tenant_id=? AND review_id=? AND outcome='claimed'", (tenant, rid))


def uncertain(tenant, rid, config):
    """A claim is written before dispatch, so no row means the provider was never called."""
    if config.get('mode') != 'openai':
        return False
    with store.db() as conn:
        row = conn.execute(f'SELECT outcome FROM {table(config)} WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    return bool(row) and row['outcome'] != 'response'


def failure_metrics(tenant, rid, config):
    """Keep observed usage on refusal/schema failures; unknown usage stays null."""
    with store.db() as conn:
        row = conn.execute(f'SELECT response FROM {table(config)} WHERE tenant_id=? AND review_id=?', (tenant, rid)).fetchone()
    if not row:
        return None
    value = ADAPTER.validate_json(row['response']) if row['response'] else None
    usage = value.raw_usage if value else None
    return dict(provider='openai', model=config['model'],
                model_calls=1 if value else None, requests=1 if value else None,
                input_tokens=usage.get('input_tokens') if usage else None,
                output_tokens=usage.get('output_tokens') if usage else None,
                total_tokens=usage.get('total_tokens') if usage else None)
