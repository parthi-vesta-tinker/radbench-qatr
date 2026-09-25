"""Tenant-scoped immutable JEV runs, dispatch claims, and reviewer feedback."""

import json
import re

from . import store
from .classification import ClassificationProblem
from .contracts import ClassificationLabels, section_index
from . import presentation
from .presentation import API_VERSION

CREATE = "POST /api/v1/classifications"
STEPS = ("input_validation", "jev_classification", "output_validation", "result_assembly")


def _decode(row):
    if row is None:
        return None
    return {name: json.loads(row[name]) if name in {"input", "config", "steps", "result", "error"} and row[name] is not None
            else row[name] for name in row.keys()}


def _source(conn, tenant, payload):
    row = conn.execute("SELECT document FROM reviews WHERE tenant_id=? AND id=?",
                       (tenant, payload.review_id)).fetchone()
    if not row:
        raise ClassificationProblem("REVIEW_NOT_FOUND", "Review not found.")
    review = json.loads(row["document"])
    if review["input_version"] != payload.input_version:
        raise ClassificationProblem("REVIEW_CONFLICT", "Review version changed. Reload the review.")
    result = review.get("result") or {}
    if review["execution_status"] != "completed" or not result.get("critical_comments"):
        raise ClassificationProblem("NO_CRITICAL_FINDING", "A completed review with a critical finding is required.")
    observation = next((item for item in result["critical_comments"]
                        if item["observation_id"] == payload.observation_id), None)
    if not observation:
        raise ClassificationProblem("CRITICAL_FINDING_NOT_FOUND", "Critical finding not found in this review.")
    mapping = next((item for item in result.get("_candidate_mapping", [])
                    if item["observation_id"] == payload.observation_id), None)
    report = review["input"]["report_text"]
    excerpts = []
    for candidate in (mapping or {}).get("candidates", []):
        for anchor in candidate.get("grounded_anchors", []):
            excerpt = dict(section=anchor["section"], text=anchor["quote"])
            if not excerpt["text"].strip() or excerpt["text"] not in report:
                raise ClassificationProblem("CLASSIFICATION_INVALID_INPUT", "Critical finding evidence is unavailable.")
            if excerpt not in excerpts:
                excerpts.append(excerpt)
    # Only the fixed synthetic demo samples can supply canned target anchors.
    # Never promote an ungrounded QA comment into report evidence.
    if not excerpts and review.get("provenance", {}).get("mode") == "demo":
        from .reviewer import SAMPLES, normalized
        if any(normalized(item["report_text"]) == normalized(report) and
               item["id"] in {"mixed", "critical", "critical_documented", "critical_unflagged"}
               for item in SAMPLES):
            for section in section_index(report):
                for match in re.finditer(r"acute\s+right\s+pneumothorax\.",
                                         report[section["start"]:section["end"]], re.IGNORECASE):
                    excerpts.append(dict(section=section["kind"], text=match.group()))
    if not excerpts:
        raise ClassificationProblem("CLASSIFICATION_INVALID_INPUT", "Critical finding evidence is unavailable.")
    quotes = list(dict.fromkeys(item["text"] for item in excerpts))
    finding = "\n".join(quotes)
    if not 1 <= len(finding) <= 4000 or len(observation["comment"]) > 4000:
        raise ClassificationProblem("CLASSIFICATION_INPUT_TOO_LARGE", "Critical finding text exceeds the JEV limit.")
    return dict(finding_text=finding, qa_comment=observation["comment"], report_quotes=quotes,
                target=dict(report_excerpts=excerpts), report_context=report)



def reserve(tenant, key, payload, config, actor=None, automatic=False):
    request = payload.model_dump()
    operation = CREATE if not automatic else "AUTO /api/v1/classifications"
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if not automatic:
            saved = store.replay_in(conn, tenant, operation, key, request, API_VERSION)
            if saved:
                return saved, False
        if automatic:
            existing = conn.execute("""SELECT id FROM finding_classifications
                WHERE tenant_id=? AND review_id=? AND input_version=? AND observation_id=? AND automatic=1""",
                (tenant, payload.review_id, payload.input_version, payload.observation_id)).fetchone()
            if existing:
                return store.receipt(200, resource(conn, tenant, existing["id"])), False
        input_data = _source(conn, tenant, payload)
        from .classification import request_body, validate_context_size
        validate_context_size(request_body(input_data, config))
        rid = store.new_id("jc")
        created = store.now()
        input_hash = store.digest(store.canonical(input_data))
        workflow_id = f"qa:classification:v1:{tenant}:{rid}"
        steps = [dict(step_id=step, status="pending", started_at=None, completed_at=None) for step in STEPS]
        conn.execute("""INSERT INTO finding_classifications
            (tenant_id,id,review_id,input_version,observation_id,input_hash,input,config,workflow_id,
             automatic,execution_status,steps,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,'queued',?,?,?)""",
            (tenant, rid, payload.review_id, payload.input_version, payload.observation_id,
             input_hash, store.canonical(input_data), store.canonical(config), workflow_id,
             int(automatic), store.canonical(steps), created, created))
        saved = store.receipt(202, resource(conn, tenant, rid),
                              {"Location": "/api/v1/classifications/" + rid, "Retry-After": "1"})
        if not automatic:
            store.remember(conn, tenant, operation, key, request, API_VERSION, saved)
        return saved, True


