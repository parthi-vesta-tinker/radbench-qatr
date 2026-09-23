"""Tenant-scoped SQLite resources, transactional outbox and durable POST receipts."""

import hashlib
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from .settings import DATA
from .contracts import STEPS
from . import presentation

START_LOCK = threading.Lock()
CREATE_REVIEW = "POST /api/v1/reviews"


class IdempotencyConflict(Exception):
    pass


class ReviewConflict(Exception):
    pass


class InvalidCursor(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix):
    return prefix + "_" + uuid.uuid4().hex


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def feedback_scope(rid):
    return f"POST /api/v1/reviews/{rid}/feedback"


@contextmanager
def db():
    conn = sqlite3.connect(DATA / "reviews.sqlite", timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


SCHEMA_VERSION = 7


def init():
    """Open a matching database or bootstrap an empty one; never migrate old data."""
    from pathlib import Path
    from .access import tenants
    from .settings import APP_VERSION

    DATA.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()
        if version == 6:
            raise RuntimeError("Schema 6 requires an explicit upgrade. Stop the application, finish pending work with the prior build, then run scripts/upgrade_review_storage.py --data-dir <QA_DATA_DIR>. Existing records are preserved.")
        if version != SCHEMA_VERSION and (version != 0 or exists):
            raise RuntimeError("Incompatible database schema. Choose a fresh QA_DATA_DIR for application and DBOS storage; existing records are preserved.")
        if version == 0:
            # executescript implicitly commits: execute complete statements individually
            # so bootstrap and its version marker remain one atomic transaction.
            statement = ""
            for line in Path(__file__).with_name("schema.sql").read_text(encoding="utf-8").splitlines(True):
                statement += line
                if sqlite3.complete_statement(statement):
                    conn.execute(statement)
                    statement = ""
            if statement.strip():
                raise RuntimeError("Incomplete bootstrap schema")
            conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        # The configured profile, not a resolved release: bootstrap has not composed a pack yet.
        # Accepting a review records the resolved release id for the snapshot it captured.
        from .content import profile
        for tenant, entry in tenants().items():
            conn.execute("INSERT INTO tenants(id,active_release) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET active_release=excluded.active_release", (tenant, profile(tenant, entry)[0]))
        for row in conn.execute("SELECT config FROM reviews WHERE json_extract(document,'$.execution_status') IN ('queued','running')"):
            if json.loads(row["config"]).get("workflow_version") != APP_VERSION:
                raise RuntimeError("Pending workflow version mismatch. Use the matching application or a fresh QA_DATA_DIR.")


def receipt(status, body, headers=None):
    return dict(status=status, body=body, headers=headers or {})


def request_hash(payload, version):
    return digest(canonical({"api_version": version, "payload": payload}))


def replay_in(conn, tenant, operation, key, payload, version):
    row = conn.execute(
        "SELECT * FROM idempotency WHERE tenant_id=? AND operation=? AND key_hash=?",
        (tenant, operation, digest(key)),
    ).fetchone()
    if row:
        if row["request_hash"] != request_hash(payload, version):
            raise IdempotencyConflict()
        return json.loads(row["response"])
    return None


def replay(tenant, operation, key, payload, version):
    with db() as conn:
        return replay_in(conn, tenant, operation, key, payload, version)


def remember(conn, tenant, operation, key, payload, version, response):
    conn.execute(
        "INSERT INTO idempotency(tenant_id,operation,key_hash,request_hash,api_version,response,created_at) VALUES(?,?,?,?,?,?,?)",
        (
            tenant,
            operation,
            digest(key),
            request_hash(payload, version),
            version,
            canonical(response),
            now(),
        ),
    )


def reserve(tenant, key, request, config, version=presentation.API_VERSION, replace_id=None, submitted_by=None):
    payload = request.model_dump()
    operation = f"PUT /api/v1/reviews/{replace_id}" if replace_id else CREATE_REVIEW
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        saved = replay_in(conn, tenant, operation, key, payload, version)
        if saved:
            return saved, False
        previous = None
        if replace_id:
            previous = conn.execute("SELECT * FROM review_records WHERE tenant_id=? AND id=?", (tenant, replace_id)).fetchone()
            if previous is None:
                raise KeyError("Review not found")
            if previous["execution_status"] in ("queued", "running"):
                raise ReviewConflict("Wait for this review to finish before replacing it.")
            if request.expected_input_version != previous["input_version"]:
                raise ReviewConflict("This review changed in another session. Reload it before submitting.")
        rid = replace_id or new_id("qr")
        generation = previous["input_version"] + 1 if previous else 1
        config = dict(config, input_version=generation)
        report_input = {"report_text": request.report_text}
        doc = dict(
            tenant_id=tenant,
            review_id=rid,
            created_at=now(),
            input_version=generation,
            input_hash=request.fingerprint(),
            input=report_input,
            execution_status="queued",
            result=None,
            error=None,
            steps=[
                dict(step_id=s, status="pending", started_at=None, completed_at=None)
                for s in STEPS
            ],
            provenance={
                k: v
                for k, v in config.items()
                if k
                not in ("policy_text", "ready", "skill_snapshot", "stage_instructions", "combined_instructions", "combined_task")
            }
            | dict(
                source_kind="manual_paste",
                source_version=generation,
                authorship_status="unknown",
                signature_status="unknown",
                upstream_qa=None,
                submitted_by=submitted_by,
            ),
        )
        snapshot_id = new_id("qs")
        conn.execute("UPDATE tenants SET active_release=? WHERE id=?", (config.get("skill_release"), tenant))
        captured = canonical(config)
        conn.execute("INSERT INTO review_snapshots(tenant_id,id,sha256,config) VALUES(?,?,?,?)",
                     (tenant, snapshot_id, digest(captured), captured))
        if previous:
            # Replace the current projection atomically, retaining review-level feedback.
            # Outcomes are invalidated: old acceptance never applies to corrected text.
            for table in ("outcomes", "observations", "review_results", "model_attempts"):
                conn.execute(f"DELETE FROM {table} WHERE tenant_id=? AND review_id=?", (tenant, rid))
            conn.execute("""UPDATE review_records SET snapshot_id=?,report_text=?,input_hash=?,created_at=?,
                         completed_at=NULL,input_version=?,execution_status='queued',steps=?,provenance=?,error=NULL,api_version=?
                         WHERE tenant_id=? AND id=?""",
                         (snapshot_id, request.report_text, doc["input_hash"], doc["created_at"], generation,
                          canonical(doc["steps"]), canonical(doc["provenance"]), version, tenant, rid))
            conn.execute("DELETE FROM review_snapshots WHERE tenant_id=? AND id=?", (tenant, previous["snapshot_id"]))
        else:
            conn.execute(
                "INSERT INTO review_records(tenant_id,id,snapshot_id,report_text,input_hash,created_at,execution_status,steps,provenance,api_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (tenant, rid, snapshot_id, request.report_text, doc["input_hash"], doc["created_at"],
                 "queued", canonical(doc["steps"]), canonical(doc["provenance"]), version),
            )
        saved = receipt(
            202,
            presentation.review(doc, version),
            {"Location": "/api/v1/reviews/" + rid, "Retry-After": "1"},
        )
        remember(conn, tenant, operation, key, payload, version, saved)
        return saved, True


