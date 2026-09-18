"""Append-only operator-recorded decisions; not authenticated stakeholder signatures."""

import json
from . import store
from .contracts import OutcomeResource


def save(tenant, rid, key, payload, version):
    data = payload.model_dump()
    operation = f"POST /api/v1/reviews/{rid}/outcomes"
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        saved = store.replay_in(conn, tenant, operation, key, data, version)
        if saved:
            return saved, False
        row = conn.execute("SELECT document FROM reviews WHERE tenant_id=? AND id=?", (tenant, rid)).fetchone()
        if row is None:
            raise KeyError("Review not found")
        review = json.loads(row[0])
        if review["execution_status"] != "completed" or (review.get("result") or {}).get("result_version") != data["result_version"]:
            raise ValueError("A completed matching result version is required.")
        doc = OutcomeResource(outcome_id=store.new_id("qo"), review_id=rid,
                              created_at=store.now(), **data).model_dump()
        conn.execute("INSERT INTO outcomes(tenant_id,id,review_id,document) VALUES(?,?,?,?)",
                     (tenant, doc["outcome_id"], rid, store.canonical(doc)))
        saved = store.receipt(201, doc)
        store.remember(conn, tenant, operation, key, data, version, saved)
        return saved, True


def history(tenant, rid, limit, after):
    with store.db() as conn:
        conn.execute("BEGIN")
        terms, values = ["tenant_id=?", "review_id=?"], [tenant, rid]
        if after:
            row = conn.execute("SELECT rowid FROM outcomes WHERE tenant_id=? AND review_id=? AND id=?",
                               (tenant, rid, after)).fetchone()
            if row is None:
                raise store.InvalidCursor()
            terms.append("rowid<?")
            values.append(row[0])
        rows = conn.execute("SELECT document FROM outcomes WHERE " + " AND ".join(terms)
                            + " ORDER BY rowid DESC LIMIT ?", [*values, limit + 1]).fetchall()
    return [OutcomeResource.model_validate_json(row[0]).model_dump() for row in rows[:limit]], len(rows) > limit


def acceptance_counts(conn, review_terms, review_values, eligible):
    # One latest event per report, result version, stakeholder and subject. Newer unknown
    # events retract an earlier decision without deleting its history.
    rows = conn.execute("""WITH ranked AS (
        SELECT json_extract(o.document,'$.stakeholder') AS stakeholder,
               json_extract(o.document,'$.subject') AS subject,
               json_extract(o.document,'$.decision') AS decision,
               row_number() OVER (
                 PARTITION BY o.review_id, json_extract(o.document,'$.stakeholder'), json_extract(o.document,'$.subject')
                 ORDER BY o.rowid DESC) AS rank
        FROM outcomes o JOIN reviews r ON r.tenant_id=o.tenant_id AND r.id=o.review_id
        WHERE """ + " AND ".join(review_terms) + """
        AND json_extract(r.document,'$.execution_status')='completed'
        AND json_extract(o.document,'$.result_version')=json_extract(r.document,'$.result.result_version')
        ) SELECT stakeholder,subject,decision,count(*) AS count FROM ranked
        WHERE rank=1 GROUP BY stakeholder,subject,decision""", review_values).fetchall()
    result = []
    for stakeholder in ("qa", "radiologist", "facility"):
        for subject in ("report", "qa_comments"):
            values = dict.fromkeys(("accepted", "rejected", "review_requested", "unknown"), 0)
            for row in rows:
                if row["stakeholder"] == stakeholder and row["subject"] == subject:
                    values[row["decision"]] = row["count"]
            recorded = sum(values.values())
            final = values["accepted"] + values["rejected"]
            result.append(dict(stakeholder=stakeholder, subject=subject, eligible=eligible,
                               recorded=recorded, not_recorded=eligible-recorded,
                               acceptance_rate=values["accepted"] / final if final else None, **values))
    return result