def resource(conn, tenant, rid):
    row = conn.execute("SELECT * FROM finding_classifications WHERE tenant_id=? AND id=?", (tenant, rid)).fetchone()
    item = _decode(row)
    if item is None:
        return None
    current = conn.execute("SELECT input_version FROM review_records WHERE tenant_id=? AND id=?",
                           (tenant, item["review_id"])).fetchone()
    source_status = "unavailable" if not current else "current" if current[0] == item["input_version"] else "superseded"
    return presentation.classification(item, source_status)


def get(tenant, rid):
    with store.db() as conn:
        return resource(conn, tenant, rid)


def for_review(tenant, review_id, input_version):
    with store.db() as conn:
        rows = conn.execute("""SELECT id FROM finding_classifications WHERE tenant_id=? AND review_id=? AND input_version=?
            ORDER BY created_at,id""", (tenant, review_id, input_version)).fetchall()
        return [resource(conn, tenant, row["id"]) for row in rows]


def pending():
    with store.db() as conn:
        return [(row["tenant_id"], row["id"], row["workflow_id"])
                for row in conn.execute("SELECT tenant_id,id,workflow_id FROM finding_classifications WHERE execution_status IN ('queued','running')")]


def overviews(conn, tenant, *, review_ids=None, period_start=None, period_end=None, source="all"):
    """Latest attempt per current critical observation, only if completed.

    Use the caller's read transaction so history and analytics stay snapshot-consistent.
    Newer pending/failed attempts suppress older results rather than recycling them.
    """
    terms = ["r.tenant_id=?", "json_extract(r.document,'$.execution_status')='completed'",
             "c.input_version=json_extract(r.document,'$.input_version')",
             "c.execution_status='completed'", "c.result IS NOT NULL", "o.group_name='critical_comments'"]
    values = [tenant]
    if review_ids is not None:
        if not review_ids:
            return {}
        terms.append("r.id IN (" + ",".join("?" for _ in review_ids) + ")")
        values.extend(review_ids)
    if source != "all":
        terms.append("json_extract(r.document,'$.provenance.mode')=?")
        values.append(source)
    for bound, operator in ((period_start, ">="), (period_end, "<")):
        if bound:
            terms.append(f"julianday(json_extract(r.document,'$.created_at')){operator}julianday(?)")
            values.append(bound)
    rows = conn.execute(
        "SELECT c.review_id,c.result FROM finding_classifications c "
        "JOIN reviews r ON r.tenant_id=c.tenant_id AND r.id=c.review_id "
        "JOIN observations o ON o.tenant_id=c.tenant_id AND o.review_id=c.review_id AND o.id=c.observation_id "
        "WHERE " + " AND ".join(terms) +
        " AND NOT EXISTS (SELECT 1 FROM finding_classifications newer WHERE newer.tenant_id=c.tenant_id "
        "AND newer.review_id=c.review_id AND newer.input_version=c.input_version "
        "AND newer.observation_id=c.observation_id AND (newer.created_at,newer.id)>(c.created_at,c.id)) "
        "ORDER BY c.review_id,o.position,c.created_at,c.id", values).fetchall()
    grouped = {}
    for row in rows:
        grouped.setdefault(row["review_id"], []).append(presentation.classification_overview(json.loads(row["result"])))
    return grouped


def pending_automatic():
    """Only current critical findings from reviews admitted with JEV enabled."""
    with store.db() as conn:
        return [(row["tenant_id"], row["review_id"], row["input_version"], row["id"])
                for row in conn.execute("""SELECT o.tenant_id,o.review_id,r.input_version,o.id
                    FROM observations o JOIN review_records r ON r.tenant_id=o.tenant_id AND r.id=o.review_id
                    WHERE r.execution_status='completed' AND o.group_name='critical_comments'
                      AND o.result_version=r.input_version
                      AND json_extract(r.provenance,'$.jev_enabled_at_acceptance')=1
                      AND NOT EXISTS (SELECT 1 FROM finding_classifications c WHERE c.tenant_id=o.tenant_id
                        AND c.review_id=o.review_id AND c.input_version=r.input_version AND c.observation_id=o.id)
                    ORDER BY r.created_at,o.position LIMIT 100""")]


def job(tenant, rid):
    with store.db() as conn:
        row = conn.execute("SELECT input,config FROM finding_classifications WHERE tenant_id=? AND id=?", (tenant, rid)).fetchone()
        return (json.loads(row["input"]), json.loads(row["config"])) if row else None