def get(tenant, rid):
    with db() as conn:
        row = conn.execute(
            "SELECT document FROM reviews WHERE tenant_id=? AND id=?", (tenant, rid)
        ).fetchone()
        return json.loads(row["document"]) if row else None


def job(tenant, rid):
    from .records import AcceptedSnapshot

    with db() as conn:
        row = conn.execute(
            "SELECT r.report_text,s.* FROM review_records r JOIN review_snapshots s ON s.tenant_id=r.tenant_id AND s.id=r.snapshot_id WHERE r.tenant_id=? AND r.id=?",
            (tenant, rid),
        ).fetchone()
        return ({"report_text": row["report_text"]}, AcceptedSnapshot.from_row(row).decode()) if row else None


def pending():
    # Internal recovery enumeration only; indexed status avoids scanning completed report bodies.
    with db() as conn:
        return [
            (row["tenant_id"], row["id"])
            for row in conn.execute(
                "SELECT tenant_id,id FROM review_records WHERE execution_status IN ('queued','running')"
            )
        ]


def update(
    tenant,
    rid,
    *,
    input_version=None,
    step=None,
    step_status=None,
    execution_status=None,
    result=None,
    error=None,
    metrics=None,
):
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT document FROM reviews WHERE tenant_id=? AND id=?", (tenant, rid)
        ).fetchone()
        if row is None:
            raise KeyError("Review not found in workflow tenant")
        doc = json.loads(row["document"])
        if input_version is not None and doc["input_version"] != input_version:
            return  # A superseded worker can never overwrite the current review.
        if result is not None:
            result = dict(result, result_version=doc["input_version"])
        if doc["execution_status"] in ("completed", "failed", "needs_input"):
            if result is not None and canonical(result) != canonical(doc["result"]):
                raise ValueError("A terminal review cannot be replaced")
            if execution_status and execution_status != doc["execution_status"]:
                raise ValueError("A terminal review cannot change state")
            return  # same-build durable finalization replay
        if result is not None and execution_status != "completed":
            raise ValueError("Results require atomic completed finalization")
        if execution_status == "completed" and result is None:
            raise ValueError("Completion requires a validated result")
        if execution_status:
            doc["execution_status"] = execution_status
        if result is not None:
            doc["result"] = result
        if error is not None:
            doc["error"] = error
        if step:
            item = next(x for x in doc["steps"] if x["step_id"] == step)
            item["status"] = step_status
            if step_status == "running":
                item["started_at"] = now()
            if step_status in ("completed", "failed", "needs_input"):
                item["completed_at"] = now()
            if metrics:
                item["metrics"] = metrics
        if execution_status in ("failed", "needs_input"):
            doc["result"] = None
            for item in doc["steps"]:
                if item["status"] == "pending":
                    item["status"] = "skipped"
        if execution_status in ("completed", "failed", "needs_input"):
            doc["completed_at"] = now()
        if result is not None:
            metadata = {k: v for k, v in result.items() if k not in ("general_comments", "critical_comments")}
            conn.execute("INSERT INTO review_results(tenant_id,review_id,result_version,metadata) VALUES(?,?,?,?)",
                         (tenant, rid, result["result_version"], canonical(metadata)))
            for group in ("general_comments", "critical_comments"):
                for position, observation in enumerate(result[group]):
                    conn.execute("INSERT INTO observations(tenant_id,review_id,result_version,id,group_name,position,document) VALUES(?,?,?,?,?,?,?)",
                                 (tenant, rid, result["result_version"], observation["observation_id"], group, position, canonical(observation)))
        conn.execute(
            "UPDATE review_records SET execution_status=?,steps=?,completed_at=?,error=? WHERE tenant_id=? AND id=?",
            (doc["execution_status"], canonical(doc["steps"]), doc.get("completed_at"),
             canonical(doc["error"]) if doc.get("error") else None, tenant, rid),
        )


def save_feedback(tenant, rid, key, data, version=presentation.API_VERSION):
    payload = data.model_dump()
    operation = feedback_scope(rid)
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        saved = replay_in(conn, tenant, operation, key, payload, version)
        if saved:
            return saved, False
        row = conn.execute(
            "SELECT document FROM reviews WHERE tenant_id=? AND id=?", (tenant, rid)
        ).fetchone()
        if row is None:
            raise KeyError("Review not found")
        review = json.loads(row["document"])
        target_comment = None
        if data.target == 'observation':
            target_comment = next((o['comment'] for group in ('general_comments', 'critical_comments')
                                   for o in (review.get('result') or {}).get(group, [])
                                   if o['observation_id'] == data.observation_id), None)
            if target_comment is None:
                raise ReviewConflict('The comment is no longer available. Reload this review.')
        doc = dict(
            target_comment=target_comment,
            tenant_id=tenant,
            feedback_id=new_id("qf"),
            review_id=rid,
            created_at=now(),
            **payload,
        )
        conn.execute(
            "INSERT INTO feedback(tenant_id,id,review_id,document,schema_version) VALUES(?,?,?,?,?)",
            (tenant, doc["feedback_id"], rid, canonical(doc), SCHEMA_VERSION),
        )
        saved = receipt(201, presentation.feedback(doc, version))
        remember(conn, tenant, operation, key, payload, version, saved)
        return saved, True


def feedback(tenant, rid, limit=20, starting_after=None):
    with db() as conn:
        after = 0
        if starting_after:
            row = conn.execute(
                "SELECT rowid FROM feedback WHERE tenant_id=? AND review_id=? AND id=?",
                (tenant, rid, starting_after),
            ).fetchone()
            if not row:
                raise InvalidCursor()
            after = row[0]
        rows = list(
            conn.execute(
                "SELECT document FROM feedback WHERE tenant_id=? AND review_id=? AND rowid>? ORDER BY rowid LIMIT ?",
                (tenant, rid, after, limit + 1),
            )
        )
        return [json.loads(x["document"]) for x in rows[:limit]], len(rows) > limit