def update(tenant, rid, *, step=None, step_status=None, status=None, result=None, error=None):
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT execution_status,steps,result FROM finding_classifications WHERE tenant_id=? AND id=?",
                           (tenant, rid)).fetchone()
        if not row:
            raise KeyError("Classification not found")
        if row["execution_status"] in ("completed", "failed"):
            if status and status != row["execution_status"]:
                raise ValueError("Terminal classification cannot change state")
            if result is not None and store.canonical(result) != row["result"]:
                raise ValueError("Terminal classification result cannot change")
            return
        if status == "completed" and result is None:
            raise ValueError("Completion needs validated result")
        steps = json.loads(row["steps"])
        if step:
            entry = next(item for item in steps if item["step_id"] == step)
            entry["status"] = step_status
            if step_status == "running":
                entry["started_at"] = store.now()
            if step_status in ("completed", "failed"):
                entry["completed_at"] = store.now()
        if status == "failed":
            for entry in steps:
                if entry["status"] == "pending":
                    entry["status"] = "skipped"
        conn.execute("""UPDATE finding_classifications SET execution_status=?,steps=?,result=?,error=?,updated_at=?
            WHERE tenant_id=? AND id=?""",
            (status or row["execution_status"], store.canonical(steps),
             store.canonical(result) if result is not None else row["result"],
             store.canonical(error) if error is not None else None,
             store.now(), tenant, rid))


def attempt(tenant, rid):
    with store.db() as conn:
        row = conn.execute("SELECT * FROM jev_classification_attempts WHERE tenant_id=? AND classification_id=?",
                           (tenant, rid)).fetchone()
        return dict(row) if row else None


def claim(tenant, rid):
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT outcome FROM jev_classification_attempts WHERE tenant_id=? AND classification_id=?",
                           (tenant, rid)).fetchone()
        if row:
            return False
        conn.execute("INSERT INTO jev_classification_attempts(tenant_id,classification_id,claim_id,outcome) VALUES(?,?,?,'claimed')",
                     (tenant, rid, store.new_id("ja")))
        return True


def checkpoint(tenant, rid, status, body, duration_ms):
    outcome = "response" if 200 <= status < 300 and body is not None else "known_failure"
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("""UPDATE jev_classification_attempts SET outcome=?,http_status=?,response_body=?,duration_ms=?
            WHERE tenant_id=? AND classification_id=? AND outcome='claimed'""",
            (outcome, status, body, duration_ms, tenant, rid)).rowcount != 1:
            raise ValueError("JEV checkpoint conflict")


def mark_unknown(tenant, rid):
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""UPDATE jev_classification_attempts SET outcome='unknown'
            WHERE tenant_id=? AND classification_id=? AND outcome='claimed'""", (tenant, rid))


def feedback(tenant, rid, key, payload, actor):
    request = payload.model_dump(mode="json")
    operation = f"POST /api/v1/classifications/{rid}/feedback"
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        saved = store.replay_in(conn, tenant, operation, key, request, API_VERSION)
        if saved:
            return saved, False
        row = conn.execute("SELECT result,execution_status FROM finding_classifications WHERE tenant_id=? AND id=?",
                           (tenant, rid)).fetchone()
        if not row:
            raise ClassificationProblem("CLASSIFICATION_NOT_FOUND", "Classification not found.")
        if row["execution_status"] != "completed" or not row["result"]:
            raise ClassificationProblem("CLASSIFICATION_NOT_READY", "A completed classification is required.")
        fields = json.loads(row["result"])["fields"]
        predicted = {field: fields[field]["label"] for field in fields}
        ClassificationLabels.model_validate(predicted)
        final = predicted if payload.action == "accept" else request["final_labels"] if payload.action == "edit" else None
        doc = dict(id=store.new_id("jfb"), classification_id=rid, action=payload.action,
                   predicted_labels=predicted, final_labels=final, reason=payload.reason,
                   actor_name=actor, created_at=store.now())
        conn.execute("INSERT INTO classification_feedback(tenant_id,id,classification_id,document,created_at) VALUES(?,?,?,?,?)",
                     (tenant, doc["id"], rid, store.canonical(doc), doc["created_at"]))
        saved = store.receipt(201, doc, {"Location": f"/api/v1/classifications/{rid}/feedback"})
        store.remember(conn, tenant, operation, key, request, API_VERSION, saved)
        return saved, True


def feedback_history(tenant, rid):
    with store.db() as conn:
        exists = conn.execute("SELECT 1 FROM finding_classifications WHERE tenant_id=? AND id=?", (tenant, rid)).fetchone()
        if not exists:
            return None
        rows = conn.execute("SELECT document FROM classification_feedback WHERE tenant_id=? AND classification_id=? ORDER BY created_at,id",
                            (tenant, rid)).fetchall()
        return [json.loads(row["document"]) for row in rows]