def list_reviews(
    tenant,
    limit=20,
    starting_after=None,
    query="",
    status=None,
    outcome=None,
    critical=None,
    has_feedback=None,
    include_feedback=False,
    submitted_after=None,
    submitted_before=None,
):
    """Newest-first bounded summaries; source fetched only when opening a review."""
    with db() as conn:
        terms, values = ["r.tenant_id=?"], [tenant]
        if starting_after:
            row = conn.execute(
                "SELECT json_extract(document, '$.created_at'),id FROM reviews WHERE tenant_id=? AND id=?",
                (tenant, starting_after),
            ).fetchone()
            if not row:
                raise InvalidCursor()
            terms.append("(json_extract(r.document, '$.created_at'),r.id)<(?,?)")
            values.extend([row[0], row[1]])
        if query:
            terms.append(
                "(instr(lower(json_extract(r.document, '$.input.report_text')), lower(?))>0 OR instr(r.id, ?)>0)"
            )
            values.extend([query, query])
        if status:
            terms.append("json_extract(r.document, '$.execution_status')=?")
            values.append(status)
        if outcome:
            terms.append("json_extract(r.document, '$.result.outcome')=?")
            values.append(outcome)
        if critical is not None:
            terms.append(
                "json_extract(r.document, '$.result.critical_finding_detected')=?"
            )
            values.append(int(critical))
        count_sql = "(SELECT count(*) FROM feedback f WHERE f.tenant_id=r.tenant_id AND f.review_id=r.id)"
        if has_feedback is not None:
            terms.append(count_sql + (">0" if has_feedback else "=0"))
        if submitted_after:
            terms.append("julianday(json_extract(r.document, '$.created_at')) >= julianday(?)")
            values.append(submitted_after)
        if submitted_before:
            terms.append("julianday(json_extract(r.document, '$.created_at')) < julianday(?)")
            values.append(submitted_before)
        rows = conn.execute(
            "SELECT r.document, "
            + (count_sql if include_feedback else "NULL")
            + " AS feedback_count FROM reviews r WHERE "
            + " AND ".join(terms)
            + " ORDER BY json_extract(r.document, '$.created_at') DESC,r.id DESC LIMIT ?",
            [*values, limit + 1],
        ).fetchall()
        items = []
        for row in rows[:limit]:
            doc = json.loads(row["document"])
            result = doc.get("result") or {}
            items.append(
                dict(
                    id=doc["review_id"],
                    display_id=doc["review_id"][-5:].upper(),
                    created_at=doc["created_at"],
                    submitted_by=doc.get("provenance", {}).get("submitted_by"),
                    execution_status=doc["execution_status"],
                    preview=" ".join(doc["input"]["report_text"].split())[:140],
                    outcome=result.get("outcome"),
                    general_count=len(result.get("general_comments", [])),
                    critical_count=len(result.get("critical_comments", [])),
                    feedback_count=row["feedback_count"],
                    mode=doc["provenance"]["mode"],
                )
            )
        return items, len(rows) > limit


# --- Playground -------------------------------------------------------------------
# Isolated test runs. These never touch review_records, review_results, observations,
# feedback or outcomes, and no reporting or analytics query reads playground_runs.


def playground_steps():
    return [dict(step=name, status="queued", elapsed_ms=None) for name in STEPS]


def create_playground_run(tenant, run_id, *, source, sample_id, report_text, model, mode,
                          pack_ref, release_id):
    with db() as conn:
        conn.execute(
            "INSERT INTO playground_runs(tenant_id,id,pack_ref,release_id,source,sample_id,"
            "report_text,model,mode,created_at,status,steps)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,'queued',?)",
            (tenant, run_id, pack_ref, release_id, source, sample_id, report_text, model,
             mode, now(), canonical(playground_steps())),
        )
    return playground_run(tenant, run_id)


def playground_run(tenant, run_id):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM playground_runs WHERE tenant_id=? AND id=?", (tenant, run_id)
        ).fetchone()
    if row is None:
        return None
    return dict(
        run_id=row["id"], pack_ref=row["pack_ref"], release_id=row["release_id"],
        source=row["source"], sample_id=row["sample_id"], report_text=row["report_text"],
        model=row["model"], mode=row["mode"], status=row["status"],
        created_at=row["created_at"], completed_at=row["completed_at"],
        steps=json.loads(row["steps"]),
        result=json.loads(row["result"]) if row["result"] else None,
        error=json.loads(row["error"]) if row["error"] else None,
    )


def update_playground(tenant, run_id, *, step=None, step_status=None, status=None,
                      result=None, error=None):
    """Advance a playground run. Terminal state is final, so a durable replay is a no-op."""
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT status, steps FROM playground_runs WHERE tenant_id=? AND id=?",
            (tenant, run_id),
        ).fetchone()
        if row is None:
            raise KeyError("Playground run not found in workflow tenant")
        if row["status"] in ("completed", "failed", "needs_input"):
            return
        steps = json.loads(row["steps"])
        if step:
            item = next(x for x in steps if x["step"] == step)
            item["status"] = step_status
            if step_status == "running":
                item["started"] = now()
            elif item.get("started"):
                item["elapsed_ms"] = max(
                    0,
                    round((datetime.fromisoformat(now()) - datetime.fromisoformat(item["started"])).total_seconds() * 1000),
                )
        values = {"steps": canonical(steps)}
        if status:
            values["status"] = status
            if status in ("completed", "failed", "needs_input"):
                values["completed_at"] = now()
        if result is not None:
            values["result"] = canonical(result)
        if error is not None:
            values["error"] = canonical(error)
        assignments = ",".join(f"{name}=?" for name in values)
        conn.execute(
            f"UPDATE playground_runs SET {assignments} WHERE tenant_id=? AND id=?",
            (*values.values(), tenant, run_id),
        )
